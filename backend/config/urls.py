from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from core.views import health
urlpatterns=[path('admin/',admin.site.urls),path('api/v1/',include('accounts.urls')),path('api/v1/',include('books.urls')),path('api/v1/',include('tickets.urls')),path('api/v1/health/',health),path('api/schema/',SpectacularAPIView.as_view()),path('api/docs/',SpectacularSwaggerView.as_view(url_name='schema'))]
