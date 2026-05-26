# pyrefly: ignore [missing-import]
from apps.rules.models import Rule, CertaintyFactor
# pyrefly: ignore [missing-import]
from apps.diseases.models import Disease

class DiagnosisService:
    @staticmethod
    def calculate_diagnosis(selected_symptoms):
        """
        selected_symptoms = [{'symptom_id': 1, 'user_cf': 0.8}, ...]
        """
        user_symptoms_dict = {item['symptom_id']: item['user_cf'] for item in selected_symptoms}
        symptom_ids = list(user_symptoms_dict.keys())
        
        # Forward chaining: find diseases that match the selected symptoms
        cf_rules = CertaintyFactor.objects.filter(symptom_id__in=symptom_ids)
        
        disease_scores = {}
        
        for cf in cf_rules:
            disease_id = cf.disease_id
            expert_cf = cf.expert_cf
            user_cf = user_symptoms_dict[cf.symptom_id]
            
            # CF rule = expert_cf * user_cf
            cf_he_user = expert_cf * user_cf
            
            if disease_id not in disease_scores:
                disease_scores[disease_id] = [cf_he_user]
            else:
                disease_scores[disease_id].append(cf_he_user)
        
        # Calculate CF Combine for each disease
        results = []
        for disease_id, cf_list in disease_scores.items():
            if not cf_list:
                continue
                
            cf_combine = cf_list[0]
            for i in range(1, len(cf_list)):
                cf_combine = cf_combine + (cf_list[i] * (1 - cf_combine))
                
            disease = Disease.objects.get(id=disease_id)
            percentage = round(cf_combine * 100, 2)
            
            results.append({
                'disease': disease.name,
                'disease_id': disease.id,
                'percentage': percentage,
                'recommendation': disease.recommendation
            })
            
        # Sort by percentage descending
        results.sort(key=lambda x: x['percentage'], reverse=True)
        return results
