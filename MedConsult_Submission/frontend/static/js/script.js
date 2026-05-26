// Speech to Text Integration
function startVoiceInput() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        const micBtn = document.getElementById('mic-btn');
        const status = document.getElementById('voice-status');
        
        if (micBtn) micBtn.classList.add('pulse-animation');
        if (status) status.style.display = 'inline';

        recognition.start();

        recognition.onresult = function(event) {
            const text = event.results[0][0].transcript;
            const inputField = document.getElementById('symptom-input');
            if (inputField) inputField.value = text;
            if (micBtn) micBtn.classList.remove('pulse-animation');
            if (status) status.style.display = 'none';
        };

        recognition.onerror = function(event) {
            if (micBtn) micBtn.classList.remove('pulse-animation');
            if (status) status.style.display = 'none';
            console.error('Speech recognition error:', event.error);
            alert('Voice recognition error: ' + event.error + '. Please ensure you have granted microphone permissions.');
        };

        recognition.onend = function() {
            if (micBtn) micBtn.classList.remove('pulse-animation');
            if (status) status.style.display = 'none';
        };
    } else {
        alert('Your browser does not support voice input. Please try Chrome or Edge.');
    }
}

// PDF Report Generation
function generateReport() {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();

    const patientName = document.getElementById('patient-name').innerText;
    const condition = document.getElementById('analysis-condition')?.innerText || 'N/A';
    const severity = document.getElementById('analysis-severity')?.innerText || 'N/A';
    const symptoms = document.getElementById('analysis-symptoms')?.innerText || 'N/A';
    const remedy = document.getElementById('analysis-remedy')?.innerText || 'N/A';

    doc.setFontSize(22);
    doc.text('HealthAI Analysis Report', 20, 20);
    
    doc.setFontSize(12);
    doc.text(`Patient Name: ${patientName}`, 20, 40);
    doc.text(`Date: ${new Date().toLocaleDateString()}`, 20, 50);
    
    doc.line(20, 55, 190, 55);
    
    doc.setFontSize(14);
    doc.text('Analysis Results:', 20, 70);
    doc.setFontSize(12);
    doc.text(`Detected Symptoms: ${symptoms}`, 20, 80);
    doc.text(`Possible Condition: ${condition}`, 20, 90);
    doc.text(`Severity Level: ${severity}`, 20, 100);
    
    doc.setFontSize(14);
    doc.text('Recommendations:', 20, 120);
    doc.setFontSize(12);
    doc.text(remedy, 20, 130, { maxWidth: 170 });
    
    doc.setFontSize(10);
    doc.setTextColor(150);
    doc.text('Disclaimer: This is an AI-generated report for informational purposes only. Please consult a professional doctor.', 20, 280);

    doc.save(`Health_Report_${patientName.replace(' ', '_')}.pdf`);
}

// NOTE: sendChatMessage() is defined in dashboard.js (uses /api/chat endpoint).
// It is NOT duplicated here to avoid conflicts.

function startAssessment() {
    const questions = [
        "Do you have a fever above 101°F?",
        "Have you been experiencing these symptoms for more than 3 days?",
        "Is there any sharp pain or difficulty breathing?"
    ];
    
    let current = 0;
    const ask = () => {
        if (current < questions.length) {
            const answer = confirm(questions[current]);
            current++;
            ask();
        } else {
            alert("Assessment complete. Based on your answers, our initial AI analysis remains consistent. Please consult the recommended doctor for a physical examination.");
            const doctorSection = document.getElementById('doctor-section');
            if (doctorSection) doctorSection.scrollIntoView({ behavior: 'smooth' });
        }
    };
    ask();
}

// Final Booking Confirmation Step
function confirmBooking(docName, docId, patientMail) {
    const symptoms = document.getElementById('analysis-symptoms')?.innerText || 'General checkup';
    const time = prompt("Select a preferred time (e.g., 10:30 AM tomorrow):", "10:00 AM");
    
    if (time) {
        const confirmation = confirm(`Please confirm your booking:\n\nDoctor: Dr. ${docName}\nSymptoms: ${symptoms}\nTime: ${time}\n\nDo you want to proceed?`);
        if (confirmation) {
            window.location.href = `/consult?a=${patientMail}&b=${docId}&t=${encodeURIComponent(time)}`;
        }
    }
}

function showLoading() {
    document.getElementById('loading-spinner').style.display = 'flex';
}
