import os
import joblib
import pandas as pd
import re
import nltk
from nltk.tokenize import word_tokenize

# Ensure nltk packages are available (download quietly if needed)
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_path = os.path.join(base_dir, 'dataset', 'symptom_model.pkl')
dataset_path = os.path.join(base_dir, 'dataset', 'symptoms_dataset.csv')

# Load Model
if os.path.exists(model_path):
    ml_model = joblib.load(model_path)
else:
    ml_model = None

# Load Dataset for meta-info lookup
if os.path.exists(dataset_path):
    df = pd.read_csv(dataset_path)
    # create a lookup dictionary based on Condition
    condition_meta = {}
    for _, row in df.iterrows():
        condition_meta[row['Condition']] = {
            'Severity': row['Severity'],
            'Specialty': row['Specialty'],
            'Remedies': [r.strip() for r in re.split(r'[|,]', row['Remedies'])],
            'Warnings': [row['Warnings']],
            'Emergency': row['Emergency']
        }
else:
    condition_meta = {}

def analyze_symptoms(user_text):
    """
    Analyzes user text using a scikit-learn Machine Learning model to predict conditions.
    Extracts keywords using NLTK.
    """
    text = user_text.lower()
    
    if not ml_model or not condition_meta:
        return {
            'status': 'error',
            'message': 'ML Model or Dataset not found. Please train the model first.',
            'severity': 'Low',
            'emergency': False
        }
        
    # Use NLTK for basic tokenization and symptom keyword extraction (basic heuristic)
    tokens = word_tokenize(text)
    # Just an example of nltk usage: extract words > 3 letters as potential "symptom" keywords
    found_symptoms = [word for word in tokens if len(word) > 3 and word not in ['have', 'been', 'feeling', 'like', 'with', 'some', 'very']]
    
    if not found_symptoms:
        found_symptoms = ["general malaise"]
    
    # Predict Condition using ML model
    predicted_condition = ml_model.predict([text])[0]
    
    # Retrieve metadata for predicted condition
    data = condition_meta.get(predicted_condition, {
        'Severity': 'Low',
        'Specialty': 'General Physician',
        'Remedies': ['Rest and stay hydrated'],
        'Warnings': ['Consult a doctor if symptoms persist.'],
        'Emergency': False
    })
    
    severity = data['Severity']
    is_emergency = data['Emergency']
    
    # Basic Mood detection
    mood = "Neutral"
    if re.search(r'\b(sad|depressed|low|unhappy|crying|tired)\b', text):
        mood = "Low / Stressed"
    elif re.search(r'\b(happy|better|good|fine)\b', text):
        mood = "Positive"

    return {
        'status': 'success',
        'symptoms': found_symptoms,
        'condition': predicted_condition,
        'possible_conditions': [predicted_condition],
        'severity': severity,
        'specialty': data['Specialty'],
        'remedies': data['Remedies'],
        'warnings': data['Warnings'],
        'emergency': is_emergency,
        'mood': mood,
        'raw_text': user_text
    }
