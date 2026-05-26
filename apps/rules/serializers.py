from rest_framework import serializers
from .models import Rule, CertaintyFactor

class RuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rule
        fields = '__all__'

class CertaintyFactorSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertaintyFactor
        fields = '__all__'
