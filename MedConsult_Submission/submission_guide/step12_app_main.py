# STEP 12: MAIN APPLICATION INTEGRATION
# This file ties all the modules together into the final Flask application.
# Matches Feature 10 (Backend + Database Integration).

from flask import Flask, render_template, request, session, redirect, url_for
import mysql.connector
from step3_auth_management import verify_password
from step4_symptom_analyzer import analyze_symptoms
from step5_doctor_recommender import get_recommendations
from step7_chatbot_engine import get_chatbot_response

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

def get_db_connection():
    """Returns a new MySQL database connection."""
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='health_assistant'
    )

def get_all_doctors_from_db():
    """Fetches all doctors with their hospital name from the database."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT d.id, d.name, d.dept, d.rating, d.availability, d.location,
               h.name AS hospital_name
        FROM doctor d
        JOIN hospitals h ON d.hospital_id = h.id
    """)
    doctors = cursor.fetchall()
    cursor.close()
    conn.close()
    return doctors


@app.route('/dashboard')
def dashboard():
    """Main landing page after login."""
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', patient=session['user'])

@app.route('/analyze', methods=['POST'])
def handle_analysis():
    """Endpoint for Feature 2: AI Symptom Analysis."""
    user_input = request.form['symptoms']
    result = analyze_symptoms(user_input)
    
    # Save to session/history
    session['last_analysis'] = result
    
    # Feature 3: Smart Doctor Recommendation
    doctors = get_all_doctors_from_db() # Mock DB call
    recommendations = get_recommendations(result, doctors)
    
    return render_template('index.html', analysis=result, doctors=recommendations)

@app.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint for Feature 4: AI Chatbot."""
    user_msg = request.json['message']
    response = get_chatbot_response(user_msg)
    return {'response': response}

if __name__ == "__main__":
    app.run(debug=True)
