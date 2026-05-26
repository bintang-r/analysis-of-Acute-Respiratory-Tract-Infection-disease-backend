from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Rule, CertaintyFactor
from .serializers import RuleSerializer, CertaintyFactorSerializer

class RuleViewSet(viewsets.ModelViewSet):
    queryset = Rule.objects.all()
    serializer_class = RuleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class CertaintyFactorViewSet(viewsets.ModelViewSet):
    queryset = CertaintyFactor.objects.all()
    serializer_class = CertaintyFactorSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
