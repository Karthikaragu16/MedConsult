// STEP 11: EMERGENCY & VOICE INPUT LOGIC
// Matches Feature 1 and Feature 7

function startVoiceInput() {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        document.getElementById('symptom-input').value = transcript;
    };
    recognition.start();
}

// Emergency Detection Logic (Client-side)
function checkEmergency(severity) {
    if (severity === 'High') {
        Swal.fire({
            title: '🚨 EMERGENCY ALERT',
            text: 'Severe symptoms detected. Consult a doctor IMMEDIATELY.',
            icon: 'error',
            confirmButtonText: 'View Emergency Contacts'
        });
    }
}
