# pyrefly: ignore [missing-import]
from rest_framework import viewsets
# pyrefly: ignore [missing-import]
from rest_framework.permissions import IsAuthenticated
from .models import Consultation
from .serializers import ConsultationSerializer

class ConsultationViewSet(viewsets.ModelViewSet):
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Consultation.objects.filter(user=self.request.user).order_by('-consultation_date')

# pyrefly: ignore [missing-import]
from rest_framework.views import APIView
# pyrefly: ignore [missing-import]
from rest_framework.response import Response
# pyrefly: ignore [missing-import]
from rest_framework import generics, permissions
from .models import Testimonial
from .serializers import TestimonialSerializer
# pyrefly: ignore [missing-import]
from django.db.models import Count, Avg
# pyrefly: ignore [missing-import]
from apps.authentication.models import User

class StatisticsView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # Count all regular users (role='user') registered in the app
        total_patients = User.objects.filter(role='user').count()
        total_consultations = Consultation.objects.count()
        avg_confidence = Consultation.objects.aggregate(Avg('confidence_result'))['confidence_result__avg'] or 0

        # Get top diseases
        diseases = Consultation.objects.values('final_diagnosis').annotate(cases=Count('id')).order_by('-cases')[:5]
        disease_data = [{'name': d['final_diagnosis'], 'cases': d['cases']} for d in diseases if d['final_diagnosis']]

        # Get last 5 users who have uploaded a profile picture
        recent_users = User.objects.filter(
            role='user',
            profile_picture__isnull=False
        ).exclude(profile_picture='').order_by('-date_joined')[:5]
        
        avatars = []
        for u in recent_users:
            if u.profile_picture:
                url = request.build_absolute_uri(u.profile_picture.url)
                avatars.append({'name': u.full_name or u.username, 'avatar': url})

        return Response({
            'total_patients': total_patients,
            'total_consultations': total_consultations,
            'avg_confidence': round(avg_confidence, 2),
            'disease_distribution': disease_data,
            'recent_avatars': avatars,
        })

class TestimonialListCreateView(generics.ListCreateAPIView):
    queryset = Testimonial.objects.all().order_by('-created_at')
    serializer_class = TestimonialSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user
        if Testimonial.objects.filter(user=user).exists():
            # pyrefly: ignore [unknown-name]
            raise serializers.ValidationError("You have already submitted a testimonial.")
        if not Consultation.objects.filter(user=user).exists():
            # pyrefly: ignore [unknown-name]
            raise serializers.ValidationError("You must complete at least one consultation to submit a testimonial.")
        serializer.save(user=user)
