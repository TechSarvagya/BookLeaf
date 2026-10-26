from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import LoginView,MeView,ProfileView,LogoutView
urlpatterns=[path('auth/login/',LoginView.as_view()),path('auth/refresh/',TokenRefreshView.as_view()),path('auth/logout/',LogoutView.as_view()),path('auth/me/',MeView.as_view()),path('authors/me/',ProfileView.as_view())]
