from rest_framework import serializers
from accounts.models import User
from books.models import Book
from books.serializers import BookSerializer
from .models import Ticket, TicketMessage, InternalNote

class TicketCreateSerializer(serializers.ModelSerializer):
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all(), allow_null=True, required=False)
    class Meta:
        model = Ticket
        fields = ['id', 'ticket_number', 'book', 'subject', 'description']
        read_only_fields = ['id', 'ticket_number']

    def validate_book(self, book):
        if book and book.author.user_id != self.context['request'].user.pk:
            raise serializers.ValidationError('Select one of your own books.')
        return book

    def validate(self, attrs):
        unknown=set(self.initial_data)-{'book','subject','description'}
        if unknown: raise serializers.ValidationError({'detail':'Unsupported ticket field.'})
        return attrs

    def validate_subject(self, value):
        value = value.strip()
        if len(value) < 3: raise serializers.ValidationError('Enter at least 3 characters.')
        return value

    def validate_description(self, value):
        value = value.strip()
        if len(value) < 10: raise serializers.ValidationError('Enter at least 10 characters.')
        return value

class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)
    sender_role = serializers.CharField(source='sender.role', read_only=True)
    class Meta:
        model = TicketMessage
        fields = ['id', 'sender_name', 'sender_role', 'message', 'created_at']
        read_only_fields = ['id', 'sender_name', 'sender_role', 'created_at']
    def validate_message(self, value):
        value = value.strip()
        if not value: raise serializers.ValidationError('Message cannot be blank.')
        return value

class NoteSerializer(serializers.ModelSerializer):
    admin_name = serializers.CharField(source='admin.full_name', read_only=True)
    class Meta:
        model = InternalNote
        fields = ['id', 'admin_name', 'note', 'created_at']
        read_only_fields = ['id', 'admin_name', 'created_at']
    def validate_note(self, value):
        value = value.strip()
        if not value: raise serializers.ValidationError('Note cannot be blank.')
        return value

class AuthorTicketSerializer(serializers.ModelSerializer):
    book_data = BookSerializer(source='book', read_only=True)
    class Meta:
        model = Ticket
        fields = ['id','ticket_number','book','book_data','subject','description',
                  'category','priority','status','ai_status','created_at','updated_at']

class AdminTicketSerializer(AuthorTicketSerializer):
    author_name = serializers.CharField(source='author.user.full_name', read_only=True)
    author_email = serializers.CharField(source='author.user.email', read_only=True)
    assigned_admin_name = serializers.CharField(source='assigned_admin.full_name', read_only=True)
    messages = MessageSerializer(many=True, read_only=True)
    notes = NoteSerializer(many=True, read_only=True)
    class Meta(AuthorTicketSerializer.Meta):
        fields = AuthorTicketSerializer.Meta.fields + [
            'author_name','author_email','assigned_admin','assigned_admin_name',
            'category_source','priority_source','ai_confidence','ai_reason',
            'ai_draft','ai_model','ai_error','ai_processed_at','ai_latency_ms',
            'ai_input_tokens','ai_output_tokens','messages','notes','resolved_at','closed_at']

class AdminTicketUpdateSerializer(serializers.ModelSerializer):
    assigned_admin = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role='ADMIN'),allow_null=True,required=False)
    class Meta:
        model = Ticket
        fields = ['category','priority','status','assigned_admin']
    def validate(self, attrs):
        if set(self.initial_data)-set(self.fields):
            raise serializers.ValidationError({'detail':'Unsupported update field.'})
        return attrs
