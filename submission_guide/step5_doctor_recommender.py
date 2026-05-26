# STEP 5: SMART DOCTOR RECOMMENDATION SYSTEM
# Filters and ranks doctors based on analysis results.

def get_recommendations(analysis, all_doctors):
    """
    Ranks doctors based on specialization match and ratings.
    Matches Feature 3.
    """
    # Safely retrieve the target specialty from analysis result
    target_specialty = analysis.get('specialty', '')

    # Filter by specialty
    specialty_match = [d for d in all_doctors if d.get('dept', '') == target_specialty]
    other_doctors  = [d for d in all_doctors if d.get('dept', '') != target_specialty]

    # Sort by rating (highest first), default to 0.0 if 'rating' key is missing
    specialty_match.sort(key=lambda x: x.get('rating', 0.0), reverse=True)
    other_doctors.sort(key=lambda x: x.get('rating', 0.0), reverse=True)

    # Primary recommendations first
    recommended = specialty_match + other_doctors

    return recommended
