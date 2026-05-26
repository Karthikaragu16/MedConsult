import random

HEALTH_RESPONSES = {
    'greeting': ["Hello! I'm your health assistant. How are you feeling today?", "Hi! I can help you with health queries. What's on your mind?"],
    'thanks': ["You're welcome! Stay healthy.", "Happy to help. Take care!"],
    'appointment': ["You can book an appointment through the 'Find Doctor' tab.", "Would you like me to recommend a specialist for your symptoms?"],
    'generic': ["I'm a health-focused assistant. Please ask me about symptoms, remedies, or doctor advice.", "I can provide guidance on health matters. Could you describe how you're feeling?"]
}

def get_chatbot_response(user_message, context=None, state=None):
    """
    Generates a health-focused response based on user message and current health context.
    Returns (response_string, new_state)
    """
    msg = user_message.lower()
    
    # Check for active state
    if state:
        if state == 'ask_fever_duration':
            if any(word in msg for word in ['day', 'week', 'hour', 'month']):
                return f"I see. Since your fever has lasted {user_message}, make sure to stay hydrated. If it exceeds 3 days, please see a General Physician.", None
            else:
                return "Please tell me how many days you've had the fever.", 'ask_fever_duration'
                
        if state == 'ask_breathing':
            if 'yes' in msg or 'yeah' in msg or 'do' in msg:
                return "Chest pain with breathing difficulty is a medical EMERGENCY. Please seek immediate medical help or call an ambulance.", None
            else:
                return "Even without breathing issues, chest pain should be evaluated by a Cardiologist. Please rest and seek medical advice.", None

    # Follow-up triggers
    if 'fever' in msg:
        return "I understand you have a fever. How long have you been experiencing this high temperature?", 'ask_fever_duration'
        
    if 'chest pain' in msg:
        return "Chest pain can be serious. Are you also experiencing any difficulty breathing?", 'ask_breathing'

    # 1. Check Context (Context-Awareness)
    if context and 'symptoms' in context:
        symptoms_str = ", ".join(context['symptoms'])
        if any(word in msg for word in ['what', 'help', 'do', 'advice']):
            return f"Regarding your symptoms ({symptoms_str}), I recommend checking the remedies provided in your dashboard. Would you like to see a {context.get('specialty', 'doctor')}?", None

    # 2. Pattern Matching
    if any(word in msg for word in ['hi', 'hello', 'hey']):
        return random.choice(HEALTH_RESPONSES['greeting']), None
    
    if any(word in msg for word in ['thank', 'thanks', 'ty']):
        return random.choice(HEALTH_RESPONSES['thanks']), None
        
    if 'appointment' in msg or 'book' in msg:
        return random.choice(HEALTH_RESPONSES['appointment']), None

    # 3. Default
    return random.choice(HEALTH_RESPONSES['generic']), None
