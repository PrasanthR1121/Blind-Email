/* ── Stars ── */
const starsEl = document.getElementById('stars');
for (let i = 0; i < 120; i++) {
    const s = document.createElement('div');
    s.className = 'star';
    const size = Math.random() * 2.5 + 0.5;
    s.style.cssText = `width:${size}px;height:${size}px;top:${Math.random() * 100}%;left:${Math.random() * 100}%;--d:${(Math.random() * 4 + 2).toFixed(1)}s;--delay:${(Math.random() * 5).toFixed(1)}s;`;
    starsEl.appendChild(s);
}

/* ── Voice engine ── */
const micBtn = document.getElementById('micBtn');
const micIcon = document.getElementById('micIcon');
const statusEl = document.getElementById('voiceStatus');

let recognition = null;
let micOn = false;
let isSpeaking = false;
const VOICE = "UK English Female";

function speak(text, cb = null) {
    if (!window.responsiveVoice) return;
    responsiveVoice.cancel();
    isSpeaking = true;
    responsiveVoice.speak(text, VOICE, {
        rate: 0.9,
        onend: () => { isSpeaking = false; if (cb) cb(); }
    });
}

function handleCommand(raw) {
    const cmd = raw.toLowerCase().trim();
    statusEl.textContent = "You said: " + raw;

    if (isSpeaking) { responsiveVoice.cancel(); isSpeaking = false; }

    if (cmd.includes("login") || cmd.includes("sign in")) {
        speak("Opening login page.", () => window.location.href = "/login/");
    } else if (cmd.includes("register") || cmd.includes("sign up") || cmd.includes("create account")) {
        speak("Opening registration page.", () => window.location.href = "/reg/");
    } else if (cmd === "help") {
        speak("Say LOGIN to go to the sign in page, or say REGISTER to create a new account. Press M on your keyboard to toggle the microphone.");
    } else {
        speak("I did not understand. Say LOGIN or REGISTER.");
    }
}

/* ── mic auto-restarts so it stays alive ── */
function startListening() {
    if (!("webkitSpeechRecognition" in window || "SpeechRecognition" in window)) {
        speak("Speech recognition not supported. Please use Google Chrome."); return;
    }
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SR();
    recognition.lang = "en-IN";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
        micOn = true;
        micBtn.classList.add("mic-active");
        micIcon.className = "fa fa-microphone-slash";
        statusEl.textContent = "Listening…";
    };
    recognition.onresult = (e) => {
        handleCommand(e.results[0][0].transcript);
    };
    recognition.onerror = (e) => {
        statusEl.textContent = "Error: " + e.error;
        if (e.error === "no-speech" || e.error === "network") {
            setTimeout(() => { if (micOn) startListening(); }, 500);
        }
    };
    recognition.onend = () => {
        micOn = false;
        micBtn.classList.remove("mic-active");
        micIcon.className = "fa fa-microphone";
        statusEl.textContent = "Mic off. Press M to start again.";
    };
    recognition.start();
}

function toggleMic() {
    if (micOn) {
        micOn = false;
        recognition && recognition.stop();
    } else {
        if (isSpeaking) { responsiveVoice.cancel(); isSpeaking = false; }
        startListening();
    }
}

micBtn.addEventListener("click", toggleMic);

document.addEventListener("keydown", (e) => {
    const tag = document.activeElement.tagName.toLowerCase();
    if (tag === "input" || tag === "textarea") return;
    if (isSpeaking) { responsiveVoice.cancel(); isSpeaking = false; }
    const key = e.key.toLowerCase();
    if (key === "m") toggleMic();
    else if (key === "l") speak("Opening login page.", () => window.location.href = "/login/");
    else if (key === "r") speak("Opening registration page.", () => window.location.href = "/reg/");
    else if (key.length === 1) speak("Wrong key. Press M for microphone, L for login, R for register.");
});

/* Welcome on load */
setTimeout(() => speak(
    "Welcome to Blind Email. " +
    "This is a voice controlled email system. " +
    "Press M to start the microphone, then say LOGIN or REGISTER. " +
    "You can also press L for login or R for register."
), 1000);

/* Idle reminder every 50s */
setInterval(() => {
    if (!micOn && !isSpeaking) {
        speak("Press M and say login or register.");
    }
}, 50000);