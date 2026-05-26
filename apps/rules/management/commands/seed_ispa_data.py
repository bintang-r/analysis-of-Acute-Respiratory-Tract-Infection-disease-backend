from django.core.management.base import BaseCommand
from apps.symptoms.models import Symptom
from apps.diseases.models import Disease
from apps.rules.models import Rule, RuleSymptom, CertaintyFactor
from apps.experts.models import HealthExpert
from apps.authentication.models import User

class Command(BaseCommand):
    help = 'Seeds the database with ISPA data'

    def handle(self, *args, **kwargs):
        # 25 Symptoms
        symptoms_data = [
            ("S01", "Batuk"),
            ("S02", "Pilek"),
            ("S03", "Sesak napas"),
            ("S04", "Demam"),
            ("S05", "Sakit tenggorokan"),
            ("S06", "Nyeri otot"),
            ("S07", "Kelelahan"),
            ("S08", "Sakit kepala"),
            ("S09", "Nyeri dada"),
            ("S10", "Dahak kuning/hijau"),
            ("S11", "Hidung tersumbat"),
            ("S12", "Napas berbunyi (mengi)"),
            ("S13", "Mual"),
            ("S14", "Muntah"),
            ("S15", "Kehilangan penciuman"),
            ("S16", "Nyeri sendi"),
            ("S17", "Beringus cair"),
            ("S18", "Suara serak"),
            ("S19", "Mata berair"),
            ("S20", "Menggigil"),
            ("S21", "Nyeri menelan"),
            ("S22", "Keringat malam"),
            ("S23", "Napas cepat"),
            ("S24", "Bibir biru"),
            ("S25", "Penurunan kesadaran"),
        ]
        
        for code, name in symptoms_data:
            Symptom.objects.get_or_create(code=code, defaults={"name": name})
            
        # 7 Diseases
        diseases_data = [
            ("D01", "ISPA ringan", "Rest and hydration"),
            ("D02", "Bronkitis", "Consult doctor for medication"),
            ("D03", "Sinusitis", "Use nasal decongestant"),
            ("D04", "Faringitis", "Gargle with warm salt water"),
            ("D05", "Laringitis", "Rest your voice"),
            ("D06", "Tonsilitis", "Cold drinks and pain relievers"),
            ("D07", "ISPA berat", "Immediate medical attention required!"),
        ]
        
        for code, name, rec in diseases_data:
            Disease.objects.get_or_create(code=code, defaults={"name": name, "recommendation": rec})
            
        # 30 CF rules mappings
        mappings = [
            ("D01", "S01", 0.6), ("D01", "S02", 0.8), ("D01", "S04", 0.4), ("D01", "S11", 0.6), ("D01", "S17", 0.8),
            ("D02", "S01", 0.8), ("D02", "S03", 0.6), ("D02", "S04", 0.6), ("D02", "S09", 0.4), ("D02", "S10", 0.8),
            ("D03", "S02", 0.6), ("D03", "S08", 0.8), ("D03", "S11", 0.8), ("D03", "S15", 0.6), ("D03", "S21", 0.4),
            ("D04", "S04", 0.6), ("D04", "S05", 0.8), ("D04", "S21", 0.8), ("D04", "S07", 0.4),
            ("D05", "S01", 0.4), ("D05", "S05", 0.6), ("D05", "S18", 0.8), ("D05", "S21", 0.6),
            ("D06", "S04", 0.8), ("D06", "S05", 0.8), ("D06", "S21", 0.8), ("D06", "S13", 0.4),
            ("D07", "S03", 0.8), ("D07", "S04", 0.8), ("D07", "S23", 0.8), ("D07", "S24", 0.8), ("D07", "S25", 0.8),
        ]
        
        Rule.objects.all().delete()
        RuleSymptom.objects.all().delete()
        CertaintyFactor.objects.all().delete()
        
        for idx, (d_code, s_code, cf) in enumerate(mappings):
            disease = Disease.objects.get(code=d_code)
            symptom = Symptom.objects.get(code=s_code)
            
            rule, _ = Rule.objects.get_or_create(code=f"R{idx+1:02d}", disease=disease)
            RuleSymptom.objects.get_or_create(rule=rule, symptom=symptom)
            CertaintyFactor.objects.get_or_create(disease=disease, symptom=symptom, expert_cf=cf)
            
        # 3 Health Experts
        experts = [
            ("Dr. Andi", "Pulmonologist", "RS Sehat Selalu"),
            ("Dr. Budi", "General Practitioner", "Klinik Medika"),
            ("Dr. Clara", "ENT Specialist", "RS THT Pusat"),
        ]
        
        for name, prof, wp in experts:
            HealthExpert.objects.get_or_create(name=name, defaults={"profession": prof, "workplace": wp})
            
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@admin.com", "admin")
            
        self.stdout.write(self.style.SUCCESS('Successfully seeded ISPA data.'))
