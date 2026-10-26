from django.urls import path
from .views import MyBooksView,MyBookDetailView,DashboardView
urlpatterns=[path('authors/me/books/',MyBooksView.as_view()),path('authors/me/books/<int:pk>/',MyBookDetailView.as_view()),path('authors/me/dashboard/',DashboardView.as_view())]
