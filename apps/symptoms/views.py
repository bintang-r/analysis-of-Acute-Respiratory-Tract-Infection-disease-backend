from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Symptom
from .serializers import SymptomSerializer

class SymptomViewSet(viewsets.ModelViewSet):
    queryset = Symptom.objects.all()
    serializer_class = SymptomSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
