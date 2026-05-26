# pyrefly: ignore [missing-import]
from rest_framework import serializers
from .models import Consultation, ConsultationDetail, Testimonial

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
        # pyrefly: ignore [missing-import]
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

class TestimonialSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = Testimonial
        fields = ['id', 'user_name', 'rating', 'content', 'created_at']
