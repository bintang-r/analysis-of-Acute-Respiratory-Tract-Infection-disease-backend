# pyrefly: ignore [missing-import]
from rest_framework import serializers
from .models import Symptom

class SymptomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Symptom
        fields = '__all__'
