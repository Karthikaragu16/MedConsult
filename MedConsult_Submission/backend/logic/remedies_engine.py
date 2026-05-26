REMEDIES_DB = {
    'fever': {
        'tips': ['Drink plenty of fluids', 'Get adequate rest', 'Use a cool compress'],
        'dos': ['Monitor temperature regularly', 'Wear light clothing'],
        'donts': ['Avoid heavy exercise', 'Do not skip meals'],
        'warnings': ['Consult a doctor if fever lasts more than 3 days.']
    },
    'cough': {
        'tips': ['Honey and ginger tea', 'Steam inhalation', 'Salt water gargle'],
        'dos': ['Keep your throat warm', 'Drink warm water'],
        'donts': ['Avoid cold food and drinks', 'Avoid smoking'],
        'warnings': ['If you cough up blood, seek immediate help.']
    },
    'chest pain': {
        'tips': ['Stop any physical activity', 'Loosen tight clothing'],
        'dos': ['Call for help immediately', 'Stay calm'],
        'donts': ['Do not drive yourself to the hospital', 'Do not ignore the pain'],
        'warnings': ['Chest pain is a medical emergency.']
    },
    'headache': {
        'tips': ['Rest in a quiet, dark room', 'Hydrate well', 'Gentle neck stretches'],
        'dos': ['Maintain a regular sleep schedule'],
        'donts': ['Avoid loud noises and bright lights', 'Avoid excessive caffeine'],
        'warnings': ['If accompanied by confusion or vision loss, see a doctor.']
    }
}

def get_intelligent_remedies(symptoms):
    """
    Returns detailed remedies, dos/donts, and warnings for a list of symptoms.
    """
    results = []
    
    for symptom in symptoms:
        symptom = symptom.lower()
        if symptom in REMEDIES_DB:
            results.append({
                'symptom': symptom,
                'data': REMEDIES_DB[symptom]
            })
            
    if not results:
        return [{
            'symptom': 'General',
            'data': {
                'tips': ['Rest and stay hydrated.', 'Monitor your symptoms.'],
                'dos': ['Maintain good hygiene.'],
                'donts': ['Do not overexert yourself.'],
                'warnings': ['If symptoms persist, consult a professional.']
            }
        }]
        
    return results
