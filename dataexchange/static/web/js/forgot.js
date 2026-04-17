
const VOICE = "UK English Female";
const emailInput = document.getElementById('emailInput');
const mobileInput = document.getElementById('mobileInput');

let recognition = null;
let micOn = false;
let isSpeaking = false;
let currentStep = "email";   // "email" | "phone"

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

/* ─── READ BACK ─── */
function makeReadable(email) {
    return email
        .replace("@", " at ")
        .replace(/\./g, " dot ")
        .replace(/_/g, " underscore ")
        .replace(/-/g, " dash ");
}

function readEmail() {
    const val = emailInput.value.trim();
    if (val) speak("You entered: " + makeReadable(val));
    else speak("Email field is empty. Please type your email using the keyboard.");
}

function readPhone() {
    const val = mobileInput.value.trim();
    if (val) speak("Phone number: " + val.split('').join(', '));
    else speak("Phone field is empty. Please type your phone number using the keyboard.");
}

/* ─── FOCUS HELPERS ─── */
function focusEmail() {
    currentStep = "email";
    emailInput.focus();
    speak(
        "Email field selected. " +
        "Please type your registered email using the keyboard. " +
        "Voice input is not accurate for emails. " +
        "Then say READ to confirm, or say PHONE to continue."
    );
}

function focusPhone() {
    currentStep = "phone";
    mobileInput.focus();
    speak(
        "Phone number field selected. " +
        "Please type your registered phone number using the keyboard. " +
        "Then say READ to confirm, or say VERIFY to submit."
    );
}

/* ─── CLEAR ─── */
function clearEmail() { emailInput.value = ""; speak("Email cleared."); }
function clearPhone() { mobileInput.value = ""; speak("Phone cleared."); }

/* ─── SUBMIT ─── */
function submitForm() {
    const email = emailInput.value.trim();
    const mobile = mobileInput.value.trim();
    if (!email && !mobile) { speak("Both fields are empty. Please type your email first."); focusEmail(); return; }
    if (!email) { speak("Email is empty. Please type your email."); focusEmail(); return; }
    if (!mobile) { speak("Phone number is empty. Please type your phone number."); focusPhone(); return; }
    speak("Verifying your identity. Please wait.", () => document.getElementById('forgotForm').submit());
}

/* ─── COMMAND HANDLER ─── */
function handleCommand(raw) {
    const cmd = raw.toLowerCase().trim();
    if (isSpeaking) { responsiveVoice.cancel(); isSpeaking = false; }

    // ── Navigation ──
    if (cmd.includes("login") || cmd.includes("back") || cmd.includes("sign in")) {
        speak("Going back to login page.", () => window.location.href = "/login/"); return;
    }
    if (cmd.includes("register") || cmd.includes("create account")) {
        speak("Opening registration page.", () => window.location.href = "/reg/"); return;
    }
    if (cmd.includes("home")) {
        speak("Going to home page.", () => window.location.href = "/blindemail/"); return;
    }

    // ── Field switching ──
    if (cmd === "email" || cmd === "e-mail" || cmd === "go to email") { focusEmail(); return; }
    if (cmd === "phone" || cmd === "mobile" || cmd === "go to phone") { focusPhone(); return; }

    // ── READ ──
    if (cmd === "read" || cmd === "red" || cmd === "reed") {
        currentStep === "email" ? readEmail() : readPhone(); return;
    }

    // ── CLEAR ──
    if (cmd === "clear" || cmd === "erase" || cmd === "delete") {
        currentStep === "email" ? clearEmail() : clearPhone(); return;
    }

    // ── NEXT / BACK ──
    if (cmd === "next" || cmd === "next field") {
        if (currentStep === "email") {
            if (!emailInput.value.trim()) { speak("Please type your email first, then say PHONE to continue."); return; }
            focusPhone();
        } else {
            speak("You are on the last field. Say VERIFY to submit.");
        }
        return;
    }
    if (cmd === "back" || cmd === "previous") {
        if (currentStep === "phone") focusEmail();
        else speak("You are already on the first field.");
        return;
    }

    // ── SUBMIT ──
    if (cmd === "verify" || cmd === "submit" || cmd.includes("verify identity")) {
        submitForm(); return;
    }

    // ── TYPE reminder ──
    if (cmd === "type") {
        if (currentStep === "email") {
            speak("Please type your email using the keyboard. Voice input is not accurate for emails.");
            emailInput.focus();
        } else {
            speak("Please type your phone number using the keyboard.");
            mobileInput.focus();
        }
        return;
    }

    // ── HELP ──
    if (cmd === "help") {
        speak(
            "Forgot password page. " +
            "Say EMAIL to focus the email field. " +
            "Say PHONE to focus the phone number field. " +
            "Say READ to hear what you have typed. " +
            "Say CLEAR to erase the current field. " +
            "Say NEXT or BACK to move between fields. " +
            "Say VERIFY to submit. " +
            "Say BACK TO LOGIN to return to the login page. " +
            "Always type your email with the keyboard."
        );
        return;
    }

    speak("Command not recognised. Say HELP for all commands.");
}

/* ─── MIC ─── */
function startListening() {
    if (!("webkitSpeechRecognition" in window || "SpeechRecognition" in window)) {
        speak("Speech recognition not supported. Please use Google Chrome."); return;
    }
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SR();
    recognition.lang = "en-IN";
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.onresult = (e) => handleCommand(e.results[e.results.length - 1][0].transcript);
    recognition.onerror = (e) => { if (e.error === "no-speech" || e.error === "network") setTimeout(() => { if (micOn) recognition.start(); }, 500); };
    recognition.onend = () => { if (micOn) setTimeout(() => recognition.start(), 300); };
    recognition.start();
}

function toggleMic() {
    if (micOn) {
        micOn = false; recognition && recognition.stop(); speak("Microphone off.");
    } else {
        micOn = true; startListening(); speak("Microphone on. Listening for commands.");
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
    else if (key === "p") focusPhone();
    else if (key === "r") { currentStep === "email" ? readEmail() : readPhone(); }
    else if (key === "c") { currentStep === "email" ? clearEmail() : clearPhone(); }
});

/* ─── ON LOAD ─── */
document.addEventListener("DOMContentLoaded", () => {
    const errBox = document.getElementById('errorBox');
    const errText = errBox ? errBox.textContent.trim() : "";

    if (errText) {
        speak(errText + ". Say EMAIL to try again.");
    } else {
        speak(
            "Forgot password page. " +
            "Enter your registered email and phone number to verify your identity. " +
            "Press M to activate the microphone. " +
            "Say EMAIL to go to the email field, then type with the keyboard. " +
            "Say HELP for all commands."
        );
    }

    // track field focus from click/tab
    emailInput.addEventListener("focus", () => { currentStep = "email"; });
    mobileInput.addEventListener("focus", () => { currentStep = "phone"; });

    focusEmail();
});