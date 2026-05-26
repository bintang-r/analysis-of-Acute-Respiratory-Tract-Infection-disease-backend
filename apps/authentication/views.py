from rest_framework import generics, permissions
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

from rest_framework.views import APIView
from apps.consultations.models import Consultation

class AdminUserListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Only admins can view the list of users
        if getattr(request.user, 'role', '') != 'admin':
            return Response({'error': 'Unauthorized'}, status=403)
            
        users = User.objects.filter(role='user').order_by('-date_joined')
        data = []
        
        from apps.rules.services import DiagnosisService
        
        for u in users:
            consultations = Consultation.objects.filter(user=u).order_by('-consultation_date')
            history = []
            for c in consultations:
                details = c.details.all()
                
                # Get the list of symptom codes that were positive (user_cf > 0)
                active_symptoms = list(details.filter(user_cf__gt=0.0).values_list('symptom__code', flat=True))
                
                # Also construct a dictionary of symptom codes to user_cf for precise match calculation if needed
                symptom_cfs = {d.symptom.code: d.user_cf for d in details}
                
                # Re-calculate diagnosis results for the trace
                selected_symptoms = [{'symptom_id': d.symptom_id, 'user_cf': d.user_cf} for d in details]
                diagnosis_results = DiagnosisService.calculate_diagnosis(selected_symptoms)
                
                history.append({
                    'id': c.id,
                    'consultation_date': c.consultation_date,
                    'final_diagnosis': c.final_diagnosis,
                    'confidence_result': c.confidence_result,
                    'age': c.age,
                    'active_symptoms': active_symptoms,
                    'symptom_cfs': symptom_cfs,
                    'diagnosis_results': diagnosis_results
                })
                
            data.append({
                'id': u.id,
                'username': u.username,
                'email': u.email,
                'full_name': u.full_name or u.username,
                'date_joined': u.date_joined,
                'consultations_count': len(history),
                'consultations': history
            })
            
        return Response(data)
