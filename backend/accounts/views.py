from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from .serializers import UserSerializer, ProfileSerializer, LogoutSerializer
class LoginSerializer(TokenObtainPairSerializer):
    username_field='email'
    @classmethod
    def get_token(cls,user):
        token=super().get_token(user); token['role']=user.role; return token
class LoginView(TokenObtainPairView): serializer_class=LoginSerializer
class MeView(generics.GenericAPIView):
    permission_classes=[IsAuthenticated]
    serializer_class=UserSerializer
    def get(self,request): return Response(UserSerializer(request.user).data)
class LogoutView(generics.GenericAPIView):
    permission_classes=[IsAuthenticated]
    serializer_class=LogoutSerializer
    def post(self,request):
        refresh=request.data.get('refresh')
        if not refresh: return Response({'detail':'Refresh token is required.'},status=status.HTTP_400_BAD_REQUEST)
        try:
            token=RefreshToken(refresh)
            if token['user_id'] != request.user.pk: return Response({'detail':'Invalid refresh token.'},status=status.HTTP_400_BAD_REQUEST)
            token.blacklist()
        except Exception: return Response({'detail':'Invalid refresh token.'},status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)
class ProfileView(generics.GenericAPIView):
    permission_classes=[IsAuthenticated]
    serializer_class=ProfileSerializer
    def get(self,request):
        if request.user.role!='AUTHOR': return Response({'detail':'Author account required.'},403)
        return Response(ProfileSerializer(request.user.author_profile).data)
