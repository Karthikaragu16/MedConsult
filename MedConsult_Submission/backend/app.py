from flask import Flask, render_template, request, session, redirect, url_for, jsonify, send_file, make_response
from flask_mysqldb import MySQL
import MySQLdb.cursors
import os
import sys
import datetime
import threading
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from werkzeug.utils import secure_filename
import speech_recognition as sr
import io
from gtts import gTTS
# Add current directory to path for logic imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logic.symptom_analyzer import analyze_symptoms
from logic.doctor_recommender import get_recommendations
from logic.chatbot_engine import get_chatbot_response
from logic.remedies_engine import get_intelligent_remedies
from logic.report_generator import generate_pdf_report
from logic.auth_manager import hash_password, verify_password

# Initialize Flask with custom template and static folders
app = Flask(__name__, 
            template_folder='../frontend/templates',
            static_folder='../frontend/static')

app.secret_key = 'your_secret_key_here'
# Use absolute path so uploads work regardless of CWD
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# --- LOCAL MYSQL CONFIGURATION ---
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Karthika@16'
app.config['MYSQL_DB'] = 'health_assistant'

mysql = MySQL(app)

# ─── Email Reminder Configuration ────────────────────────────────────────────
# Update these with your real Gmail address and App Password
# (Gmail → Manage Account → Security → 2-Step Verification → App passwords)
EMAIL_SENDER   = 'your_email@gmail.com'      # ← App sender Gmail
EMAIL_PASSWORD = 'your_app_password_here'           # ← Paste your 16-char App Password here
EMAIL_ENABLED  = True    # Set False to disable all emails

_reminders_sent = set()  # tracks appointment IDs already reminded this session

def send_reminder_email(to_addr, subject, html_body):
    """Send an HTML email via Gmail SMTP. Fails silently if not configured."""
    if not EMAIL_ENABLED or not to_addr:
        return
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = EMAIL_SENDER
        msg['To']      = to_addr
        msg.attach(MIMEText(html_body, 'html'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as srv:
            srv.login(EMAIL_SENDER, EMAIL_PASSWORD)
            srv.sendmail(EMAIL_SENDER, to_addr, msg.as_string())
        print(f'[REMINDER] Email sent → {to_addr}')
    except Exception as e:
        print(f'[REMINDER] Email error: {e}')

def _reminder_loop():
    """Background thread: every 5 min, check for appointments ~1 hour away."""
    while True:
        try:
            conn = MySQLdb.connect(
                host='localhost', user='root',
                passwd='YOUR_DB_PASSWORD', db='health_assistant'
            )
            cur  = conn.cursor(MySQLdb.cursors.DictCursor)
            now  = datetime.datetime.now()
            # Window: appointments starting 55–65 min from now
            win_start = (now + datetime.timedelta(minutes=55)).strftime('%H:%M')
            win_end   = (now + datetime.timedelta(minutes=65)).strftime('%H:%M')
            today     = now.strftime('%Y-%m-%d')
            cur.execute("""
                SELECT a.id, a.appointment_date, a.appointment_time,
                       a.patient_mail, a.status,
                       p.name AS patient_name,
                       d.name AS doctor_name, d.mail AS doctor_mail,
                       d.dept, d.hospital_name
                FROM appointments a
                JOIN patient p ON p.mail = a.patient_mail
                JOIN doctor  d ON d.id   = a.doctor_id
                WHERE a.appointment_date = %s
                  AND a.status = 'Accepted'
            """, [today])
            rows = cur.fetchall()
            for row in rows:
                if row['id'] in _reminders_sent:
                    continue
                # Parse stored time string e.g. "9:00 AM" → datetime
                try:
                    t_str  = str(row['appointment_time']).strip()
                    # Handle both "9:00 AM" and "09:00:00" (timedelta) formats
                    if isinstance(row['appointment_time'], datetime.timedelta):
                        total = int(row['appointment_time'].total_seconds())
                        h, m  = total // 3600, (total % 3600) // 60
                        appt_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
                    else:
                        appt_dt = datetime.datetime.strptime(today + ' ' + t_str, '%Y-%m-%d %I:%M %p')
                except Exception:
                    continue
                diff_min = (appt_dt - now).total_seconds() / 60
                if 50 <= diff_min <= 70:
                    _reminders_sent.add(row['id'])
                    appt_label = appt_dt.strftime('%d %b %Y at %I:%M %p')
                    doc_label  = f"Dr. {row['doctor_name']} ({row['dept']})"
                    hosp       = row.get('hospital_name') or 'the clinic'

                    # ── Patient email ──
                    patient_html = f"""
                    <div style="font-family:Inter,sans-serif;max-width:520px;margin:auto;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.1);">
                      <div style="background:linear-gradient(135deg,#3b82f6,#1d4ed8);padding:1.5rem 2rem;">
                        <h2 style="color:#fff;margin:0;font-size:1.3rem;">⏰ Appointment Reminder</h2>
                        <p style="color:rgba(255,255,255,0.8);margin:0.3rem 0 0;font-size:0.85rem;">MedConsult Health Assistant</p>
                      </div>
                      <div style="padding:1.5rem 2rem;background:#f8fafc;">
                        <p style="color:#1e293b;font-size:0.95rem;">Hi <strong>{row['patient_name']}</strong>,</p>
                        <p style="color:#475569;">This is a reminder that your appointment is in <strong>~1 hour</strong>.</p>
                        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:1rem 1.25rem;margin:1rem 0;">
                          <p style="margin:0 0 0.4rem;color:#64748b;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.05em;">Appointment Details</p>
                          <p style="margin:0.2rem 0;color:#1e293b;"><strong>Doctor:</strong> {doc_label}</p>
                          <p style="margin:0.2rem 0;color:#1e293b;"><strong>Hospital:</strong> {hosp}</p>
                          <p style="margin:0.2rem 0;color:#1e293b;"><strong>Date & Time:</strong> {appt_label}</p>
                        </div>
                        <p style="color:#475569;font-size:0.85rem;">Please arrive 10 minutes early. Carry your ID and any previous prescriptions.</p>
                        <p style="color:#94a3b8;font-size:0.75rem;margin-top:1.5rem;">© 2026 MedConsult AI — This is an automated reminder. Do not reply.</p>
                      </div>
                    </div>"""
                    send_reminder_email(
                        row['patient_mail'],
                        f'⏰ Reminder: Appointment with {doc_label} in 1 Hour',
                        patient_html
                    )

                    # ── Doctor email ──
                    doctor_html = f"""
                    <div style="font-family:Inter,sans-serif;max-width:520px;margin:auto;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.1);">
                      <div style="background:linear-gradient(135deg,#10b981,#059669);padding:1.5rem 2rem;">
                        <h2 style="color:#fff;margin:0;font-size:1.3rem;">🩺 Upcoming Appointment</h2>
                        <p style="color:rgba(255,255,255,0.8);margin:0.3rem 0 0;font-size:0.85rem;">MedConsult Health Assistant</p>
                      </div>
                      <div style="padding:1.5rem 2rem;background:#f8fafc;">
                        <p style="color:#1e293b;font-size:0.95rem;">Hi <strong>Dr. {row['doctor_name']}</strong>,</p>
                        <p style="color:#475569;">You have a patient appointment in <strong>~1 hour</strong>.</p>
                        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:1rem 1.25rem;margin:1rem 0;">
                          <p style="margin:0 0 0.4rem;color:#64748b;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.05em;">Appointment Details</p>
                          <p style="margin:0.2rem 0;color:#1e293b;"><strong>Patient:</strong> {row['patient_name']}</p>
                          <p style="margin:0.2rem 0;color:#1e293b;"><strong>Date & Time:</strong> {appt_label}</p>
                          <p style="margin:0.2rem 0;color:#1e293b;"><strong>Hospital:</strong> {hosp}</p>
                        </div>
                        <p style="color:#94a3b8;font-size:0.75rem;margin-top:1.5rem;">© 2026 MedConsult AI — Automated reminder.</p>
                      </div>
                    </div>"""
                    send_reminder_email(
                        row['doctor_mail'],
                        f'🩺 Reminder: Patient {row["patient_name"]} in 1 Hour',
                        doctor_html
                    )
            conn.close()
        except Exception as ex:
            print(f'[REMINDER] Scheduler error: {ex}')
        time.sleep(300)  # check every 5 minutes

# Start reminder thread (only once — not in Flask reloader child)
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
    _t = threading.Thread(target=_reminder_loop, daemon=True)
    _t.start()
    print('[REMINDER] Background email scheduler started.')

# ── Auto-migrate: add missing columns safely ──────────────────────────────────
def _auto_migrate():
    """Adds any missing DB columns so the app works on older schemas."""
    try:
        conn = MySQLdb.connect(
            host='localhost', user='root',
            passwd='YOUR_DB_PASSWORD', db='health_assistant'
        )
        cur = conn.cursor()
        migrations = [
            "ALTER TABLE appointments ADD COLUMN IF NOT EXISTS patient_rating DECIMAL(2,1) DEFAULT NULL",
            "ALTER TABLE appointments ADD COLUMN IF NOT EXISTS consultation_mode VARCHAR(50) DEFAULT 'Physical'",
            "ALTER TABLE doctor ADD COLUMN IF NOT EXISTS hospital_id INT DEFAULT NULL",
        ]
        for sql in migrations:
            try:
                cur.execute(sql)
            except Exception:
                pass  # column may already exist
        conn.commit()
        conn.close()
        print('[MIGRATE] Auto-migration complete.')
    except Exception as ex:
        print(f'[MIGRATE] Skipped: {ex}')

_auto_migrate()


# --- ROUTES ---

@app.route("/", methods=["GET"])
def gateway():
    if 's_mail' in session:
        return redirect(url_for('dashboard'))
    
    # Cookie based new/returning user check
    returning_user = request.cookies.get('returning_user')
    if returning_user == 'true':
        return redirect(url_for('login'))
    else:
        return redirect(url_for('register'))

@app.route('/api/tts', methods=['GET'])
def text_to_speech():
    """Convert text to speech using gTTS and return MP3 audio."""
    text = request.args.get('text', '').strip()
    lang = request.args.get('lang', 'en')   # 'en' or 'ta'
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return send_file(buf, mimetype='audio/mpeg', as_attachment=False, download_name='speech.mp3')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/remedies_chat', methods=['POST'])
def remedies_chat():
    """AI home remedies chatbot with smart keyword extraction and doctor referral."""
    data        = request.get_json(force=True)
    raw_message = (data.get('message') or '').strip()
    message     = raw_message.lower()

    # ── 1. Detect "not improving" signals → refer to doctor ─────────────────
    not_improving = any(kw in message for kw in [
        'not working', 'not cured', 'not better', 'still sick', 'still pain',
        'getting worse', 'no improvement', "didn't help", "didn't work",
        'no relief', 'worsening', 'hospital', 'consult',
        'not recovering', 'not healed', 'still same', 'worse', 'not improving'
    ])
    if not_improving:
        return jsonify({
            'type': 'doctor',
            'text': (
                "⚠️ It seems the home remedies haven't provided enough relief.\n\n"
                "This could mean your condition needs professional medical attention.\n\n"
                "🏥 Please consult a doctor, especially if:\n"
                "  • Symptoms last more than 3 days\n"
                "  • Pain is severe or worsening\n"
                "  • You have fever above 101°F / 38.3°C\n"
                "  • You have difficulty breathing\n\n"
                "Click below to check your symptoms and find the right specialist."
            )
        })

    # ── 2. Extract meaningful keywords (remove stop words) ───────────────────
    STOP_WORDS = {
        'i','me','my','have','has','am','is','are','a','an','the','and','or',
        'but','in','on','at','to','for','of','with','this','that','it','be',
        'do','did','does','been','was','were','will','would','can','could',
        'should','get','got','feel','feeling','experiencing','suffering','from',
        'please','help','suggest','tell','give','what','how','why','when',
        'some','little','very','quite','bit','pain','ache'  # 'pain'/'ache' kept as partial
    }
    # Also keep multi-word combos before splitting
    MULTI_WORD_SYMPTOMS = [
        'chest pain', 'stomach pain', 'back pain', 'joint pain', 'muscle pain',
        'sore throat', 'runny nose', 'skin rash', 'high fever', 'low fever',
        'body ache', 'breathing issue', 'shortness of breath', 'ear pain',
        'eye pain', 'leg pain', 'knee pain', 'abdominal pain', 'neck pain'
    ]

    keywords = []
    # Check multi-word first
    for mw in MULTI_WORD_SYMPTOMS:
        if mw in message:
            keywords.append(mw)

    # Then single words
    for word in message.split():
        word = word.strip('.,!?;:')
        if len(word) >= 4 and word not in STOP_WORDS and word not in keywords:
            keywords.append(word)

    # ── 3. Check built-in REMEDIES_DB (fast, no DB needed) ──────────────────
    from logic.remedies_engine import REMEDIES_DB
    matched_builtin = []
    for kw in keywords:
        for condition_key, remedy_data in REMEDIES_DB.items():
            if kw in condition_key or condition_key in kw:
                if condition_key not in [m['condition'] for m in matched_builtin]:
                    matched_builtin.append({'condition': condition_key, 'data': remedy_data})

    builtin_parts = []
    for m in matched_builtin[:2]:
        d    = m['data']
        cond = m['condition'].title()
        tips = '\n  • '.join(d.get('tips', []))
        dos  = '\n  • '.join(d.get('dos', []))
        donts= '\n  • '.join(d.get('donts', []))
        warn = '\n  ⚠️ '.join(d.get('warnings', []))
        builtin_parts.append(
            f"🌿 {cond}\n\n"
            f"💊 Remedies:\n  • {tips}\n\n"
            f"✅ DOs:\n  • {dos}\n\n"
            f"❌ DON'Ts:\n  • {donts}\n\n"
            + (f"⚠️ Warning: {warn}" if warn else "")
        )

    # ── 4. Search MySQL remedies table by individual keywords ─────────────────
    db_parts = []
    if keywords:
        try:
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            # Build OR clause for each keyword
            clauses = []
            params  = []
            for kw in keywords[:5]:   # max 5 keywords
                like = f"%{kw}%"
                clauses.append("(LOWER(condition_name) LIKE %s OR LOWER(remedy_text) LIKE %s)")
                params.extend([like, like])
            sql = f"""
                SELECT DISTINCT condition_name, remedy_text, dos, donts
                FROM remedies
                WHERE {' OR '.join(clauses)}
                LIMIT 3
            """
            cur.execute(sql, params)
            rows = cur.fetchall()
            cur.close()
            for r in rows:
                dos   = (r.get('dos')   or '').replace('|', '\n  • ')
                donts = (r.get('donts') or '').replace('|', '\n  • ')
                db_parts.append(
                    f"🌿 {r['condition_name']}\n\n"
                    f"{r['remedy_text']}\n\n"
                    f"✅ DOs:\n  • {dos}\n\n"
                    f"❌ DON'Ts:\n  • {donts}"
                )
        except Exception:
            pass

    # ── 5. Combine results ────────────────────────────────────────────────────
    all_parts = builtin_parts + db_parts
    if all_parts:
        reply = "\n\n─────────────────\n\n".join(all_parts)
        reply += "\n\n💬 If these remedies don't help within 2–3 days, type \"not improving\" and I'll help you find a doctor."
        return jsonify({'type': 'remedy', 'text': reply})

    # ── 6. No match at all → general wellness tips ───────────────────────────
    return jsonify({
        'type': 'remedy',
        'text': (
            f"I couldn't find a specific remedy for \"{raw_message}\".\n\n"
            "Here are some general wellness tips that help most conditions:\n\n"
            "💧 Stay hydrated — drink 8+ glasses of water daily\n"
            "😴 Rest well — your body heals during sleep\n"
            "🍲 Eat light, warm foods like soups and broths\n"
            "🚫 Avoid cold drinks, junk food and stress\n"
            "♨️ Steam inhalation helps with congestion & throat issues\n"
            "🧘 Light stretching or yoga can ease body aches\n\n"
            "💬 Try typing a specific symptom like: fever, headache, cough, chest pain, cold, etc.\n"
            "Or type \"not improving\" if you need to see a doctor."
        )
    })

@app.route("/login", methods=["POST", "GET"])
def login():
    # Only skip login form if session is genuinely active (user was already logged in)
    # Do NOT skip if arriving from register (registered_id present in URL)
    registered_id_arg = request.args.get('registered_id')
    if 's_mail' in session and not registered_id_arg:
        return redirect(url_for('dashboard'))
    # If arriving from registration, clear old session so form shows
    if registered_id_arg:
        session.clear()

    registered_id = request.args.get('registered_id')
    success_msg = None
    if registered_id:
        success_msg = f"Registration successful! Your Patient ID is #{registered_id}. Please log in below."

    if request.method == 'POST' and ('mail' in request.form or 'login_input' in request.form) and 'pwd' in request.form:
        login_input = request.form.get('login_input') or request.form.get('mail')
        pwd = request.form['pwd']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Check if the user entered a Patient ID (integer) or Email Address
        if login_input.isdigit():
            cursor.execute('select * from patient where id = %s', [int(login_input)])
        else:
            cursor.execute('select * from patient where mail = %s', [login_input])
            
        account = cursor.fetchone()
        
        # Verify password — handle both hashed and legacy plain-text passwords safely
        password_ok = False
        if account:
            try:
                password_ok = verify_password(account['pwd'], pwd)
            except Exception:
                # Fallback for old plain-text passwords not yet migrated
                password_ok = (account['pwd'] == pwd)
        if account and password_ok:
            session['loggedin'] = True
            session['s_mail'] = account['mail']
            session['s_name'] = account['name']
            
            # Set returning_user cookie on successful login
            response = make_response(redirect(url_for('dashboard')))
            response.set_cookie('returning_user', 'true', max_age=60*60*24*365) # 1 year
            return response
        else:
            return render_template('login.html', msg='Incorrect username/password', success_msg=success_msg)
    return render_template('login.html', success_msg=success_msg)

@app.route("/register", methods=["POST", "GET"])
def register():
    # Always clear session when on register page so login page shows form fresh
    session.clear()
    if request.method == 'POST' and 'name' in request.form and 'pwd' in request.form:
        name = request.form['name']
        mail = request.form['mail']
        phone = request.form.get('phone', '')
        age = request.form.get('age', None)
        gender = request.form.get('gender', '')
        pwd = hash_password(request.form['pwd']) # Secure hashing
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        try:
            cursor.execute('insert into patient (name,mail,pwd,phone_number,age,gender) values(%s,%s,%s,%s,%s,%s)', (name, mail, pwd, phone, age, gender))
            mysql.connection.commit()
            
            # Get the auto-incremented Patient ID
            patient_id = cursor.lastrowid
            
            # Clear any lingering session, then redirect to login with the new Patient ID
            session.clear()
            response = make_response(redirect(url_for('login', registered_id=patient_id)))
            # Do NOT set returning_user cookie here – it will be set after a successful login
            return response
        except Exception as e:
            return render_template('register.html', msg='Error: ' + str(e))
    return render_template('register.html')

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/home")
def home():
    if 's_mail' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/symptoms')
def symptoms():
    if 's_mail' in session:
        mail = session.get('s_mail')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('select * from patient where mail=%s', [mail])
        account = cursor.fetchone()
        return render_template('symptoms.html', patient=account)
    return redirect(url_for('login'))

@app.route("/dashboard")
def dashboard():
    if 's_mail' in session:
        mail = session.get('s_mail')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        cursor.execute('select * from patient where mail= %s', [mail])
        account = cursor.fetchone()
        
        analysis = session.get('last_analysis')
        
        # Smart Doctor Recommendations
        cursor.execute('select * from doctor')
        all_doctors = cursor.fetchall()
        recommended, others = get_recommendations(all_doctors, analysis, account.get('location'))
        
        # Fetch Consultations
        cursor.execute("""
            SELECT DISTINCT d.name, d.dept, d.link, c.status, c.timing
            FROM doctor d
            INNER JOIN consult c ON d.id = c.doctor_id
            WHERE c.patient_mail = %s
        """, [mail])
        status = cursor.fetchall()
        
        # Fetch History
        cursor.execute("SELECT * FROM history WHERE patient_mail = %s ORDER BY analysis_date DESC LIMIT 5", [mail])
        history = cursor.fetchall()
        
        # Fetch Queries
        cursor.execute('select * from queries')
        queries = cursor.fetchall()
        
        # Fetch Reports (uploaded by patient)
        cursor.execute('select * from reports where patient_mail= %s', [mail])
        reports = cursor.fetchall()

        # Fetch Doctor Prescriptions / Reports (uploaded by doctor for this patient)
        cursor.execute("""
            SELECT rx.filename, rx.description, rx.appointment_id,
                   a.appointment_date, a.appointment_time,
                   d.name AS doctor_name, d.dept
            FROM doctor_prescriptions rx
            JOIN appointments a ON a.id = rx.appointment_id
            JOIN doctor d ON d.id = rx.doctor_id
            WHERE rx.patient_mail = %s
            ORDER BY a.appointment_date DESC
        """, [mail])
        doctor_reports = cursor.fetchall()

        # Fetch Remedies
        cursor.execute('select * from remedies')
        remedies = cursor.fetchall()

        # Fetch Patient's Booked Appointments (joined with doctor info)
        cursor.execute("""
            SELECT a.id, a.appointment_date, a.appointment_time, a.status,
                   d.name AS doctor_name, d.dept, d.hospital_name
            FROM appointments a
            JOIN doctor d ON d.id = a.doctor_id
            WHERE a.patient_mail = %s
            ORDER BY a.appointment_date DESC, a.appointment_time ASC
            LIMIT 10
        """, [mail])
        appointments = cursor.fetchall()

        return render_template('index.html',
                               doctor=recommended + list(others),
                               patient=account,
                               status=status,
                               queries=queries,
                               analysis=analysis,
                               history=history,
                               reports=reports,
                               doctor_reports=doctor_reports,
                               remedies=remedies,
                               appointments=appointments)
    return redirect(url_for('login'))

@app.route('/upload_report', methods=['POST'])
def upload_report():
    if 's_mail' not in session:
        return redirect(url_for('login'))

    if 'report_file' not in request.files:
        return redirect(url_for('dashboard'))

    file = request.files['report_file']
    if file.filename == '':
        return redirect(url_for('dashboard'))

    if file and allowed_file(file.filename):
        report_name = request.form.get('report_name', '').strip()
        original    = secure_filename(file.filename)
        timestamp   = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

        # Use custom label if provided, else just timestamp + original name
        if report_name:
            safe_label = secure_filename(report_name.replace(' ', '_'))
            filename   = f"{timestamp}_{safe_label}_{original}"
        else:
            filename   = f"{timestamp}_{original}"

        # Ensure upload folder exists
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Save to DB
        mail   = session.get('s_mail')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('insert into reports (patient_mail, filename) values (%s, %s)', (mail, filename))
        mysql.connection.commit()

    return redirect(url_for('dashboard'))

@app.route('/view_report/<filename>')
def view_report(filename):
    if 's_mail' in session:
        # Use absolute path to backend/uploads/
        upload_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', filename)
        return send_file(upload_path)
    return redirect(url_for('login'))

@app.route("/analyze", methods=["POST"])
def analyze():
    if 's_mail' in session:
        user_input = request.form.get('usrquestion')
        analysis_result = analyze_symptoms(user_input)
        session['last_analysis'] = analysis_result
        
        mail = session.get('s_mail')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Save to history
        if analysis_result['status'] == 'success':
            cursor.execute('INSERT INTO history (patient_mail, symptoms, condition_name, severity) VALUES (%s, %s, %s, %s)', 
                           (mail, ", ".join(analysis_result['symptoms']), analysis_result['condition'], analysis_result['severity']))
            mysql.connection.commit()
            
        return redirect('/dashboard?tab=ai-checker')
    return redirect(url_for('login'))

@app.route("/api/chat", methods=["POST"])
def chat():
    if 's_mail' in session:
        user_msg = request.json.get('message')
        context = session.get('last_analysis')
        chat_state = session.get('chat_state', None)
        
        from logic.chatbot_engine import get_chatbot_response
        response, new_state = get_chatbot_response(user_msg, context, chat_state)
        session['chat_state'] = new_state
        return jsonify({'response': response})
    return jsonify({'error': 'Unauthorized'}), 401


@app.route("/api/symptom_flow", methods=["POST"])
def symptom_flow():
    """Step-based conversational symptom checker API."""
    if 's_mail' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data      = request.json or {}
    step      = data.get('step', 0)
    message   = (data.get('message') or '').strip()
    collected = data.get('collected', {})

    if step == 0:
        collected['symptoms'] = message
        return jsonify({
            'step': 1, 'type': 'question',
            'text': 'How long have you been experiencing these symptoms?',
            'options': ['Just today', '2–3 days', 'About a week', 'More than a week'],
            'collected': collected
        })

    elif step == 1:
        collected['duration'] = message
        return jsonify({
            'step': 2, 'type': 'question',
            'text': 'How severe would you rate your symptoms?',
            'options': ['Mild — I can manage', 'Moderate — affecting daily life', 'Severe — need urgent help'],
            'collected': collected
        })

    elif step == 2:
        collected['severity_input'] = message
        return jsonify({
            'step': 3, 'type': 'question',
            'text': 'Any additional symptoms or relevant medical history? (fever, allergies, chronic conditions…)',
            'options': ['No additional symptoms', 'I also have fever', 'I have allergies', 'I have a chronic condition'],
            'collected': collected
        })

    elif step == 3:
        collected['additional'] = message
        # Build combined symptom text
        extra = collected.get('additional', '')
        full_text = collected.get('symptoms', '')
        if extra and extra.lower() not in ('no additional symptoms', 'none', ''):
            full_text += ' ' + extra

        # ML Analysis
        analysis = analyze_symptoms(full_text)
        session['last_analysis'] = analysis

        # Save to history
        mail = session.get('s_mail')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if analysis.get('status') == 'success':
            try:
                cursor.execute(
                    'INSERT INTO history (patient_mail, symptoms, condition_name, severity) VALUES (%s,%s,%s,%s)',
                    (mail, ', '.join(analysis.get('symptoms', [])),
                     analysis.get('condition', ''), analysis.get('severity', ''))
                )
                mysql.connection.commit()
            except Exception:
                pass

        # Doctor recommendations
        cursor.execute('SELECT * FROM doctor')
        all_doctors = cursor.fetchall()
        cursor.execute('SELECT * FROM patient WHERE mail = %s', [mail])
        account = cursor.fetchone()
        recommended, others = get_recommendations(
            all_doctors, analysis, account.get('location') if account else None
        )
        doctors_list = (recommended + list(others))[:6]

        def fmt(d):
            return {
                'id':            d['id'],
                'name':          d['name'],
                'dept':          d['dept'],
                'hospital_name': d.get('hospital_name') or '',
                'rating':        str(d.get('rating') or '4.5'),
                'availability':  d.get('availability') or 'Available Today',
            }

        return jsonify({
            'step':      4,
            'type':      'result',
            'condition': analysis.get('condition', 'Unidentified Condition'),
            'severity':  analysis.get('severity', 'Low'),
            'specialty': analysis.get('specialty', 'General Physician'),
            'remedies':  analysis.get('remedies', []),
            'warnings':  analysis.get('warnings', []),
            'doctors':   [fmt(d) for d in doctors_list],
            'collected': collected
        })

    return jsonify({'error': 'Invalid step'}), 400

@app.route("/api/voice_to_text", methods=["POST"])
def voice_to_text():
    if 's_mail' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    if 'audio_data' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
        
    audio_file = request.files['audio_data']
    
    recognizer = sr.Recognizer()
    try:
        # Read the audio data
        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)
            return jsonify({'transcript': text, 'status': 'success'})
    except sr.UnknownValueError:
        return jsonify({'error': 'Could not understand audio', 'status': 'error'}), 400
    except sr.RequestError as e:
        return jsonify({'error': f'Speech recognition error: {e}', 'status': 'error'}), 500
    except Exception as e:
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route("/download_report")
def download_report():
    if 's_mail' in session and 'last_analysis' in session:
        analysis = session.get('last_analysis')
        patient_name = session.get('s_name')
        # Save to a known absolute path inside backend/
        safe_mail = session.get('s_mail', 'user').replace('@', '_').replace('.', '_')
        report_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"report_{safe_mail}.pdf")
        generate_pdf_report(patient_name, analysis, report_file)
        return send_file(report_file, as_attachment=True, download_name='HealthReport.pdf')
    return redirect(url_for('login'))

@app.route('/api/get_slots', methods=['GET'])
def get_slots():
    """Returns available (not booked) time slots for a doctor on a given date."""
    if 's_mail' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    doctor_id = request.args.get('doctor_id')
    slot_date  = request.args.get('date')

    if not doctor_id or not slot_date:
        return jsonify({'error': 'Missing doctor_id or date parameter'}), 400

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT id, slot_time
        FROM   doctor_slots
        WHERE  doctor_id = %s
          AND  slot_date  = %s
          AND  is_booked  = FALSE
        ORDER BY slot_time
    """, (doctor_id, slot_date))
    rows = cursor.fetchall()

    slots = [{'id': r['id'], 'time': r['slot_time']} for r in rows]
    return jsonify({'slots': slots})

@app.route('/api/booked_slots', methods=['GET'])
def booked_slots():
    """Returns already-booked appointment_time values for a doctor on a given date."""
    if 's_mail' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    doctor_id  = request.args.get('doctor_id')
    appt_date  = request.args.get('date')
    if not doctor_id or not appt_date:
        return jsonify({'error': 'Missing params'}), 400
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "SELECT appointment_time FROM appointments WHERE doctor_id=%s AND appointment_date=%s",
        (doctor_id, appt_date)
    )
    booked = [r['appointment_time'] for r in cursor.fetchall()]
    return jsonify({'booked': booked})

@app.route("/book_appointment", methods=["POST"])
def book_appointment():
    if 's_mail' in session:
        doctor_id = request.form.get('doctor_id')
        date      = request.form.get('date')
        time      = request.form.get('time')
        mail      = session.get('s_mail')

        if not doctor_id or not date or not time:
            return redirect(url_for('dashboard'))

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # --- Check for duplicate booking (same doctor, date, time) ---
        cursor.execute(
            'SELECT id FROM appointments WHERE doctor_id=%s AND appointment_date=%s AND appointment_time=%s',
            (doctor_id, date, time)
        )
        if cursor.fetchone():
            return (
                "<div style='font-family:sans-serif; padding:3rem; text-align:center;'>"
                "<h3 style='color:#ef4444;'>⚠️ Slot Already Booked</h3>"
                "<p>This time slot is already taken. Please go back and choose a different time.</p>"
                "<a href='/dashboard' style='display:inline-block;margin-top:1rem;padding:0.6rem 1.5rem;"
                "background:#3b82f6;color:white;border-radius:0.5rem;text-decoration:none;font-weight:600;'>← Go Back</a>"
                "</div>"
            )

        # --- Save the appointment ---
        cursor.execute(
            'INSERT INTO appointments (patient_mail, doctor_id, appointment_date, appointment_time) VALUES (%s, %s, %s, %s)',
            (mail, doctor_id, date, time)
        )
        appointment_id = cursor.lastrowid

        # --- Create payment record ---
        if appointment_id:
            try:
                cursor.execute(
                    'INSERT INTO payments (appointment_id, amount, payment_status) VALUES (%s, %s, %s)',
                    (appointment_id, 500.00, 'Completed')
                )
            except Exception:
                pass  # payments table may not exist in all environments

        mysql.connection.commit()

        # --- Send confirmation email to patient ---
        try:
            cursor.execute('SELECT name FROM patient WHERE mail = %s', [mail])
            patient_row = cursor.fetchone()
            cursor.execute('SELECT name, dept, hospital_name FROM doctor WHERE id = %s', [doctor_id])
            doctor_row = cursor.fetchone()

            if patient_row and doctor_row:
                patient_name = patient_row['name']
                doc_name     = doctor_row['name']
                doc_dept     = doctor_row['dept']
                hospital     = doctor_row.get('hospital_name') or 'the clinic'

                confirmation_html = f"""
                <div style="font-family:Inter,sans-serif;max-width:540px;margin:auto;
                            border-radius:12px;overflow:hidden;
                            box-shadow:0 4px 20px rgba(0,0,0,0.1);">
                  <div style="background:linear-gradient(135deg,#3b82f6,#1d4ed8);
                              padding:1.5rem 2rem;">
                    <h2 style="color:#fff;margin:0;font-size:1.3rem;">✅ Appointment Confirmed</h2>
                    <p style="color:rgba(255,255,255,0.8);margin:0.3rem 0 0;
                              font-size:0.85rem;">MedConsult Health Assistant</p>
                  </div>
                  <div style="padding:1.5rem 2rem;background:#f8fafc;">
                    <p style="color:#1e293b;font-size:0.95rem;">Hi <strong>{patient_name}</strong>,</p>
                    <p style="color:#475569;">Your appointment has been successfully booked. Here are your details:</p>
                    <div style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;
                                padding:1rem 1.25rem;margin:1rem 0;">
                      <p style="margin:0 0 0.4rem;color:#64748b;font-size:0.8rem;
                                text-transform:uppercase;letter-spacing:0.05em;">Booking Details</p>
                      <p style="margin:0.2rem 0;color:#1e293b;"><strong>Doctor:</strong> Dr. {doc_name} ({doc_dept})</p>
                      <p style="margin:0.2rem 0;color:#1e293b;"><strong>Hospital:</strong> {hospital}</p>
                      <p style="margin:0.2rem 0;color:#1e293b;"><strong>Date:</strong> {date}</p>
                      <p style="margin:0.2rem 0;color:#1e293b;"><strong>Time:</strong> {time}</p>
                      <p style="margin:0.2rem 0;color:#1e293b;"><strong>Booking ID:</strong> #{appointment_id}</p>
                    </div>
                    <p style="color:#475569;font-size:0.85rem;">
                      Please arrive 10 minutes early and carry a valid ID and any previous prescriptions.
                    </p>
                    <p style="color:#94a3b8;font-size:0.75rem;margin-top:1.5rem;">
                      © 2026 MedConsult AI — This is an automated confirmation. Do not reply.
                    </p>
                  </div>
                </div>"""

                send_reminder_email(
                    mail,
                    f'✅ Appointment Confirmed — Dr. {doc_name} on {date} at {time}',
                    confirmation_html
                )
        except Exception as e:
            print(f'[BOOKING] Confirmation email error: {e}')

        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route("/consult", methods=["POST", "GET"])
def consult():
    if 's_mail' in session:
        patient_mail = request.args.get('a')
        doctor_id = request.args.get('b')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('insert into consult (patient_mail,doctor_id, status) values (%s,%s, %s)', (patient_mail, doctor_id, 'Requested'))
        mysql.connection.commit()
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/askquery', methods=["POST", "GET"])
def askquery():
    if 's_mail' in session and request.method == 'POST':
        usrquestion = request.form['usrquestion']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('insert into queries (question, status) values(%s, %s)', [usrquestion, 'pending'])
        mysql.connection.commit()
        return redirect(url_for('features'))
    return redirect(url_for('login'))

@app.route("/update", methods=["POST", "GET"])
def update():
    if 's_mail' in session and request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        location = request.form['location']
        BMI = request.form['bmi']
        mail = session.get('s_mail')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('update patient set name = %s , age=%s, gender= %s , location=%s , BMI=%s where mail =%s', (name, age, gender, location, BMI, mail))
        mysql.connection.commit()
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/logout_user')
def logout_user():
    session.clear()
    return redirect(url_for('login'))

@app.route('/doctorLogout')
def doctorLogout():
    """Doctor logout — clears session and redirects to doctor login page."""
    session.clear()
    return redirect(url_for('doctorLogin'))

@app.route('/answerquery', methods=['POST'])
def answerquery():
    """Allows a doctor to submit an answer to a patient query."""
    if 'd_id' not in session:
        return redirect(url_for('doctorLogin'))
    query_id = request.form.get('query_id') or request.form.get('sno')
    answer = request.form.get('answer', '').strip()
    if query_id and answer:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            "UPDATE queries SET answer = %s, status = 'answered' WHERE id = %s",
            (answer, query_id)
        )
        mysql.connection.commit()
    return redirect(url_for('docpage'))

@app.route('/doctor', methods=["POST", "GET"])
def doctorLogin():
    if request.method == 'POST' and 'mail' in request.form:
        mail = request.form['mail']
        pwd = request.form['pwd']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('select * from doctor where mail= %s', [mail])
        doctor = cursor.fetchone()
        
        if doctor and (doctor['pwd'] == pwd or verify_password(doctor['pwd'], pwd)):
            session['loggedin'] = True
            session['d_id'] = doctor['id']
            return redirect(url_for('docpage'))
        else:
            return render_template('doctor_login.html', msg='Invalid Credentials')
    return render_template('doctor_login.html', msg='')

@app.route('/doctor_register', methods=["POST", "GET"])
def doctor_register():
    # static list of doctor specialties for the dropdown
    specializations = [
        "Cardiologist",
        "Dermatologist",
        "General Practitioner",
        "Neurologist",
        "Pediatrician",
        "Psychiatrist",
        "Radiologist",
        "Surgeon",
    ]

    # create a DB cursor (used for both POST and GET)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == "POST" and "name" in request.form:
        name = request.form["name"]
        mail = request.form["mail"]
        dept = request.form["dept"]
        hospital = request.form["hospital_name"]
        exp = request.form["experience"]
        contact = request.form["contact"]
        pwd = hash_password(request.form["pwd"])
        try:
            # Resolve hospital name to its ID (doctor table stores both hospital_id and hospital_name)
            cursor_hosp = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor_hosp.execute('SELECT id, name FROM hospitals WHERE name = %s', (hospital,))
            hosp_row = cursor_hosp.fetchone()
            if not hosp_row:
                raise Exception(f"Hospital '{hospital}' not found in database.")
            hospital_id   = hosp_row['id']
            hospital_name = hosp_row['name']   # store the text name too

            cursor.execute(
                "INSERT INTO doctor (name, mail, pwd, dept, hospital_id, hospital_name, experience, contact) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (name, mail, pwd, dept, hospital_id, hospital_name, exp, contact),
            )
            mysql.connection.commit()
            return redirect(url_for("doctorLogin"))
        except Exception as e:
            # On error, re‑fetch hospital list so the form can be re‑rendered
            cursor_hosp = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor_hosp.execute("SELECT name FROM hospitals")
            hospitals = [row["name"] for row in cursor_hosp.fetchall()]
            return render_template(
                "doctor_register.html",
                specializations=specializations,
                hospitals=hospitals,
                msg="Error: " + str(e),
            )

    # GET request – render the registration form with current hospitals
    cursor_hosp = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor_hosp.execute("SELECT name FROM hospitals")
    hospitals = [row["name"] for row in cursor_hosp.fetchall()]
    return render_template(
        "doctor_register.html",
        specializations=specializations,
        hospitals=hospitals,
    )


@app.route('/docpage/')
def docpage():
    if 'd_id' in session:
        doc_id = session.get('d_id')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM doctor WHERE id = %s', [doc_id])
        doctor = cursor.fetchone()

        # Fetch appointments WITH patient details AND latest symptom analysis
        try:
            cursor.execute("""
                SELECT
                    p.name, p.age, p.gender, p.phone_number,
                    a.patient_mail, a.appointment_date, a.appointment_time,
                    a.status, a.id,
                    COALESCE(a.patient_rating, NULL) AS patient_rating,
                    h.condition_name, h.severity, h.symptoms
                FROM appointments a
                JOIN patient p ON p.mail = a.patient_mail
                LEFT JOIN history h ON h.id = (
                    SELECT MAX(id) FROM history WHERE patient_mail = a.patient_mail
                )
                WHERE a.doctor_id = %s
                ORDER BY a.appointment_date DESC, a.appointment_time
            """, [doc_id])
        except Exception:
            # Fallback if patient_rating column doesn't exist yet
            cursor.execute("""
                SELECT
                    p.name, p.age, p.gender, p.phone_number,
                    a.patient_mail, a.appointment_date, a.appointment_time,
                    a.status, a.id, NULL AS patient_rating,
                    h.condition_name, h.severity, h.symptoms
                FROM appointments a
                JOIN patient p ON p.mail = a.patient_mail
                LEFT JOIN history h ON h.id = (
                    SELECT MAX(id) FROM history WHERE patient_mail = a.patient_mail
                )
                WHERE a.doctor_id = %s
                ORDER BY a.appointment_date DESC, a.appointment_time
            """, [doc_id])
        appointments = cursor.fetchall()

        # Fetch prescriptions uploaded by this doctor, keyed by appointment_id
        cursor.execute('SELECT * FROM doctor_prescriptions WHERE doctor_id = %s', [doc_id])
        rx_rows = cursor.fetchall()
        prescriptions = {r['appointment_id']: r for r in rx_rows}

        cursor.execute('SELECT * FROM queries')
        queries = cursor.fetchall()

        return render_template('doctor_main_page.html',
                               appointments=appointments,
                               doctor=doctor,
                               queries=queries,
                               prescriptions=prescriptions)
    return redirect(url_for('doctorLogin'))


@app.route('/accept_appointment/<int:appt_id>', methods=['POST'])
def accept_appointment(appt_id):
    """Doctor accepts a pending appointment."""
    if 'd_id' not in session:
        return redirect(url_for('doctorLogin'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "UPDATE appointments SET status = 'Accepted' WHERE id = %s AND doctor_id = %s",
        (appt_id, session['d_id'])
    )
    mysql.connection.commit()
    return redirect(url_for('docpage'))


@app.route('/decline_appointment/<int:appt_id>', methods=['POST'])
def decline_appointment(appt_id):
    """Doctor declines an appointment."""
    if 'd_id' not in session:
        return redirect(url_for('doctorLogin'))
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        "UPDATE appointments SET status = 'Declined' WHERE id = %s AND doctor_id = %s",
        (appt_id, session['d_id'])
    )
    mysql.connection.commit()
    return redirect(url_for('docpage'))


@app.route('/upload_prescription', methods=['POST'])
def upload_prescription():
    """Doctor uploads a report/prescription file for a patient."""
    if 'd_id' not in session:
        return redirect(url_for('doctorLogin'))

    appt_id     = request.form.get('appointment_id')
    patient_mail = request.form.get('patient_mail')
    description  = request.form.get('description', '').strip()
    file         = request.files.get('prescription_file')

    if file and file.filename and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filename = f"rx_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        upload_path = app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        file.save(os.path.join(upload_path, filename))

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # Upsert: replace if already uploaded for this appointment
        cursor.execute(
            """INSERT INTO doctor_prescriptions
               (appointment_id, doctor_id, patient_mail, filename, description)
               VALUES (%s, %s, %s, %s, %s)
               ON DUPLICATE KEY UPDATE filename=VALUES(filename), description=VALUES(description)""",
            (appt_id, session['d_id'], patient_mail, filename, description)
        )
        mysql.connection.commit()

    return redirect(url_for('docpage'))


@app.route('/rate_doctor', methods=['POST'])
def rate_doctor():
    """Patient submits a star rating for a completed appointment."""
    if 's_mail' not in session:
        return redirect(url_for('login'))

    appt_id   = request.form.get('appointment_id')
    doctor_id = request.form.get('doctor_id')
    rating    = request.form.get('rating')
    mail      = session.get('s_mail')

    try:
        rating_val = float(rating)
        if not (1 <= rating_val <= 5):
            raise ValueError
    except (TypeError, ValueError):
        return redirect(url_for('dashboard'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Save rating on the appointment row
    cursor.execute(
        'UPDATE appointments SET patient_rating = %s WHERE id = %s AND patient_mail = %s',
        (rating_val, appt_id, mail)
    )

    # Recalculate and update doctor's average rating
    cursor.execute(
        'SELECT AVG(patient_rating) AS avg_r FROM appointments WHERE doctor_id = %s AND patient_rating IS NOT NULL',
        [doctor_id]
    )
    result = cursor.fetchone()
    if result and result['avg_r']:
        new_avg = round(float(result['avg_r']), 1)
        cursor.execute('UPDATE doctor SET rating = %s WHERE id = %s', (new_avg, doctor_id))

    mysql.connection.commit()
    return redirect(url_for('dashboard'))



@app.route('/chatbot')
def chatbot():
    if 's_mail' in session:
        return render_template('chatbot.html')
    return redirect(url_for('login'))

@app.route('/remedies')
def remedies():
    if 's_mail' in session:
        analysis = session.get('last_analysis')
        symptoms = analysis['symptoms'] if analysis else []
        intelligent_remedies = get_intelligent_remedies(symptoms)
        return render_template('remedies.html', remedies=intelligent_remedies)
    return redirect(url_for('login'))

@app.route('/features')
def features():
    if 's_mail' in session:
        mail = session.get('s_mail')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('select * from patient where mail=%s', [mail])
        account = cursor.fetchone()

        # Legacy consult-table appointments
        cursor.execute("""
            SELECT DISTINCT d.name, d.dept, d.link, c.status, c.timing
            FROM doctor d
            INNER JOIN consult c ON d.id = c.doctor_id
            WHERE c.patient_mail = %s
        """, [mail])
        status = cursor.fetchall()

        # New appointments table — with doctor info, rating status, and prescription
        cursor.execute("""
            SELECT
                a.id, a.appointment_date, a.appointment_time, a.status, a.patient_rating,
                a.doctor_id,
                d.name AS doctor_name, d.dept, d.hospital_name, d.rating AS doctor_rating,
                rx.filename AS rx_file, rx.description AS rx_desc
            FROM appointments a
            JOIN doctor d ON d.id = a.doctor_id
            LEFT JOIN doctor_prescriptions rx ON rx.appointment_id = a.id
            WHERE a.patient_mail = %s
            ORDER BY a.appointment_date DESC, a.appointment_time
        """, [mail])
        appointments = cursor.fetchall()

        # Fetch Queries
        cursor.execute('select * from queries')
        queries = cursor.fetchall()

        return render_template('features.html',
                               patient=account,
                               status=status,
                               appointments=appointments,
                               queries=queries)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
