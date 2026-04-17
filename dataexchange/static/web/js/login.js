const VOICE = "UK English Female";

const emailInput = document.getElementById('emailInput');
const passwordInput = document.getElementById('passwordInput');

let recognition = null;
let micOn = false;
let isSpeaking = false;
let currentStep = "email";   // "email" | "password"
let inactivityTimer;
let userInteracted = false;

/* ─── SPEAK ─── */
function speak(text, cb = null) {
    if (!window.responsiveVoice) return;
    responsiveVoice.cancel();
    isSpeaking = true;
    responsiveVoice.speak(text, VOICE, {
        rate: 0.9,
        onend: () => { isSpeaking = false; if (cb) cb(); }
    });
}

/* ─── READ BACK: makes email human-readable ─── */
function makeReadable(email) {
    return email
        .replace("@", " at ")
        .replace(/\./g, " dot ")
        .replace(/_/g, " underscore ")
        .replace(/-/g, " dash ");
}

function readEmail() {
    const val = emailInput.value.trim();
    if (val) {
        speak("You entered: " + makeReadable(val));
    } else {
        speak("Email field is empty. Please type your email using the keyboard.");
    }
}

function readPassword() {
    if (passwordInput.value) {
        speak("Password entered. " + passwordInput.value.length + " characters.");
    } else {
        speak("Password field is empty. Please type your password using the keyboard.");
    }
}

/* ─── FOCUS HELPERS ─── */
function focusEmail() {
    currentStep = "email";
    emailInput.focus();
    speak(
        "Email field selected. " +
        "Please type your email using the keyboard. " +
        "Voice input is not accurate for email addresses. " +
        "Then say READ to confirm, or say PASSWORD to move on."
    );
}

function focusPassword() {
    currentStep = "password";
    passwordInput.focus();
    speak(
        "Password field selected. " +
        "Please type your password using the keyboard. " +
        "Then say READ to confirm the character count, or say LOGIN to sign in."
    );
}

/* ─── CLEAR ─── */
function clearEmail() {
    emailInput.value = "";
    speak("Email cleared.");
}

function clearPassword() {
    passwordInput.value = "";
    speak("Password cleared.");
}

/* ─── SUBMIT ─── */
function submitForm() {
    const email = emailInput.value.trim();
    const pass = passwordInput.value;
    if (!email && !pass) {
        speak("Both fields are empty. Type your email first."); focusEmail(); return;
    }
    if (!email) {
        speak("Email is empty. Please type your email."); focusEmail(); return;
    }
    if (!pass) {
        speak("Password is empty. Please type your password."); focusPassword(); return;
    }
    speak("Signing in. Please wait.", () => document.getElementById('loginForm').submit());
}

/* ─── INACTIVITY HINT ─── */
function resetTimer() {
    clearTimeout(inactivityTimer);
    if (!userInteracted) return;
    inactivityTimer = setTimeout(() => {
        if (currentStep === "email") {
            speak(emailInput.value.trim()
                ? "Email entered. Say PASSWORD to continue."
                : "Waiting for email. Type it using the keyboard, then say READ to confirm.");
        } else {
            speak(passwordInput.value
                ? "Password entered. Say LOGIN to sign in."
                : "Waiting for password. Type it using the keyboard.");
        }
    }, 5000);
}

/* ─── COMMAND HANDLER ─── */
function handleCommand(raw) {
    userInteracted = true;
    const cmd = raw.toLowerCase().trim();
    resetTimer();
    if (isSpeaking) { responsiveVoice.cancel(); isSpeaking = false; }

    // ── Global navigation ──
    if (cmd.includes("register") || cmd.includes("create account")) {
        speak("Opening registration page.", () => window.location.href = "/reg/"); return;
    }
    if (cmd.includes("forgot") || cmd.includes("reset password")) {
        speak("Opening forgot password page.", () => window.location.href = "/forgot/"); return;
    }
    if (cmd.includes("home") || cmd.includes("go back")) {
        speak("Going to home page.", () => window.location.href = "/blindemail/"); return;
    }
    if (cmd === "help") {
        speak(
            "Available commands: " +
            "Say EMAIL to focus the email field. " +
            "Say PASSWORD to move to the password field. " +
            "Say READ to hear what you have typed. " +
            "Say CLEAR to erase the current field. " +
            "Say LOGIN to sign in. " +
            "Important tip: always type your email and password with the keyboard. " +
            "Voice is only for navigation and confirmation."
        );
        return;
    }

    // ── Field switching ──
    if (cmd === "email" || cmd === "go to email") { focusEmail(); return; }
    if (cmd === "password" || cmd === "go to password") {
        if (currentStep === "email" && !emailInput.value.trim()) {
            speak("Please type your email first, then say PASSWORD."); return;
        }
        focusPassword(); return;
    }

    // ── READ ──
    if (cmd === "read" || cmd === "red" || cmd === "reed") {
        currentStep === "email" ? readEmail() : readPassword(); return;
    }

    // ── CLEAR ──
    if (cmd === "clear" || cmd === "erase" || cmd === "delete") {
        currentStep === "email" ? clearEmail() : clearPassword(); return;
    }

    // ── TYPE reminder ──
    if (cmd === "type") {
        if (currentStep === "email") {
            speak("Please type your email using the keyboard. Voice is not accurate for emails. Say READ when done.");
        } else {
            speak("Please type your password using the keyboard. Say READ to confirm character count.");
        }
        return;
    }

    // ── SUBMIT ──
    if (cmd === "login" || cmd === "submit" || cmd === "sign in" || cmd === "enter") {
        submitForm(); return;
    }

    // ── Unrecognised ──
    speak("Command not recognised. Say HELP for a list of commands.");
}

/* ─── MIC: auto-restarts to stay alive ─── */
function startListening() {
    if (!("webkitSpeechRecognition" in window || "SpeechRecognition" in window)) {
        speak("Speech recognition not supported. Please use Google Chrome."); return;
    }
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SR();
    recognition.lang = "en-IN";
    recognition.continuous = true;
    recognition.interimResults = false;

    recognition.onresult = (e) => {
        const text = e.results[e.results.length - 1][0].transcript;
        if (isSpeaking) { responsiveVoice.cancel(); isSpeaking = false; }
        handleCommand(text);
    };
    recognition.onerror = (e) => {
        if (e.error === "no-speech" || e.error === "network") {
            setTimeout(() => { if (micOn) recognition.start(); }, 500);
        }
    };
    recognition.onend = () => {
        if (micOn) setTimeout(() => recognition.start(), 300);
    };
    recognition.start();
}

function toggleMic() {
    if (micOn) {
        micOn = false;
        recognition && recognition.stop();
        speak("Microphone off.");
    } else {
        micOn = true;
        startListening();
        speak("Microphone on. Listening for commands.");
    }
}

/* ─── KEYBOARD SHORTCUTS ─── */
document.addEventListener("keydown", (e) => {
    const tag = document.activeElement.tagName.toLowerCase();
    if (tag === "input" || tag === "textarea") return;
    if (isSpeaking) { responsiveVoice.cancel(); isSpeaking = false; }
    const key = e.key.toLowerCase();
    if (key === "m") toggleMic();
    else if (key === "e") focusEmail();
    else if (key === "p") focusPassword();
    else if (key === "r") { currentStep === "email" ? readEmail() : readPassword(); }
    else if (key === "c") { currentStep === "email" ? clearEmail() : clearPassword(); }
});

/* ─── ON LOAD ─── */
$(document).ready(function () {
    const msg = $(".django-msg").first().text().trim();
    if (msg) {
        speak(msg + ". Say EMAIL to try again.");
    } else {
        speak(
            "Login page. " +
            "Press M to activate the microphone for voice commands. " +
            "Say EMAIL to go to the email field, then type with the keyboard. " +
            "Say HELP for all commands."
        );
    }

    // toast auto-dismiss
    setTimeout(() => {
        $(".toast-card").fadeOut(600, function () { $(this).remove(); });
    }, 5000);

    // track which field is active when user clicks/tabs
    emailInput.addEventListener("focus", () => { currentStep = "email"; userInteracted = true; resetTimer(); });
    passwordInput.addEventListener("focus", () => { currentStep = "password"; userInteracted = true; resetTimer(); });

    // idle reminder every 30s
    setInterval(() => {
        if (!micOn && !isSpeaking) {
            speak("Press M to activate voice control.");
        }
    }, 30000);
});