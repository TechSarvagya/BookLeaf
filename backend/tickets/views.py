from django.db import transaction, IntegrityError
from django.db.models import Q, Case, When, Value, IntegerField
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from core.pagination import StandardPagination
from .models import Ticket, TicketMessage
from .serializers import (TicketCreateSerializer, AuthorTicketSerializer,
                          AdminTicketSerializer, AdminTicketUpdateSerializer,
                          MessageSerializer, NoteSerializer)
from ai_services.service import classify_ticket, draft_reply

def require_admin(request):
    if request.user.role != 'ADMIN':
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied('Admin account required.')

def accessible_ticket(request, pk):
    queryset = Ticket.objects.select_related('author__user','book','assigned_admin')
    if request.user.role != 'ADMIN':
        queryset = queryset.filter(author__user=request.user)
    return get_object_or_404(queryset, pk=pk)

class TicketsView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        queryset = Ticket.objects.select_related('book','author__user','assigned_admin').order_by('-updated_at')
        return queryset if self.request.user.role == 'ADMIN' else queryset.filter(author__user=self.request.user)
    def get_serializer_class(self):
        if self.request.method == 'POST': return TicketCreateSerializer
        return AdminTicketSerializer if getattr(self.request.user,'role',None) == 'ADMIN' else AuthorTicketSerializer
    def perform_create(self, serializer):
        if self.request.user.role != 'AUTHOR':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Only authors can create tickets.')
        serializer.save(author=self.request.user.author_profile, category='GENERAL',
                        priority='MEDIUM', ai_status='PENDING')

class TicketDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    def get_object(self): return accessible_ticket(self.request, self.kwargs['pk'])
    def get_serializer_class(self):
        return AdminTicketSerializer if getattr(self.request.user,'role',None) == 'ADMIN' else AuthorTicketSerializer

class MessagesView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer
    def get(self, request, pk):
        ticket = accessible_ticket(request, pk)
        return Response(MessageSerializer(ticket.messages.select_related('sender'), many=True).data)
    def post(self, request, pk):
        ticket = accessible_ticket(request, pk)
        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key = request.headers.get('Idempotency-Key', '').strip()[:80] or None
        try:
            with transaction.atomic():
                if key:
                    existing = TicketMessage.objects.filter(ticket=ticket, sender=request.user,
                                                            idempotency_key=key).first()
                    if existing: return Response(MessageSerializer(existing).data, status=200)
                message = serializer.save(ticket=ticket, sender=request.user, idempotency_key=key)
                if request.user.role == 'AUTHOR' and ticket.status in ('RESOLVED','CLOSED'):
                    ticket.status, ticket.resolved_at, ticket.closed_at = 'OPEN', None, None
                    ticket.save(update_fields=['status','resolved_at','closed_at','updated_at'])
                else:
                    ticket.save(update_fields=['updated_at'])
        except IntegrityError:
            if not key: raise
            existing = get_object_or_404(TicketMessage,ticket=ticket,sender=request.user,idempotency_key=key)
            return Response(MessageSerializer(existing).data,status=200)
        return Response(MessageSerializer(message).data, status=201)

class AdminReplyView(MessagesView):
    http_method_names = ['post','options']
    def post(self, request, pk):
        require_admin(request)
        return super().post(request, pk)

class AdminDashboard(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AdminTicketSerializer
    def get(self, request):
        require_admin(request)
        tickets = Ticket.objects.all()
        return Response({'total_tickets': tickets.count(),
                         'open_tickets': tickets.filter(status='OPEN').count(),
                         'in_progress_tickets': tickets.filter(status='IN_PROGRESS').count(),
                         'resolved_tickets': tickets.filter(status='RESOLVED').count(),
                         'critical_tickets': tickets.filter(priority='CRITICAL').count(),
                         'unassigned_tickets': tickets.filter(assigned_admin__isnull=True).count()})

class AdminTickets(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AdminTicketSerializer
    def get_queryset(self):
        require_admin(self.request)
        q = Ticket.objects.select_related('author__user','book','assigned_admin')
        params = self.request.query_params
        choices = {'status': Ticket.Status.values, 'category': Ticket.Category.values,
                   'priority': Ticket.Priority.values}
        for field, valid in choices.items():
            if params.get(field):
                if params[field] not in valid: raise serializers.ValidationError({field:'Invalid filter.'})
                q = q.filter(**{field: params[field]})
        if params.get('assigned') == 'me': q = q.filter(assigned_admin=self.request.user)
        if params.get('search'):
            term = params['search'].strip()[:100]
            q = q.filter(Q(ticket_number__icontains=term)|Q(subject__icontains=term)|
                         Q(author__user__full_name__icontains=term)|Q(author__user__email__icontains=term))
        for field, lookup in [('from','created_at__date__gte'),('to','created_at__date__lte')]:
            if params.get(field):
                date = serializers.DateField().run_validation(params[field])
                q = q.filter(**{lookup: date})
        sort = params.get('sort','newest')
        if sort == 'oldest': return q.order_by('created_at','id')
        if sort == 'oldest_unresolved': return q.exclude(status__in=['RESOLVED','CLOSED']).order_by('created_at','id')
        if sort == 'priority':
            return q.annotate(priority_rank=Case(
                When(priority='CRITICAL',then=Value(0)),When(priority='HIGH',then=Value(1)),
                When(priority='MEDIUM',then=Value(2)),default=Value(3),output_field=IntegerField()
            )).order_by('priority_rank','created_at')
        if sort != 'newest': raise serializers.ValidationError({'sort':'Invalid sort option.'})
        return q.order_by('-created_at','-id')

class AdminTicket(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AdminTicketSerializer
    def get(self, request, pk):
        require_admin(request)
        return Response(AdminTicketSerializer(accessible_ticket(request,pk)).data)
    @extend_schema(request=AdminTicketUpdateSerializer,responses=AdminTicketSerializer)
    def patch(self, request, pk):
        require_admin(request)
        ticket = accessible_ticket(request,pk)
        serializer = AdminTicketUpdateSerializer(ticket,data=request.data,partial=True)
        serializer.is_valid(raise_exception=True)
        changes = serializer.validated_data
        allowed = {'OPEN':{'OPEN','IN_PROGRESS','RESOLVED'},
                   'IN_PROGRESS':{'OPEN','IN_PROGRESS','RESOLVED'},
                   'RESOLVED':{'OPEN','IN_PROGRESS','RESOLVED','CLOSED'},
                   'CLOSED':{'OPEN','CLOSED'}}
        target = changes.get('status',ticket.status)
        if target not in allowed[ticket.status]:
            raise serializers.ValidationError({'status':'Use a valid status transition.'})
        serializer.save()
        if 'category' in changes: ticket.category_source = 'MANUAL'
        if 'priority' in changes: ticket.priority_source = 'MANUAL'
        if target == 'RESOLVED' and ticket.resolved_at is None: ticket.resolved_at = timezone.now()
        if target == 'CLOSED' and ticket.closed_at is None: ticket.closed_at = timezone.now()
        if target in ('OPEN','IN_PROGRESS'):
            ticket.resolved_at = None; ticket.closed_at = None
        ticket.save()
        return Response(AdminTicketSerializer(ticket).data)

class AssignView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AdminTicketSerializer
    def post(self, request, pk):
        require_admin(request)
        ticket = accessible_ticket(request,pk)
        ticket.assigned_admin = request.user
        ticket.save(update_fields=['assigned_admin','updated_at'])
        return Response(AdminTicketSerializer(ticket).data)

class NotesView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NoteSerializer
    def get(self, request, pk):
        require_admin(request)
        return Response(NoteSerializer(accessible_ticket(request,pk).notes.select_related('admin').order_by('created_at','id'),many=True).data)
    def post(self, request, pk):
        require_admin(request)
        ticket = accessible_ticket(request,pk)
        serializer = NoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(ticket=ticket,admin=request.user)
        return Response(serializer.data,status=201)

class AIAction(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AdminTicketSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'ai'
    @extend_schema(request=None,responses=AdminTicketSerializer)
    def post(self, request, pk, action):
        ticket = accessible_ticket(request,pk)
        if action == 'classify' and request.user.role == 'AUTHOR':
            if ticket.ai_status != 'PENDING':
                return Response(AuthorTicketSerializer(ticket).data)
        else:
            require_admin(request)
            if action not in ('draft','retry-classification'):
                return Response({'detail':'Unknown AI action.'},status=400)
        if action == 'draft': draft_reply(ticket)
        else: classify_ticket(ticket)
        ticket.refresh_from_db()
        return Response(AdminTicketSerializer(ticket).data if request.user.role == 'ADMIN'
                        else AuthorTicketSerializer(ticket).data)
