from django.db import models
from django.conf import settings
from apps.symptoms.models import Symptom

class Consultation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    consultation_date = models.DateTimeField(auto_now_add=True)
    final_diagnosis = models.CharField(max_length=255, blank=True, null=True)
    confidence_result = models.FloatField(blank=True, null=True)

class ConsultationDetail(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='details')
    symptom = models.ForeignKey(Symptom, on_delete=models.CASCADE)
    user_cf = models.FloatField()
