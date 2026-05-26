# STEP 6: INTELLIGENT HOME REMEDIES ENGINE
# Provides specific remedies, dos, and don'ts based on symptoms.

def get_intelligent_remedies(symptoms):
    """
    Returns tailored advice for detected symptoms.
    Matches Feature 6.
    """
    remedy_data = {
        "Fever": {
            "dos": ["Rest in bed", "Drink 3L of water", "Apply cold sponge"],
            "donts": ["Avoid cold water showers", "Don't skip meals"],
            "tips": ["Ginger Tea", "Tulsi water"]
        },
        "Headache": {
            "dos": ["Rest in a dark room", "Stay hydrated"],
            "donts": ["Avoid bright screens", "No caffeine"],
            "tips": ["Peppermint oil rub", "Herbal tea"]
        },
        "Cough": {
            "dos": ["Steam inhalation", "Salt water gargle"],
            "donts": ["Avoid cold drinks", "No spicy food"],
            "tips": ["Honey and Ginger juice"]
        }
    }
    
    results = []
    for s in symptoms:
        if s in remedy_data:
            results.append({"symptom": s, "data": remedy_data[s]})
            
    return results
