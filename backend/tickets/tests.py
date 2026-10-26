from pathlib import Path
from unittest.mock import Mock, patch
from django.core.management import call_command
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from accounts.models import User, AuthorProfile
from books.models import Book
from .models import Ticket, TicketMessage, InternalNote

class PortalTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user('author@example.test','secret123',full_name='Author')
        self.other = User.objects.create_user('other@example.test','secret123',full_name='Other')
        self.admin = User.objects.create_user('staff@example.test','secret123',full_name='Staff',role='ADMIN',is_staff=True)
        self.profile = AuthorProfile.objects.create(user=self.author,author_id='AUTH1')
        self.other_profile = AuthorProfile.objects.create(user=self.other,author_id='AUTH2')
        self.book = Book.objects.create(book_id='BK1',author=self.profile,title='Published Book',status='Published & Live',total_copies_sold=0,royalty_pending=0)
        self.other_book = Book.objects.create(book_id='BK2',author=self.other_profile,title='Private Book',status='Cover Design',publication_date=None,mrp=None,available_on=[])
        self.client = APIClient()

    def as_user(self, user): self.client.force_authenticate(user=user)
    def create_ticket(self, book=None):
        self.as_user(self.author)
        response = self.client.post('/api/v1/tickets/',{'book':book,'subject':'Royalty question','description':'Please review my royalty statement for this title.'},format='json')
        self.assertEqual(response.status_code,201,response.data)
        return response.data['id']

    def test_authentication_login_logout_and_refresh(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get('/api/v1/authors/me/books/').status_code,401)
        bad = self.client.post('/api/v1/auth/login/',{'email':self.author.email,'password':'incorrect'})
        self.assertEqual(bad.status_code,401)
        login = self.client.post('/api/v1/auth/login/',{'email':self.author.email,'password':'secret123'})
        self.assertEqual(login.status_code,200)
        refresh = self.client.post('/api/v1/auth/refresh/',{'refresh':login.data['refresh']})
        self.assertEqual(refresh.status_code,200)
        self.as_user(self.author)
        self.assertEqual(self.client.post('/api/v1/auth/logout/',{'refresh':refresh.data['refresh']}).status_code,204)

    def test_books_and_profile_are_private_with_nulls_and_zero_values(self):
        self.as_user(self.author)
        books = self.client.get('/api/v1/authors/me/books/')
        self.assertEqual([item['book_id'] for item in books.data],['BK1'])
        self.assertEqual(self.client.get(f'/api/v1/authors/me/books/{self.other_book.pk}/').status_code,404)
        self.assertEqual(self.client.get('/api/v1/authors/me/dashboard/').data['pending'],0)
        self.as_user(self.other)
        data = self.client.get(f'/api/v1/authors/me/books/{self.other_book.pk}/').data
        self.assertIsNone(data['publication_date'])
        self.assertIsNone(data['mrp'])
        self.assertEqual(data['available_on'],[])

    def test_ticket_creation_is_immediate_and_rejects_foreign_book(self):
        self.as_user(self.author)
        invalid = self.client.post('/api/v1/tickets/',{'book':self.other_book.pk,'subject':'Help','description':'This is somebody else’s book.'},format='json')
        self.assertEqual(invalid.status_code,400)
        self.assertEqual(Ticket.objects.count(),0)
        ticket_id = self.create_ticket()
        ticket = Ticket.objects.get(pk=ticket_id)
        self.assertIsNone(ticket.book)
        self.assertEqual(ticket.ai_status,'PENDING')
        self.assertTrue(ticket.ticket_number.startswith('BL-'))

    def test_author_isolation_and_private_notes_and_draft(self):
        ticket_id=self.create_ticket(self.book.pk)
        ticket=Ticket.objects.get(pk=ticket_id)
        ticket.ai_draft='Only staff should read this.'; ticket.save()
        InternalNote.objects.create(ticket=ticket,admin=self.admin,note='Private note')
        self.as_user(self.author)
        own=self.client.get(f'/api/v1/tickets/{ticket_id}/').data
        self.assertNotIn('notes',own); self.assertNotIn('ai_draft',own)
        self.assertNotIn('Private note',str(own))
        self.assertEqual(self.client.get(f'/api/v1/admin/tickets/{ticket_id}/notes/').status_code,403)
        self.assertEqual(self.client.patch(f'/api/v1/admin/tickets/{ticket_id}/',{'priority':'CRITICAL'}).status_code,403)
        self.assertEqual(self.client.post(f'/api/v1/admin/tickets/{ticket_id}/reply/',{'message':'Forged staff reply'}).status_code,403)
        self.as_user(self.other)
        self.assertEqual(self.client.get(f'/api/v1/tickets/{ticket_id}/').status_code,404)
        self.assertEqual(self.client.get(f'/api/v1/tickets/{ticket_id}/messages/').status_code,404)

    def test_admin_status_assignment_notes_filters_and_invalid_inputs(self):
        ticket_id=self.create_ticket(self.book.pk)
        self.as_user(self.admin)
        path=f'/api/v1/admin/tickets/{ticket_id}/'
        self.assertEqual(self.client.post(f'/api/v1/admin/tickets/{ticket_id}/assign/').data['assigned_admin'],self.admin.pk)
        self.assertEqual(self.client.post(f'/api/v1/admin/tickets/{ticket_id}/notes/',{'note':'Internal follow-up'}).status_code,201)
        self.assertEqual(len(self.client.get(f'/api/v1/admin/tickets/{ticket_id}/notes/').data),1)
        self.assertEqual(self.client.patch(path,{'status':'CLOSED'},format='json').status_code,400)
        self.assertEqual(self.client.patch(path,{'status':'IN_PROGRESS','category':'ROYALTY','priority':'HIGH'},format='json').status_code,200)
        self.assertEqual(self.client.patch(path,{'status':'RESOLVED'},format='json').status_code,200)
        self.assertEqual(self.client.patch(path,{'status':'CLOSED'},format='json').status_code,200)
        self.assertEqual(self.client.patch(path,{'category':'NOT_REAL'},format='json').status_code,400)
        queue=self.client.get('/api/v1/admin/tickets/?status=CLOSED&priority=HIGH&search=Royalty')
        self.assertEqual(queue.data['count'],1)
        self.assertEqual(self.client.get('/api/v1/admin/tickets/?status=BAD').status_code,400)

    def test_author_reopens_ticket_with_message_and_duplicate_reply_is_safe(self):
        ticket_id=self.create_ticket()
        ticket=Ticket.objects.get(pk=ticket_id); ticket.status='RESOLVED'; ticket.save()
        self.as_user(self.author)
        self.assertEqual(self.client.post(f'/api/v1/tickets/{ticket_id}/messages/',{'message':'I still need help.'}).status_code,201)
        ticket.refresh_from_db(); self.assertEqual(ticket.status,'OPEN')
        self.as_user(self.admin)
        url=f'/api/v1/admin/tickets/{ticket_id}/reply/'
        headers={'HTTP_IDEMPOTENCY_KEY':'reply-001'}
        first=self.client.post(url,{'message':'We will review it.'},**headers)
        second=self.client.post(url,{'message':'We will review it.'},**headers)
        self.assertEqual((first.status_code,second.status_code),(201,200))
        self.assertEqual(TicketMessage.objects.filter(ticket=ticket,sender=self.admin).count(),1)

    @override_settings(GEMINI_API_KEY='fake')
    @patch('ai_services.service._client')
    def test_ai_classification_schema_and_manual_override(self,client):
        ticket_id=self.create_ticket()
        response=Mock(output_text='{"category":"Royalty & Payments","priority":"High","confidence":0.91,"reason":"Delayed payout"}',usage_metadata=None,usage=None)
        client.return_value.interactions.create.return_value=response
        self.as_user(self.author)
        result=self.client.post(f'/api/v1/tickets/{ticket_id}/ai/classify/')
        self.assertEqual(result.data['category'],'ROYALTY')
        self.assertEqual(result.data['priority'],'HIGH')
        self.as_user(self.admin)
        self.client.patch(f'/api/v1/admin/tickets/{ticket_id}/',{'category':'GENERAL'},format='json')
        client.return_value.interactions.create.return_value=Mock(output_text='{"category":"ISBN & Metadata Issues","priority":"Low","confidence":0.8,"reason":"ISBN discrepancy"}',usage_metadata=None,usage=None)
        self.client.post(f'/api/v1/admin/tickets/{ticket_id}/ai/retry-classification/')
        ticket=Ticket.objects.get(pk=ticket_id)
        self.assertEqual(ticket.category,'GENERAL')
        self.assertEqual(ticket.priority,'LOW')

    @override_settings(GEMINI_API_KEY='fake')
    @patch('ai_services.service._client')
    def test_ai_failure_keeps_ticket_and_allows_manual_reply(self,client):
        ticket_id=self.create_ticket()
        client.return_value.interactions.create.side_effect=RuntimeError('provider rejected key')
        self.as_user(self.author)
        result=self.client.post(f'/api/v1/tickets/{ticket_id}/ai/classify/')
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.data['ai_status'],'FAILED')
        self.assertNotIn('provider rejected key',str(result.data))
        self.assertEqual(Ticket.objects.count(),1)
        self.as_user(self.admin)
        self.assertEqual(self.client.post(f'/api/v1/admin/tickets/{ticket_id}/ai/draft/').status_code,200)
        self.assertEqual(self.client.post(f'/api/v1/admin/tickets/{ticket_id}/reply/',{'message':'We will investigate.'}).status_code,201)
        self.as_user(self.author)
        self.assertEqual(len(self.client.get(f'/api/v1/tickets/{ticket_id}/messages/').data),1)

    @override_settings(GEMINI_API_KEY='fake')
    @patch('ai_services.service._client')
    def test_ai_invalid_category_falls_back(self,client):
        ticket_id=self.create_ticket()
        client.return_value.interactions.create.return_value=Mock(output_text='{"category":"Invalid","priority":"High","confidence":0.7,"reason":"Unknown"}',usage_metadata=None,usage=None)
        self.as_user(self.author)
        result=self.client.post(f'/api/v1/tickets/{ticket_id}/ai/classify/')
        self.assertEqual(result.data['category'],'GENERAL')
        self.assertEqual(result.data['priority'],'MEDIUM')
        self.assertEqual(result.data['ai_status'],'FAILED')

    @override_settings(GEMINI_API_KEY='fake')
    @patch('ai_services.service._client')
    def test_complete_author_to_admin_to_author_workflow(self, client):
        self.as_user(self.author)
        self.assertEqual(self.client.get('/api/v1/authors/me/books/').status_code,200)
        ticket_id=self.create_ticket(self.book.pk)
        client.return_value.interactions.create.return_value=Mock(
            output_text='{"category":"Royalty & Payments","priority":"High","confidence":0.85,"reason":"Author reports a royalty delay"}',usage_metadata=None,usage=None)
        classified=self.client.post(f'/api/v1/tickets/{ticket_id}/ai/classify/').data
        self.assertEqual((classified['category'],classified['priority']),('ROYALTY','HIGH'))
        self.as_user(self.admin)
        queue=self.client.get('/api/v1/admin/tickets/?category=ROYALTY').data
        self.assertEqual(queue['count'],1)
        client.return_value.interactions.create.return_value=Mock(
            output_text='We will review your royalty records and confirm the payout status.',usage_metadata=None,usage=None)
        draft=self.client.post(f'/api/v1/admin/tickets/{ticket_id}/ai/draft/').data['ai_draft']
        self.assertIn('review your royalty records',draft)
        edited=draft+' Thank you for your patience.'
        self.assertEqual(self.client.post(f'/api/v1/admin/tickets/{ticket_id}/reply/',
                           {'message':edited},HTTP_IDEMPOTENCY_KEY='workflow-1').status_code,201)
        self.client.patch(f'/api/v1/admin/tickets/{ticket_id}/',{'status':'RESOLVED'})
        self.as_user(self.author)
        self.assertEqual(self.client.get(f'/api/v1/tickets/{ticket_id}/').data['status'],'RESOLVED')
        messages=self.client.get(f'/api/v1/tickets/{ticket_id}/messages/').data
        self.assertEqual(messages[-1]['message'],edited)
        self.assertEqual(messages[-1]['sender_role'],'ADMIN')

class DatasetTests(TestCase):
    @override_settings(DEBUG=True)
    def test_seed_is_idempotent_and_preserves_special_cases(self):
        path=Path(__file__).resolve().parents[2]/'FULLSTACK-SAMPLEDATA (1) (1) (1).json'
        for _ in range(2): call_command('seed_bookleaf_data',file=str(path),verbosity=0)
        self.assertEqual(AuthorProfile.objects.count(),10)
        self.assertEqual(Book.objects.count(),18)
        self.assertTrue(User.objects.get(email='priya.sharma@email.com').check_password('BookleafDemo123!'))
        self.assertTrue(Book.objects.filter(publication_date__isnull=True).exists())
        self.assertTrue(Book.objects.filter(mrp__isnull=True).exists())
        self.assertTrue(Book.objects.filter(total_copies_sold=0).exists())
