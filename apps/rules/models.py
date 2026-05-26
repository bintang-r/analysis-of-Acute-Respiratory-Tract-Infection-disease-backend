from django.db import models
from apps.diseases.models import Disease
from apps.symptoms.models import Symptom

class Rule(models.Model):
    code = models.CharField(max_length=10, unique=True)
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE)

    def __str__(self):
        return self.code

class RuleSymptom(models.Model):
    rule = models.ForeignKey(Rule, on_delete=models.CASCADE, related_name='rule_symptoms')
    symptom = models.ForeignKey(Symptom, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.rule.code} - {self.symptom.code}"

class CertaintyFactor(models.Model):
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name='cf_values')
    symptom = models.ForeignKey(Symptom, on_delete=models.CASCADE)
    expert_cf = models.FloatField()

    def __str__(self):
        return f"{self.disease.code} - {self.symptom.code} ({self.expert_cf})"
