from rest_framework import serializers
from .models import User, AuthorProfile
class UserSerializer(serializers.ModelSerializer):
    class Meta: model=User; fields=['id','email','full_name','role']
class ProfileSerializer(serializers.ModelSerializer):
    user=UserSerializer(read_only=True)
    class Meta: model=AuthorProfile; fields=['author_id','phone','city','joined_date','user']
class LogoutSerializer(serializers.Serializer):
    refresh=serializers.CharField(write_only=True)
