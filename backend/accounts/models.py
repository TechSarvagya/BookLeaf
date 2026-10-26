from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
class UserManager(BaseUserManager):
    def create_user(self,email,password=None,**extra):
        if not email: raise ValueError('Email is required')
        u=self.model(email=self.normalize_email(email),**extra); u.set_password(password); u.save(); return u
    def create_superuser(self,email,password=None,**extra):
        extra.update(role='ADMIN',is_staff=True,is_superuser=True); return self.create_user(email,password,**extra)
class User(AbstractBaseUser,PermissionsMixin):
    class Role(models.TextChoices): AUTHOR='AUTHOR','Author'; ADMIN='ADMIN','Admin'
    email=models.EmailField(unique=True); full_name=models.CharField(max_length=160); role=models.CharField(max_length=10,choices=Role.choices,default=Role.AUTHOR); is_active=models.BooleanField(default=True); is_staff=models.BooleanField(default=False); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    objects=UserManager(); USERNAME_FIELD='email'; REQUIRED_FIELDS=['full_name']
    def __str__(self): return self.email
class AuthorProfile(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE,related_name='author_profile'); author_id=models.CharField(max_length=64,unique=True); phone=models.CharField(max_length=40,blank=True); city=models.CharField(max_length=100,blank=True); joined_date=models.DateField(null=True,blank=True)
