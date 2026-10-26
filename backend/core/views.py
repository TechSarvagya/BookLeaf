from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
@extend_schema(responses=inline_serializer(name='Health',fields={'status':serializers.CharField()}))
@api_view(['GET'])
@permission_classes([AllowAny])
def health(request): return Response({'status':'ok'})
