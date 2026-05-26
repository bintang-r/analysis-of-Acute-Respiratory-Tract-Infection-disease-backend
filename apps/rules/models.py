# pyrefly: ignore [missing-import]
from django.db import models
# pyrefly: ignore [missing-import]
from apps.diseases.models import Disease
# pyrefly: ignore [missing-import]
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

class DatasetRow(models.Model):
    age = models.IntegerField()
    batuk_kering = models.IntegerField(default=0)
    batuk_berdahak = models.IntegerField(default=0)
    demam = models.IntegerField(default=0)
    pilek = models.IntegerField(default=0)
    hidung_tersumbat = models.IntegerField(default=0)
    sesak_napas = models.IntegerField(default=0)
    nyeri_tenggorokan = models.IntegerField(default=0)
    sakit_kepala = models.IntegerField(default=0)
    mual_muntah = models.IntegerField(default=0)
    nyeri_dada = models.IntegerField(default=0)
    suara_serak = models.IntegerField(default=0)
    kelelahan = models.IntegerField(default=0)
    berkeringat_malam = models.IntegerField(default=0)
    nafsu_makan_turun = models.IntegerField(default=0)
    hilang_penciuman = models.IntegerField(default=0)
    nyeri_saat_menelan = models.IntegerField(default=0)
    diagnosis = models.CharField(max_length=100)

    def __str__(self):
        return f"Row {self.id} - {self.diagnosis}"
