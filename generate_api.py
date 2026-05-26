import os

def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)

# symptoms
write_file("apps/symptoms/serializers.py", '''from rest_framework import serializers
from .models import Symptom

class SymptomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Symptom
        fields = '__all__'
''')

write_file("apps/symptoms/views.py", '''from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Symptom
from .serializers import SymptomSerializer

class SymptomViewSet(viewsets.ModelViewSet):
    queryset = Symptom.objects.all()
    serializer_class = SymptomSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
''')

# diseases
write_file("apps/diseases/serializers.py", '''from rest_framework import serializers
from .models import Disease

class DiseaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disease
        fields = '__all__'
''')

write_file("apps/diseases/views.py", '''from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Disease
from .serializers import DiseaseSerializer

class DiseaseViewSet(viewsets.ModelViewSet):
    queryset = Disease.objects.all()
    serializer_class = DiseaseSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
''')

# rules
write_file("apps/rules/serializers.py", '''from rest_framework import serializers
from .models import Rule, CertaintyFactor

class RuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rule
        fields = '__all__'

class CertaintyFactorSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertaintyFactor
        fields = '__all__'
''')

write_file("apps/rules/views.py", '''from rest_framework import viewsets
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
''')

# experts
write_file("apps/experts/serializers.py", '''from rest_framework import serializers
from .models import HealthExpert

class HealthExpertSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthExpert
        fields = '__all__'
''')

write_file("apps/experts/views.py", '''from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import HealthExpert
from .serializers import HealthExpertSerializer

class HealthExpertViewSet(viewsets.ModelViewSet):
    queryset = HealthExpert.objects.all()
    serializer_class = HealthExpertSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
''')

# authentication
write_file("apps/authentication/serializers.py", '''from rest_framework import serializers
from .models import User
from django.contrib.auth.hashers import make_password

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'full_name', 'role']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data.get('password'))
        return super().create(validated_data)
''')

write_file("apps/authentication/views.py", '''from rest_framework import generics, permissions
from .models import User
from .serializers import UserSerializer
from rest_framework.response import Response

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserSerializer

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
''')

# consultations
write_file("apps/consultations/serializers.py", '''from rest_framework import serializers
from .models import Consultation, ConsultationDetail

class ConsultationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConsultationDetail
        fields = ['symptom', 'user_cf']

class ConsultationSerializer(serializers.ModelSerializer):
    details = ConsultationDetailSerializer(many=True, write_only=True)
    diagnosis_results = serializers.JSONField(read_only=True, required=False)

    class Meta:
        model = Consultation
        fields = ['id', 'consultation_date', 'final_diagnosis', 'confidence_result', 'details', 'diagnosis_results']

    def create(self, validated_data):
        from apps.rules.services import DiagnosisService
        details_data = validated_data.pop('details', [])
        user = self.context['request'].user
        
        selected_symptoms = [{'symptom_id': d['symptom'].id, 'user_cf': d['user_cf']} for d in details_data]
        results = DiagnosisService.calculate_diagnosis(selected_symptoms)
        
        final_diagnosis = results[0]['disease'] if results else "Unknown"
        confidence_result = results[0]['percentage'] if results else 0.0
        
        consultation = Consultation.objects.create(
            user=user,
            final_diagnosis=final_diagnosis,
            confidence_result=confidence_result,
            **validated_data
        )
        
        for detail in details_data:
            ConsultationDetail.objects.create(consultation=consultation, **detail)
            
        # Dynamically append diagnosis_results to the returned representation
        consultation.diagnosis_results = results
        return consultation
''')

write_file("apps/consultations/views.py", '''from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Consultation
from .serializers import ConsultationSerializer

class ConsultationViewSet(viewsets.ModelViewSet):
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Consultation.objects.filter(user=self.request.user).order_by('-consultation_date')
''')

# backend urls.py
write_file("backend/urls.py", '''from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.symptoms.views import SymptomViewSet
from apps.diseases.views import DiseaseViewSet
from apps.rules.views import RuleViewSet, CertaintyFactorViewSet
from apps.experts.views import HealthExpertViewSet
from apps.consultations.views import ConsultationViewSet
from apps.authentication.views import RegisterView, ProfileView

router = DefaultRouter()
router.register(r'symptoms', SymptomViewSet)
router.register(r'diseases', DiseaseViewSet)
router.register(r'rules', RuleViewSet)
router.register(r'certainty-factors', CertaintyFactorViewSet)
router.register(r'experts', HealthExpertViewSet)
router.register(r'consultations', ConsultationViewSet, basename='consultation')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    
    # Auth
    path('api/auth/register/', RegisterView.as_view(), name='auth_register'),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/profile/', ProfileView.as_view(), name='auth_profile'),
]
''')

print("API generated successfully!")
