# STEP 4: AI SYMPTOM ANALYSIS ENGINE
# Uses Natural Language Processing (NLP) to map symptoms to conditions and severity.

def analyze_symptoms(user_text):
    """
    Analyzes natural language text to extract symptoms and assess health.
    Matches Feature 2 (AI Analysis) and Feature 7 (Emergency Alert).
    """
    text = user_text.lower()
    
    # 1. Symptom Mapping
    symptoms_found = []
    if "headache" in text: symptoms_found.append("Headache")
    if "fever" in text: symptoms_found.append("Fever")
    if "chest pain" in text: symptoms_found.append("Chest Pain")
    if "cough" in text: symptoms_found.append("Cough")
    if "stomach" in text: symptoms_found.append("Stomach Pain")
    
    # 2. Condition & Severity Logic
    condition = "General Consultation"
    severity = "Low"
    specialty = "General Physician"
    emergency = False
    
    if "Chest Pain" in symptoms_found:
        condition = "Cardiac Concern"
        severity = "High"
        specialty = "Cardiologist"
        emergency = True
    elif "Fever" in symptoms_found and "Headache" in symptoms_found:
        condition = "Viral Infection"
        severity = "Medium"
        specialty = "General Physician"
    
    return {
        "symptoms": symptoms_found,
        "condition": condition,
        "severity": severity,
        "specialty": specialty,
        "emergency": emergency
    }
