from collections import defaultdict
from django.db import transaction
from apps.symptoms.models import Symptom
from apps.diseases.models import Disease
from apps.rules.models import Rule, RuleSymptom, CertaintyFactor, DatasetRow


class DiagnosisService:
    """
    Computes disease diagnosis using the Certainty Factor (CF) method.
    Combines user confidence values (user_cf) with expert-provided weights (expert_cf)
    and iteratively combines across all matching symptoms.
    """

    @staticmethod
    def combine_cf(cf1: float, cf2: float) -> float:
        """Kombinasi CF standar MYCIN yang menangani nilai negatif maupun positif"""
        if cf1 >= 0 and cf2 >= 0:
            return cf1 + cf2 * (1 - cf1)
        elif cf1 < 0 and cf2 < 0:
            return cf1 + cf2 * (1 + cf1)
        else:
            return (cf1 + cf2) / (1 - min(abs(cf1), abs(cf2)))

    @staticmethod
    def calculate_diagnosis(selected_symptoms: list) -> list:
        # Minimum gejala 2
        if not selected_symptoms or len(selected_symptoms) < 2:
            return [{"message": "Belum cukup gejala untuk diagnosis spesifik"}]

        user_cf_map = {item["symptom_id"]: float(item["user_cf"]) for item in selected_symptoms}
        user_symptom_ids = set(user_cf_map.keys())

        # 1. FORWARD CHAINING FILTER
        possible_diseases = set()
        rules = Rule.objects.prefetch_related('rule_symptoms').all()
        for rule in rules:
            rule_symptom_ids = set(rs.symptom_id for rs in rule.rule_symptoms.all())
            matched_ids = user_symptom_ids.intersection(rule_symptom_ids)
            matched_count = len(matched_ids)
            match_ratio = matched_count / len(rule_symptom_ids) if rule_symptom_ids else 0
            
            # Syarat lolos Forward Chaining: minimal 2 gejala cocok ATAU kecocokan >= 50%
            if matched_count >= 2 or match_ratio >= 0.5:
                possible_diseases.add(rule.disease_id)

        # Jika tidak ada penyakit yang memenuhi syarat Forward Chaining
        if not possible_diseases:
            return [{"message": "Belum cukup gejala untuk diagnosis spesifik"}]

        # 2. CERTAINTY FACTOR CALCULATION
        cf_entries = CertaintyFactor.objects.filter(
            disease_id__in=possible_diseases
        ).select_related('disease', 'symptom')

        disease_cf_map = defaultdict(list)
        for entry in cf_entries:
            disease_cf_map[entry.disease_id].append(entry)

        # Ambil detail penyakit untuk return JSON
        diseases_map = {d.id: d for d in Disease.objects.filter(id__in=possible_diseases)}
        results = []

        for disease_id, entries in disease_cf_map.items():
            combined_cf = 0.0
            matched = False
            disease = diseases_map[disease_id]
            matched_symptoms_list = []
            trace_steps = []

            for entry in entries:
                expert_cf = float(entry.expert_cf)
                
                # CF Penalty: Jika gejala tidak dipilih user, beri nilai CF negatif
                if entry.symptom_id in user_cf_map:
                    user_cf = user_cf_map[entry.symptom_id]
                    matched_symptoms_list.append(entry.symptom.name)
                else:
                    user_cf = -0.3
                
                cf_current = user_cf * expert_cf
                old_combined = combined_cf

                if not matched:
                    combined_cf = cf_current
                    matched = True
                    formula = f"CF({entry.symptom.name}) = {user_cf} * {expert_cf} = {cf_current:.3f}"
                    combine_formula = f"CF Gabungan Awal = {combined_cf:.3f}"
                else:
                    combined_cf = DiagnosisService.combine_cf(combined_cf, cf_current)
                    formula = f"CF({entry.symptom.name}) = {user_cf} * {expert_cf} = {cf_current:.3f}"
                    if old_combined >= 0 and cf_current >= 0:
                        combine_formula = f"{old_combined:.3f} + {cf_current:.3f} * (1 - {old_combined:.3f}) = {combined_cf:.3f}"
                    elif old_combined < 0 and cf_current < 0:
                        combine_formula = f"{old_combined:.3f} + {cf_current:.3f} * (1 + {old_combined:.3f}) = {combined_cf:.3f}"
                    else:
                        min_abs = min(abs(old_combined), abs(cf_current))
                        combine_formula = f"({old_combined:.3f} + {cf_current:.3f}) / (1 - {min_abs:.3f}) = {combined_cf:.3f}"

                trace_steps.append({
                    "symptom": entry.symptom.name,
                    "user_cf": user_cf,
                    "expert_cf": expert_cf,
                    "cf_current": round(cf_current, 3),
                    "old_combined": round(old_combined, 3),
                    "new_combined": round(combined_cf, 3),
                    "formula": formula,
                    "combine_formula": combine_formula
                })

            # Clamp CF ke dalam rentang [-1.0, 1.0]
            clamped_cf = max(-1.0, min(1.0, combined_cf))
            percentage = round(clamped_cf * 100, 2)
            
            # Minimum Diagnosis Threshold: Harus >= 35%
            if percentage >= 35.0:
                results.append({
                    "disease": disease.name,
                    "percentage": percentage,
                    "matched_symptoms": matched_symptoms_list,
                    "calculation_trace": trace_steps,
                    "recommendation": getattr(disease, 'treatment_solutions', getattr(disease, 'description', 'Segera konsultasikan ke dokter.'))
                })

        # Jika semua penyakit di bawah threshold
        if not results:
            return [{"message": "Belum cukup gejala untuk diagnosis spesifik"}]

        results.sort(key=lambda x: x["percentage"], reverse=True)
        return results


@transaction.atomic
def recalculate_rules_and_cf():
    CertaintyFactor.objects.all().delete()
    RuleSymptom.objects.all().delete()
    Rule.objects.all().delete()

    symptom_columns = [
        ("batuk_kering", "S01"), ("batuk_berdahak", "S02"), ("demam", "S03"),
        ("pilek", "S04"), ("hidung_tersumbat", "S05"), ("sesak_napas", "S06"),
        ("nyeri_tenggorokan", "S07"), ("sakit_kepala", "S08"), ("mual_muntah", "S09"),
        ("nyeri_dada", "S10"), ("suara_serak", "S11"), ("kelelahan", "S12"),
        ("berkeringat_malam", "S13"), ("nafsu_makan_turun", "S14"), 
        ("hilang_penciuman", "S15"), ("nyeri_saat_menelan", "S16")
    ]
    
    # 7. CEK SYMPTOM S17-S20
    age_symptoms_data = [
        ('S17', 'Kategori Umur Balita/Anak'),
        ('S18', 'Kategori Umur Remaja'),
        ('S19', 'Kategori Umur Dewasa'),
        ('S20', 'Kategori Umur Lansia'),
    ]
    for code, name in age_symptoms_data:
        Symptom.objects.get_or_create(code=code, defaults={'name': name})

    symptom_objs = {s.code: s for s in Symptom.objects.all()}
    disease_objs = {d.name.lower(): d for d in Disease.objects.all()}

    disease_counts = defaultdict(int)
    symptom_disease_counts = defaultdict(lambda: defaultdict(int))

    for r in DatasetRow.objects.iterator():
        diag = (r.diagnosis or "").strip().lower()

        if diag not in disease_objs:
            continue

        disease_counts[diag] += 1

        for attr, code in symptom_columns:
            if getattr(r, attr, 0) == 1:
                symptom_disease_counts[diag][code] += 1

        age = r.age
        if age is not None:
            if age <= 12:
                symptom_disease_counts[diag]["S17"] += 1
            elif age <= 18:
                symptom_disease_counts[diag]["S18"] += 1
            elif age <= 60:
                symptom_disease_counts[diag]["S19"] += 1
            else:
                symptom_disease_counts[diag]["S20"] += 1

    rules_to_create = []
    cfs_to_create = []
    rule_symptoms_to_create = []

    for d_name_lower, d_obj in disease_objs.items():
        total_cases = disease_counts[d_name_lower]
        if total_cases == 0:
            continue

        rule_obj = Rule.objects.create(code=f"R{d_obj.code[1:]}", disease=d_obj)

        for code, s_obj in symptom_objs.items():
            s_count = symptom_disease_counts[d_name_lower][code]
            prob = round(s_count / total_cases, 3) if total_cases > 0 else 0.0

            if prob > 0:
                cfs_to_create.append(CertaintyFactor(
                    disease=d_obj, symptom=s_obj, expert_cf=prob
                ))

            if prob >= 0.20:
                rule_symptoms_to_create.append(RuleSymptom(
                    rule=rule_obj, symptom=s_obj
                ))

    CertaintyFactor.objects.bulk_create(cfs_to_create)
    RuleSymptom.objects.bulk_create(rule_symptoms_to_create)
