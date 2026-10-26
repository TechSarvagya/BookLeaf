import uuid
from django.db import models
from accounts.models import AuthorProfile,User
from books.models import Book
class Ticket(models.Model):
    class Category(models.TextChoices): ROYALTY='ROYALTY','Royalty & Payments'; ISBN='ISBN','ISBN & Metadata Issues'; PRINTING='PRINTING','Printing & Quality'; DISTRIBUTION='DISTRIBUTION','Distribution & Availability'; PRODUCTION='PRODUCTION','Book Status & Production Updates'; GENERAL='GENERAL','General Inquiry'
    class Priority(models.TextChoices): CRITICAL='CRITICAL','Critical'; HIGH='HIGH','High'; MEDIUM='MEDIUM','Medium'; LOW='LOW','Low'
    class Status(models.TextChoices): OPEN='OPEN','Open'; IN_PROGRESS='IN_PROGRESS','In Progress'; RESOLVED='RESOLVED','Resolved'; CLOSED='CLOSED','Closed'
    ticket_number=models.CharField(max_length=20,unique=True,editable=False); author=models.ForeignKey(AuthorProfile,on_delete=models.CASCADE,related_name='tickets'); book=models.ForeignKey(Book,on_delete=models.SET_NULL,null=True,blank=True,related_name='tickets'); subject=models.CharField(max_length=180); description=models.TextField(max_length=5000); category=models.CharField(max_length=20,choices=Category.choices,default=Category.GENERAL); priority=models.CharField(max_length=12,choices=Priority.choices,default=Priority.MEDIUM); status=models.CharField(max_length=20,choices=Status.choices,default=Status.OPEN); assigned_admin=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name='assigned_tickets'); category_source=models.CharField(max_length=12,default='FALLBACK'); priority_source=models.CharField(max_length=12,default='FALLBACK'); ai_status=models.CharField(max_length=20,default='PENDING'); ai_draft=models.TextField(blank=True); ai_model=models.CharField(max_length=100,blank=True); ai_error=models.CharField(max_length=250,blank=True); ai_processed_at=models.DateTimeField(null=True,blank=True); ai_latency_ms=models.PositiveIntegerField(null=True,blank=True); ai_input_tokens=models.PositiveIntegerField(null=True,blank=True); ai_output_tokens=models.PositiveIntegerField(null=True,blank=True); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True); resolved_at=models.DateTimeField(null=True,blank=True); closed_at=models.DateTimeField(null=True,blank=True)
    ai_confidence=models.FloatField(null=True,blank=True); ai_reason=models.CharField(max_length=300,blank=True)
    class Meta: indexes=[models.Index(fields=['status','priority']),models.Index(fields=['category','created_at']),models.Index(fields=['assigned_admin']),models.Index(fields=['created_at'])]
    def save(self,*a,**kw):
        if not self.ticket_number: self.ticket_number='BL-'+uuid.uuid4().hex[:8].upper()
        super().save(*a,**kw)
class TicketMessage(models.Model):
    ticket=models.ForeignKey(Ticket,on_delete=models.CASCADE,related_name='messages'); sender=models.ForeignKey(User,on_delete=models.CASCADE); message=models.TextField(max_length=5000); idempotency_key=models.CharField(max_length=80,null=True,blank=True); created_at=models.DateTimeField(auto_now_add=True)
    class Meta: constraints=[models.UniqueConstraint(fields=['ticket','sender','idempotency_key'],name='unique_message_submission')]; ordering=['created_at','id']
class InternalNote(models.Model): ticket=models.ForeignKey(Ticket,on_delete=models.CASCADE,related_name='notes'); admin=models.ForeignKey(User,on_delete=models.CASCADE); note=models.TextField(max_length=4000); created_at=models.DateTimeField(auto_now_add=True)
