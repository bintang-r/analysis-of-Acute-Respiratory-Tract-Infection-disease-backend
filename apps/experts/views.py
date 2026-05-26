from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import HealthExpert
from .serializers import HealthExpertSerializer

class HealthExpertViewSet(viewsets.ModelViewSet):
    queryset = HealthExpert.objects.all()
    serializer_class = HealthExpertSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
