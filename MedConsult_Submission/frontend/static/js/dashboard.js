/**
 * Dashboard Features System
 * Tab Navigation · Calendly-style Booking (1-hour slots + 30-min gap) · PDF Download
 */

// ─── 1. Tab Navigation ───────────────────────────────────────────────────────
function switchTab(tab) {
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    const content = document.getElementById('content-' + tab);
    const btn     = document.getElementById('tab-' + tab);
    if (content) content.classList.add('active');
    if (btn)     btn.classList.add('active');
}

// ─── 2. Chatbot ──────────────────────────────────────────────────────────────
async function sendChatMessage() {
    const input    = document.getElementById('chat-input');
    const chatMsgs = document.getElementById('chat-messages');
    if (!input || !chatMsgs) return;
    const message = input.value.trim();
    if (!message) return;
    chatMsgs.innerHTML += `<div class="msg user">${message}</div>`;
    input.value = '';
    chatMsgs.scrollTop = chatMsgs.scrollHeight;
    try {
        const res  = await fetch('/api/chat', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({message}) });
        const data = await res.json();
        chatMsgs.innerHTML += `<div class="msg bot">${data.response}</div>`;
        chatMsgs.scrollTop = chatMsgs.scrollHeight;
    } catch(e) {
        chatMsgs.innerHTML += `<div class="msg bot">Sorry, I'm having trouble connecting right now.</div>`;
    }
}
function sendQuickChat(t) { const i = document.getElementById('chat-input'); if(i){i.value=t;sendChatMessage();} }

// ─── 3. Calendly-Style Booking Modal ─────────────────────────────────────────
// Slots: 1-hour appointment + 30-min gap between each
// Format: { start: "9:00 AM", end: "10:00 AM", label: "9:00 AM – 10:00 AM" }
const BM_SLOTS = [
    { start: '9:00 AM',  end: '10:00 AM' },
    { start: '10:30 AM', end: '11:30 AM' },
    { start: '12:00 PM', end: '1:00 PM'  },
    { start: '1:30 PM',  end: '2:30 PM'  },
    { start: '3:00 PM',  end: '4:00 PM'  },
    { start: '4:30 PM',  end: '5:30 PM'  },
    { start: '6:00 PM',  end: '7:00 PM'  },
];

const BM_MONTHS = ['January','February','March','April','May','June',
                   'July','August','September','October','November','December'];
const BM_DAYS   = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];

let bmYear = 0, bmMonth = 0, bmSelDate = null, bmSelTime = null, bmDocId = '';
let bmBookedTimes = []; // start-times already booked on the selected date

function openBookingModal(name, id, hospital) {
    bmDocId      = id;
    bmSelDate    = null;
    bmSelTime    = null;
    bmBookedTimes = [];

    // Left panel
    document.getElementById('bm-doc-name').textContent = 'Dr. ' + name;
    document.getElementById('bm-avatar').textContent   = name[0].toUpperCase();
    document.getElementById('bm-dept').textContent     = '';
    const hospTag = document.getElementById('bm-hospital-tag');
    const hospTxt = document.getElementById('bm-hosp-txt');
    if (hospital && hospital.trim()) {
        hospTxt.textContent   = hospital;
        hospTag.style.display = 'flex';
    } else {
        hospTag.style.display = 'none';
    }

    // Init calendar
    const now = new Date();
    bmYear  = now.getFullYear();
    bmMonth = now.getMonth();
    bmRenderCal();

    document.getElementById('bm-panel-cal').style.display     = 'block';
    document.getElementById('bm-panel-right').style.display   = 'none';
    document.getElementById('bm-panel-confirm').style.display = 'none';
    document.getElementById('booking-modal').style.display    = 'flex';
}

function bmRenderCal() {
    document.getElementById('bm-month-label').textContent = BM_MONTHS[bmMonth] + ' ' + bmYear;
    const grid = document.getElementById('bm-cal-grid');
    grid.innerHTML = '';
    const today       = new Date(); today.setHours(0,0,0,0);
    const firstDay    = new Date(bmYear, bmMonth, 1).getDay();
    const daysInMonth = new Date(bmYear, bmMonth + 1, 0).getDate();

    for (let i = 0; i < firstDay; i++) grid.appendChild(document.createElement('span'));

    for (let d = 1; d <= daysInMonth; d++) {
        const btn = document.createElement('button');
        btn.type  = 'button';
        btn.className = 'bm-cal-day';
        btn.textContent = d;
        const thisDate = new Date(bmYear, bmMonth, d);
        if (thisDate < today) {
            btn.disabled = true;
        } else {
            const iso = `${bmYear}-${String(bmMonth+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
            if (bmSelDate === iso) btn.classList.add('selected');
            btn.onclick = () => bmSelectDate(iso, d);
        }
        grid.appendChild(btn);
    }
}

function bmPrevMonth() {
    if (bmMonth === 0) { bmMonth = 11; bmYear--; } else bmMonth--;
    const now = new Date();
    if (bmYear < now.getFullYear() || (bmYear === now.getFullYear() && bmMonth < now.getMonth())) {
        bmYear = now.getFullYear(); bmMonth = now.getMonth();
    }
    bmRenderCal();
}
function bmNextMonth() {
    if (bmMonth === 11) { bmMonth = 0; bmYear++; } else bmMonth++;
    bmRenderCal();
}

async function bmSelectDate(iso, day) {
    bmSelDate = iso;
    bmSelTime = null;
    bmRenderCal();

    // Show date label
    const d = new Date(bmYear, bmMonth, day);
    document.getElementById('bm-selected-date-label').textContent =
        BM_DAYS[d.getDay()] + ', ' + BM_MONTHS[bmMonth].slice(0,3) + ' ' + day;

    // Show loading in slot panel
    const slotDiv = document.getElementById('bm-slots');
    slotDiv.innerHTML = '<p style="font-size:0.78rem;color:#94a3b8;margin:0;">Loading slots…</p>';
    document.getElementById('bm-panel-right').style.display = 'block';

    // Fetch already-booked start times for this doctor+date
    try {
        const res  = await fetch(`/api/booked_slots?doctor_id=${bmDocId}&date=${iso}`);
        const data = await res.json();
        bmBookedTimes = data.booked || [];
    } catch(e) {
        bmBookedTimes = [];
    }

    bmRenderSlots(d, day);
}

function bmRenderSlots(dateObj, day) {
    const slotDiv = document.getElementById('bm-slots');
    slotDiv.innerHTML = '';

    BM_SLOTS.forEach(slot => {
        const isBooked = bmBookedTimes.includes(slot.start);

        const wrap = document.createElement('div');
        wrap.style.cssText = 'position:relative;';

        const b = document.createElement('button');
        b.type = 'button';

        if (isBooked) {
            // Booked — red-tinted, locked, not clickable
            b.className = 'bm-slot bm-slot-booked';
            b.style.cssText = `
                width:100%; text-align:left;
                background:#fff0f0; border-color:#fca5a5; color:#dc2626;
                cursor:not-allowed; opacity:0.85;
                display:flex; align-items:center; justify-content:space-between; gap:0.4rem;
            `;
            b.innerHTML = `
                <span>${slot.start} – ${slot.end}</span>
                <span style="font-size:0.9rem;">🔒</span>
            `;
            // Tooltip on click
            b.onclick = () => bmShowBookedToast(slot.start);
        } else {
            // Available
            b.className = 'bm-slot';
            b.style.cssText = 'width:100%; text-align:left; display:flex; align-items:center; justify-content:space-between;';
            b.innerHTML = `<span>${slot.start} – ${slot.end}</span><span style="font-size:0.75rem;color:#94a3b8;">1 hr</span>`;
            b.onclick = () => bmSelectTime(slot.start, slot.end, dateObj, day);
        }

        wrap.appendChild(b);
        slotDiv.appendChild(wrap);
    });

    // Show "Already Booked" toast element (hidden by default)
    if (!document.getElementById('bm-booked-toast')) {
        const toast = document.createElement('div');
        toast.id = 'bm-booked-toast';
        toast.style.cssText = `
            display:none; position:fixed; bottom:2rem; left:50%; transform:translateX(-50%);
            background:#dc2626; color:#fff; padding:0.6rem 1.4rem; border-radius:2rem;
            font-size:0.85rem; font-weight:700; font-family:'Inter',sans-serif;
            box-shadow:0 4px 16px rgba(220,38,38,0.4); z-index:99999;
            animation:bmToastIn 0.2s ease;
        `;
        toast.textContent = '🔒 This slot is already booked. Please choose another.';
        document.body.appendChild(toast);
    }
}

function bmShowBookedToast() {
    const toast = document.getElementById('bm-booked-toast');
    if (!toast) return;
    toast.style.display = 'block';
    clearTimeout(window._bmToastTimer);
    window._bmToastTimer = setTimeout(() => { toast.style.display = 'none'; }, 2800);
}

function bmSelectTime(startTime, endTime, dateObj, day) {
    bmSelTime = startTime;
    // Highlight selected
    document.querySelectorAll('.bm-slot:not(.bm-slot-booked)').forEach(b => {
        b.classList.toggle('selected', b.querySelector('span').textContent === startTime + ' – ' + endTime);
    });

    setTimeout(() => {
        const dayLabel = BM_DAYS[dateObj.getDay()] + ', ' + BM_MONTHS[bmMonth] + ' ' + day + ', ' + bmYear;
        document.getElementById('bm-confirm-date').textContent = dayLabel;
        document.getElementById('bm-confirm-time').textContent = startTime + ' – ' + endTime + '  (1 hour)';

        document.getElementById('modal-doc-id').value = bmDocId;
        document.getElementById('modal-date').value   = bmSelDate;
        document.getElementById('modal-time').value   = startTime;  // store start time in DB

        document.getElementById('bm-panel-cal').style.display     = 'none';
        document.getElementById('bm-panel-right').style.display   = 'none';
        document.getElementById('bm-panel-confirm').style.display = 'flex';
    }, 200);
}

function bmBackToCalendar() {
    bmSelTime = null;
    document.getElementById('bm-panel-cal').style.display     = 'block';
    document.getElementById('bm-panel-right').style.display   = bmSelDate ? 'block' : 'none';
    document.getElementById('bm-panel-confirm').style.display = 'none';
}

function closeModal() {
    document.getElementById('booking-modal').style.display = 'none';
}

document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('booking-modal');
    if (modal) modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });

    // Inject toast keyframe if not present
    if (!document.getElementById('bm-toast-style')) {
        const s = document.createElement('style');
        s.id = 'bm-toast-style';
        s.textContent = '@keyframes bmToastIn{from{opacity:0;transform:translateX(-50%) translateY(8px)}to{opacity:1;transform:translateX(-50%) translateY(0)}}';
        document.head.appendChild(s);
    }
});

// ─── 4. PDF Report Download ───────────────────────────────────────────────────
function downloadReport() { window.location.href = '/download_report'; }
