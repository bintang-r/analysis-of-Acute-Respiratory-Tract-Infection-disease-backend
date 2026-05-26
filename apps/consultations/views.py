from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Consultation
from .serializers import ConsultationSerializer

class ConsultationViewSet(viewsets.ModelViewSet):
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Consultation.objects.filter(user=self.request.user).order_by('-consultation_date')
