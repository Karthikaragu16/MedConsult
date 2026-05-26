/**
 * Symptoms Input System
 * Handles Text and Voice Input for the Health Assistant
 */

function addSymptom(symptom) {
    const input = document.getElementById('symptom-input');
    if (input.value && !input.value.endsWith(' ')) input.value += ', ';
    input.value += symptom;
    input.focus();
}

let mediaRecorder;
let audioChunks = [];

function startVoice() {
    const btn = document.getElementById('mic-btn');
    const status = document.getElementById('voice-status');
    const input = document.getElementById('symptom-input');

    if (mediaRecorder && mediaRecorder.state === "recording") {
        mediaRecorder.stop();
        if (btn) btn.classList.remove('listening');
        if (status) {
            status.innerText = "● Processing audio...";
        }
        return;
    }

    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];

            mediaRecorder.addEventListener("dataavailable", event => {
                audioChunks.push(event.data);
            });

            mediaRecorder.addEventListener("stop", () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                
                const formData = new FormData();
                formData.append('audio_data', audioBlob, 'symptom_audio.wav');
                
                fetch('/api/voice_to_text', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        if (input) {
                            if (input.value && !input.value.endsWith(' ')) input.value += ', ';
                            input.value += data.transcript;
                        }
                    } else {
                        alert("Error: " + data.error);
                    }
                    if (status) status.style.display = 'none';
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert("Error processing audio.");
                    if (status) status.style.display = 'none';
                });
                
                // Stop all tracks to release mic
                stream.getTracks().forEach(track => track.stop());
            });

            mediaRecorder.start();
            if (btn) btn.classList.add('listening');
            if (status) {
                status.innerText = "● Listening... (Click again to stop)";
                status.style.display = 'inline';
            }
        })
        .catch(error => {
            console.error('Mic access denied:', error);
            alert('Microphone access is required for voice input.');
        });
}

function showAnalyzing() {
    const overlay = document.getElementById('loading-overlay') || document.getElementById('loading-spinner');
    if (overlay) overlay.style.display = 'flex';
}
