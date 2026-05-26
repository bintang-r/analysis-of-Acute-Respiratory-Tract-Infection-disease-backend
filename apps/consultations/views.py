# pyrefly: ignore [missing-import]
from rest_framework import viewsets
# pyrefly: ignore [missing-import]
from rest_framework.permissions import IsAuthenticated
from .models import Consultation
from .serializers import ConsultationSerializer

from rest_framework.decorators import action

class ConsultationViewSet(viewsets.ModelViewSet):
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self.request.user, 'role', '') == 'admin':
            return Consultation.objects.all().order_by('-consultation_date')
        return Consultation.objects.filter(user=self.request.user).order_by('-consultation_date')

    @action(detail=True, methods=['get'])
    def matching_rows(self, request, pk=None):
        from apps.rules.models import DatasetRow
        from apps.symptoms.models import Symptom
        consultation = self.get_object()
        
        # 1. Get patient active symptoms (symptom codes where user_cf > 0)
        details = consultation.details.filter(user_cf__gt=0.0).select_related('symptom')
        active_symptom_codes = [d.symptom.code for d in details]
        active_symptom_names = {d.symptom.code: d.symptom.name for d in details}
        
        # Determine patient age category
        age = consultation.age or 0
        patient_age_code = None
        if age <= 12:
            patient_age_code = 'S17'
        elif age <= 18:
            patient_age_code = 'S18'
        elif age <= 60:
            patient_age_code = 'S19'
        else:
            patient_age_code = 'S20'
            
        # 2. Get dataset rows with the same diagnosis
        matching_db_rows = DatasetRow.objects.filter(diagnosis=consultation.final_diagnosis)
        
        symptom_columns = {
            'batuk_kering': 'S01',
            'batuk_berdahak': 'S02',
            'demam': 'S03',
            'pilek': 'S04',
            'hidung_tersumbat': 'S05',
            'sesak_napas': 'S06',
            'nyeri_tenggorokan': 'S07',
            'sakit_kepala': 'S08',
            'mual_muntah': 'S09',
            'nyeri_dada': 'S10',
            'suara_serak': 'S11',
            'kelelahan': 'S12',
            'berkeringat_malam': 'S13',
            'nafsu_makan_turun': 'S14',
            'hilang_penciuman': 'S15',
            'nyeri_saat_menelan': 'S16'
        }
        
        results = []
        for r in matching_db_rows:
            matched_symptom_names = []
            
            # Check symptoms 1-16
            for attr, code in symptom_columns.items():
                if getattr(r, attr) == 1 and code in active_symptom_codes:
                    matched_symptom_names.append(active_symptom_names[code])
                    
            # Check age category
            r_age = r.age
            r_age_code = None
            if r_age <= 12:
                r_age_code = 'S17'
            elif r_age <= 18:
                r_age_code = 'S18'
            elif r_age <= 60:
                r_age_code = 'S19'
            else:
                r_age_code = 'S20'
                
            if r_age_code == patient_age_code:
                age_labels = {
                    'S17': 'Kategori Umur Balita/Anak',
                    'S18': 'Kategori Umur Remaja',
                    'S19': 'Kategori Umur Dewasa',
                    'S20': 'Kategori Umur Lansia'
                }
                matched_symptom_names.append(age_labels[patient_age_code])
                
            match_count = len(matched_symptom_names)
            
            results.append({
                'row_id': r.id,
                'age': r.age,
                'diagnosis': r.diagnosis,
                'matched_symptoms': matched_symptom_names,
                'match_count': match_count
            })
            
        # Sort results by match_count descending
        results.sort(key=lambda x: x['match_count'], reverse=True)
        top_matches = results[:10]
        
        return Response({
            'total_cases_in_dataset': matching_db_rows.count(),
            'matches': top_matches
        })

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

        # Get top symptoms
        from .models import ConsultationDetail
        symptoms = ConsultationDetail.objects.values('symptom__name').annotate(count=Count('id')).order_by('-count')[:5]
        top_symptoms = [{'name': s['symptom__name'], 'count': s['count']} for s in symptoms]

        # Trends (Accuracy and Consultations per month) - Aggregated in Python to avoid MySQL timezone bugs
        consultations = Consultation.objects.all().order_by('consultation_date')
        monthly_groups = {}
        for c in consultations:
            if c.consultation_date:
                month_key = c.consultation_date.strftime('%Y-%m')
                if month_key not in monthly_groups:
                    monthly_groups[month_key] = {'total': 0, 'sum_accuracy': 0.0, 'month_dt': c.consultation_date}
                monthly_groups[month_key]['total'] += 1
                monthly_groups[month_key]['sum_accuracy'] += c.confidence_result or 0.0

        accuracy_trend = []
        consultation_trend = []
        for month_key, data in sorted(monthly_groups.items()):
            month_name = data['month_dt'].strftime('%b %Y')
            avg_accuracy = round(data['sum_accuracy'] / data['total'], 2) if data['total'] > 0 else 0.0
            accuracy_trend.append({'month': month_name, 'accuracy': avg_accuracy})
            consultation_trend.append({'month': month_name, 'total': data['total']})

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
            'top_symptoms': top_symptoms,
            'accuracy_trend': accuracy_trend,
            'consultation_trend': consultation_trend,
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

class ChatView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.db.models import Q
        user = request.user
        
        if getattr(user, 'role', '') == 'admin':
            partner_id = request.query_params.get('user_id')
            if not partner_id:
                return Response({'error': 'user_id parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            messages = Message.objects.filter(
                Q(sender=user, receiver_id=partner_id) | Q(sender_id=partner_id, receiver=user)
            ).order_by('timestamp')
            
            Message.objects.filter(sender_id=partner_id, receiver=user, is_read=False).update(is_read=True)
        else:
            admin = User.objects.filter(role='admin').first()
            if not admin:
                return Response([])
                
            messages = Message.objects.filter(
                Q(sender=user, receiver=admin) | Q(sender=admin, receiver=user)
            ).order_by('timestamp')
            
            Message.objects.filter(sender=admin, receiver=user, is_read=False).update(is_read=True)
            
        from .serializers import MessageSerializer
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    def post(self, request):
        user = request.user
        content = request.data.get('content')
        if not content:
            return Response({'error': 'content is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        if getattr(user, 'role', '') == 'admin':
            receiver_id = request.data.get('receiver_id')
            if not receiver_id:
                return Response({'error': 'receiver_id is required'}, status=status.HTTP_400_BAD_REQUEST)
                
            msg = Message.objects.create(sender=user, receiver_id=receiver_id, content=content)
        else:
            admin = User.objects.filter(role='admin').first()
            if not admin:
                return Response({'error': 'No admin available'}, status=status.HTTP_400_BAD_REQUEST)
                
            msg = Message.objects.create(sender=user, receiver=admin, content=content)
            
        from .serializers import MessageSerializer
        serializer = MessageSerializer(msg)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class ChatContactsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        if getattr(request.user, 'role', '') != 'admin':
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
            
        from django.db.models import Q
        messages = Message.objects.all()
        user_ids = set()
        for m in messages:
            if m.sender_id != request.user.id:
                user_ids.add(m.sender_id)
            if m.receiver_id and m.receiver_id != request.user.id:
                user_ids.add(m.receiver_id)
                
        patients = User.objects.filter(id__in=user_ids, role='user')
        
        data = []
        for p in patients:
            last_msg = Message.objects.filter(
                Q(sender=p, receiver=request.user) | Q(sender=request.user, receiver=p)
            ).order_by('-timestamp').first()
            
            unread_count = Message.objects.filter(
                sender=p, receiver=request.user, is_read=False
            ).count()
            
            data.append({
                'id': p.id,
                'username': p.username,
                'full_name': p.full_name or p.username,
                'profile_picture': request.build_absolute_uri(p.profile_picture.url) if p.profile_picture else None,
                'last_message': last_msg.content if last_msg else "",
                'last_timestamp': last_msg.timestamp if last_msg else None,
                'unread_count': unread_count
              })
              
        data.sort(key=lambda x: x['last_timestamp'] or p.date_joined, reverse=True)
        return Response(data)
