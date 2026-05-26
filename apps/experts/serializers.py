from rest_framework import serializers
from .models import HealthExpert

class HealthExpertSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthExpert
        fields = '__all__'
