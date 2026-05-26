import pandas as pd
import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

def train_and_save_model():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dataset_path = os.path.join(base_dir, 'dataset', 'symptoms_dataset.csv')
    model_path = os.path.join(base_dir, 'dataset', 'symptom_model.pkl')
    
    # Load dataset
    if not os.path.exists(dataset_path):
        print("Dataset not found!")
        return False
        
    df = pd.read_csv(dataset_path)
    
    # Features and Labels
    X = df['Symptoms']
    y = df['Condition']
    
    # Create a pipeline that vectorizes the text then applies Naive Bayes
    text_clf = Pipeline([
        ('tfidf', TfidfVectorizer(stop_words='english')),
        ('clf', MultinomialNB()),
    ])
    
    # Train the model
    text_clf.fit(X, y)
    
    # Save the model
    joblib.dump(text_clf, model_path)
    print("Model trained and saved to", model_path)
    return True

if __name__ == "__main__":
    train_and_save_model()
