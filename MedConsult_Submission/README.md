# AI-Based Virtual Health Assistant

A full-stack web application built using Python Flask, HTML/CSS/JS, MySQL, and Machine Learning (`scikit-learn`, `nltk`, `SpeechRecognition`). This platform contains separate modules for Patients and Doctors, providing intelligent symptom analysis, home remedy recommendations, and a comprehensive appointment booking system.

## Features

### Patient Module
- **Registration & Login**: Secure authentication with password hashing.
- **Voice & Text Symptom Input**: Input symptoms via typing or speech (using Python `SpeechRecognition` / Web Speech API).
- **AI Symptom Analysis**: Uses an ML model (`scikit-learn` Naive Bayes pipeline trained on a symptoms dataset) to predict potential conditions based on natural language input.
- **Smart Chatbot**: Follow-up questions to drill down on symptoms (e.g., asking for fever duration) before recommending treatments.
- **Home Remedies**: Condition-specific remedies (Do's and Don'ts).
- **Appointment Booking**: Intelligent doctor recommendations based on predicted conditions and specialties (e.g., Cardiologist for chest pain). Prevents double booking.

### Doctor Module
- **Registration & Login**: Doctor-specific portal.
- **Dashboard**: View total appointments, upcoming patient list ordered by time.
- **Appointment Management**: Accept appointments, update status, and view patient symptom history and predicted disease.

## Project Structure

```
├── backend/
│   ├── app.py                     # Main Flask Application & API Routes
│   ├── requirements.txt           # Python Dependencies
│   ├── database_schema.sql        # Full MySQL Database Schema
│   ├── dataset/
│   │   ├── symptoms_dataset.csv   # Sample dataset mapping symptoms to conditions
│   │   └── symptom_model.pkl      # Trained ML Model (scikit-learn)
│   ├── logic/
│   │   ├── auth_manager.py        # Hashing & auth logic
│   │   ├── chatbot_engine.py      # State-based Chatbot logic
│   │   ├── doctor_recommender.py  # Recommends doctors based on condition
│   │   ├── ml_model.py            # Script to train the ML model
│   │   └── symptom_analyzer.py    # Predicts conditions using ML & NLTK
│   └── uploads/                   # Patient medical reports
├── frontend/
│   ├── static/                    # CSS, JS, Images
│   └── templates/                 # HTML UI Pages (Jinja2)
└── README.md                      # This file
```

## Setup & Installation Instructions

**1. Prerequisites:**
- Python 3.8+
- MySQL Server running locally

**2. Database Setup:**
- Open your MySQL command line or Workbench.
- Execute the commands found in `backend/database_schema.sql` to generate the required tables.
- Make sure to update your MySQL credentials inside `backend/app.py` (`app.config['MYSQL_USER']`, `app.config['MYSQL_PASSWORD']`).

**3. Install Dependencies:**
```bash
python -m pip install -r backend/requirements.txt
```

**4. Train the ML Model:**
Before running the application, you must train the Scikit-Learn symptom predictor model:
```bash
python backend/logic/ml_model.py
```
This will generate `symptom_model.pkl` in the `dataset` folder.

**5. Run the Application:**
Navigate to the root directory in your terminal and start the Flask server:
```bash
python backend/app.py
```

**6. Access the Web App:**
Open your browser and navigate to: `http://127.0.0.1:5000`
