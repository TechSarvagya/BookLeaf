from django.db.models import Sum,Count,Q
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from .models import Book
from .serializers import BookSerializer
def author_required(request): return request.user.role=='AUTHOR'
class MyBooksView(generics.GenericAPIView):
    permission_classes=[IsAuthenticated]
    serializer_class=BookSerializer
    @extend_schema(operation_id='author_book_list',responses=BookSerializer(many=True))
    def get(self,request):
        if not author_required(request): return Response({'detail':'Author account required.'},403)
        return Response(BookSerializer(Book.objects.filter(author=request.user.author_profile),many=True).data)
class MyBookDetailView(generics.GenericAPIView):
    permission_classes=[IsAuthenticated]
    serializer_class=BookSerializer
    @extend_schema(operation_id='author_book_retrieve',responses=BookSerializer)
    def get(self,request,pk):
        if not author_required(request): return Response({'detail':'Author account required.'},403)
        book=Book.objects.filter(pk=pk,author=request.user.author_profile).first()
        return Response(BookSerializer(book).data) if book else Response({'detail':'Not found.'},404)
class DashboardView(generics.GenericAPIView):
    permission_classes=[IsAuthenticated]
    serializer_class=BookSerializer
    def get(self,request):
        if not author_required(request): return Response({'detail':'Author account required.'},403)
        books=Book.objects.filter(author=request.user.author_profile); from tickets.models import Ticket
        a=books.aggregate(total_books=Count('id'),copies=Sum('total_copies_sold'),earned=Sum('total_royalty_earned'),pending=Sum('royalty_pending'))
        return Response({**a,'published_books':books.filter(status__icontains='published').count(),'open_tickets':Ticket.objects.filter(author=request.user.author_profile,status__in=['OPEN','IN_PROGRESS']).count()})
