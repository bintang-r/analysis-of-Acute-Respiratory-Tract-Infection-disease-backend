# pyrefly: ignore [missing-import]
from django.db import models
# pyrefly: ignore [missing-import]
from django.conf import settings
# pyrefly: ignore [missing-import]
from apps.symptoms.models import Symptom

class Consultation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    consultation_date = models.DateTimeField(auto_now_add=True)
    final_diagnosis = models.CharField(max_length=255, blank=True, null=True)
    confidence_result = models.FloatField(blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)

class ConsultationDetail(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='details')
    symptom = models.ForeignKey(Symptom, on_delete=models.CASCADE)
    user_cf = models.FloatField()

class Testimonial(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Testimonial by {self.user.username}"

class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"From {self.sender.username} at {self.timestamp}"
