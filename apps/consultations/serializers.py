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
        fields = ['id', 'consultation_date', 'final_diagnosis', 'confidence_result', 'details', 'diagnosis_results', 'age']

    def create(self, validated_data):
        # pyrefly: ignore [missing-import]
        from apps.rules.services import DiagnosisService
        details_data = validated_data.pop('details', [])
        user = self.context['request'].user
        
        age = validated_data.get('age')

        selected_symptoms = [{'symptom_id': d['symptom'].id, 'user_cf': d['user_cf']} for d in details_data]
        results = DiagnosisService.calculate_diagnosis(selected_symptoms)
        
        if results and "message" in results[0]:
            final_diagnosis = "Tidak Terdiagnosis"
            confidence_result = 0.0
        else:
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

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        details = instance.details.all()
        selected_symptoms = [{'symptom_id': d.symptom_id, 'user_cf': d.user_cf} for d in details]
        
        from apps.rules.services import DiagnosisService
        results = DiagnosisService.calculate_diagnosis(selected_symptoms)
        
        rep['diagnosis_results'] = results
        
        if results and "message" not in results[0]:
            from apps.diseases.models import Disease
            top_disease_name = results[0]['disease']
            try:
                disease_obj = Disease.objects.get(name=top_disease_name)
                rep['treatment_solutions'] = disease_obj.treatment_solutions
                rep['recovery_steps'] = disease_obj.recovery_steps
                rep['description'] = disease_obj.description
                rep['recommendation'] = results[0].get('recommendation', '')
            except Disease.DoesNotExist:
                rep['treatment_solutions'] = ""
                rep['recovery_steps'] = ""
                rep['description'] = ""
                rep['recommendation'] = ""
        else:
            rep['treatment_solutions'] = ""
            rep['recovery_steps'] = ""
            rep['description'] = ""
            rep['recommendation'] = results[0].get("message") if results else "Belum cukup gejala"
            
        return rep

from .models import Testimonial, Message

class TestimonialSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    profile_picture = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Testimonial
        fields = ['id', 'user_name', 'profile_picture', 'rating', 'content', 'created_at']

    def get_profile_picture(self, obj):
        request = self.context.get('request')
        if obj.user.profile_picture:
            url = obj.user.profile_picture.url
            if request:
                return request.build_absolute_uri(url)
            return url
        return None

class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)
    sender_role = serializers.CharField(source='sender.role', read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'sender_name', 'sender_role', 'receiver', 'content', 'timestamp', 'is_read']
