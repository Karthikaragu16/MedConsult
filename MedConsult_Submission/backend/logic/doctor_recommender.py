import random

def get_recommendations(doctors, analysis_result=None, location=None):
    """
    Filters and ranks doctors based on symptom analysis and user location.
    """
    recommended = []
    others = []
    
    target_specialty = analysis_result.get('specialty') if analysis_result else None
    
    for doc in doctors:
        # Add dummy data if missing
        if 'rating' not in doc:
            doc['rating'] = round(random.uniform(4.0, 5.0), 1)
        if 'availability' not in doc:
            doc['availability'] = random.choice(['Available Today', 'Available Tomorrow', 'Next Week'])
        
        # Match by specialty
        is_match = False
        if target_specialty and target_specialty.lower() in doc.get('dept', '').lower():
            is_match = True
            
        # Match by location (if provided)
        if location and location.lower() in doc.get('location', '').lower():
            # Increase priority if location matches
            pass
            
        if is_match:
            recommended.append(doc)
        else:
            others.append(doc)
            
    # Sort by rating
    recommended.sort(key=lambda x: x['rating'], reverse=True)
    others.sort(key=lambda x: x['rating'], reverse=True)
    
    return recommended, others
