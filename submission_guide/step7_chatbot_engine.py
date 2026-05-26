# STEP 7: AI CHATBOT ENGINE
# Handles interactive health-focused conversation.

def get_chatbot_response(user_message, history=None):
    """
    Generates health-focused responses.
    Matches Feature 4.
    """
    msg = user_message.lower()
    
    # Context awareness (simulated with keyword matching)
    if "symptom" in msg or "feeling" in msg:
        return "I can help with that. Please describe exactly where you feel discomfort."
    
    if "fever" in msg:
        return "For fever, I recommend rest and monitoring your temperature. If it stays above 102°F, see a doctor."
        
    if "doctor" in msg:
        return "You can book a specialist from your dashboard. Would you like me to recommend one based on your last check?"
        
    return "I am your MedConsult assistant. I can help with symptoms, remedies, or finding doctors. What's on your mind?"
