    /* ════════════════════════════════════
       FIELD REGISTRY
       ════════════════════════════════════ */
    const fields = [
        { id: 'f-name',      label: 'Full name',              type: 'text'     },
        { id: 'f-address',   label: 'Address',                type: 'textarea' },
        { id: 'f-dob',       label: 'Date of birth',          type: 'date'     },
        { id: null,          label: 'Gender',                 type: 'radio'    },
        { id: 'f-email',     label: 'Email address',          type: 'email'    },
        { id: 'f-mobile',    label: 'Phone number',           type: 'tel'      },
        { id: 'f-photo',     label: 'Profile photo, optional',type: 'file'     },
        { id: 'f-password',  label: 'Password',               type: 'password' },
        { id: 'f-cpassword', label: 'Confirm password',       type: 'password' },
        { id: 'f-answer',    label: 'Security answer, your favourite colour', type: 'text' },
    ];
 
    fields.forEach(f => { f.el = f.id ? document.getElementById(f.id) : null; });
 
    const VOICE    = "UK English Female";
    let recognition = null;
    let micOn       = false;
    let isSpeaking  = false;
    let currentIdx  = 0;
 
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
 
    /* ─── SMART READ BACK ─── */
    function makeReadable(str) {
        return str
            .replace("@", " at ")
            .replace(/\./g, " dot ")
            .replace(/_/g, " underscore ")
            .replace(/-/g, " dash ");
    }
 
    function readField() {
        const f = fields[currentIdx];
        if (f.type === 'radio') {
            const val = document.querySelector('input[name=gender]:checked')?.value || 'male';
            speak("Gender. Current selection: " + val + "."); return;
        }
        if (f.type === 'file') {
            const count = f.el?.files?.length;
            speak(count ? "Profile photo selected." : "No profile photo selected. This field is optional."); return;
        }
        if (!f.el) return;
        const val = f.el.value.trim();
        if (!val) { speak(f.label + ". Currently empty."); return; }
        if (f.type === 'password')  { speak(f.label + ". " + val.length + " characters entered."); return; }
        if (f.type === 'email')     { speak("You entered: " + makeReadable(val)); return; }
        if (f.type === 'tel')       { speak("Phone number: " + val.split('').join(', ')); return; }
        if (f.type === 'date') {
            const d = new Date(val);
            speak("Date of birth: " + d.toDateString() + "."); return;
        }
        speak(f.label + ". You entered: " + val + ".");
    }
 
    /* ─── FOCUS ─── */
    function focusField(idx) {
        if (idx < 0 || idx >= fields.length) return;
        currentIdx = idx;
        const f = fields[idx];
        if (f.type === 'radio') {
            speak("Gender field. Current selection: " + (document.querySelector('input[name=gender]:checked')?.value || 'male') + ". Say MALE or FEMALE to change.");
            return;
        }
        if (f.el) { f.el.focus(); }
        const isKeyboard = ['email','tel','password','text','textarea'].includes(f.type);
        let msg = f.label + " field selected. ";
        if (isKeyboard) {
            msg += "Please type using the keyboard. ";
            if (f.type === 'email') msg += "Voice input is not accurate for emails. ";
            msg += "Then say READ to confirm.";
        } else if (f.type === 'date') {
            msg += "Please select your date of birth using the keyboard or date picker.";
        } else if (f.type === 'file') {
            msg += "This field is optional. Press Enter or Space to open the file picker.";
        }
        speak(msg);
    }
 
    /* ─── CLEAR ─── */
    function clearField() {
        const f = fields[currentIdx];
        if (f.type === 'radio') { speak("Cannot clear gender. Say MALE or FEMALE to choose."); return; }
        if (f.type === 'file')  { speak("Cannot clear file field with voice. This field is optional."); return; }
        if (f.el) { f.el.value = ""; speak(f.label + " cleared."); }
    }
 
    /* ─── SUBMIT WITH VALIDATION ─── */
    function submitForm() {
        const checks = [
            { id: 'f-name',     label: 'your full name',       idx: 0 },
            { id: 'f-address',  label: 'your address',         idx: 1 },
            { id: 'f-dob',      label: 'your date of birth',   idx: 2 },
            { id: 'f-email',    label: 'your email address',   idx: 4 },
            { id: 'f-mobile',   label: 'your phone number',    idx: 5 },
            { id: 'f-password', label: 'a password',           idx: 7 },
            { id: 'f-answer',   label: 'your security answer', idx: 9 },
        ];
        for (const c of checks) {
            if (!document.getElementById(c.id)?.value.trim()) {
                speak("Please enter " + c.label + " first."); focusField(c.idx); return;
            }
        }
        const pass  = document.getElementById('f-password').value;
        const cpass = document.getElementById('f-cpassword').value;
        if (pass !== cpass) {
            speak("Passwords do not match. Please re-enter your confirm password.");
            focusField(8); return;
        }
        if (!document.getElementById('termsCheck').checked) {
            speak("Please agree to the terms and privacy before registering.");
            document.getElementById('termsCheck').focus(); return;
        }
        speak("Creating your account. Please wait.", () => document.getElementById('regForm').submit());
    }
 
    /* ─── COMMAND HANDLER ─── */
    function handleCommand(raw) {
        const cmd = raw.toLowerCase().trim();
        if (isSpeaking) { responsiveVoice.cancel(); isSpeaking = false; }
 
        // ── Navigation ──
        if (cmd.includes("login") || cmd.includes("sign in")) {
            speak("Going to login page.", () => window.location.href = "/login/"); return;
        }
        if (cmd.includes("home") || cmd.includes("go back")) {
            speak("Going to home page.", () => window.location.href = "/blindemail/"); return;
        }
 
        // ── Jump to field by name ──
        const jumps = {
            "name": 0, "full name": 0,
            "address": 1,
            "date of birth": 2, "birthday": 2, "dob": 2,
            "gender": 3,
            "email": 4, "e-mail": 4,
            "phone": 5, "mobile": 5,
            "photo": 6, "image": 6, "picture": 6,
            "password": 7,
            "confirm": 8, "confirm password": 8,
            "answer": 9, "security": 9, "colour": 9, "color": 9,
        };
        for (const [kw, idx] of Object.entries(jumps)) {
            if (cmd === kw || cmd === "go to " + kw) {
                focusField(idx); return;
            }
        }
 
        // ── Gender ──
        if (cmd === "male" || cmd === "select male") {
            document.querySelector('input[name=gender][value=male]').checked = true;
            speak("Gender set to male."); return;
        }
        if (cmd === "female" || cmd === "select female") {
            document.querySelector('input[name=gender][value=female]').checked = true;
            speak("Gender set to female."); return;
        }
 
        // ── Core commands ──
        if (cmd === "read" || cmd === "red" || cmd === "reed") { readField(); return; }
        if (cmd === "clear" || cmd === "erase" || cmd === "delete") { clearField(); return; }
        if (cmd === "next" || cmd === "next field") {
            if (currentIdx < fields.length - 1) { focusField(currentIdx + 1); }
            else speak("You are on the last field. Say REGISTER to create your account.");
            return;
        }
        if (cmd === "back" || cmd === "previous") {
            if (currentIdx > 0) { focusField(currentIdx - 1); }
            else speak("You are on the first field.");
            return;
        }
        if (cmd === "register" || cmd === "submit" || cmd.includes("create account")) {
            submitForm(); return;
        }
        if (cmd === "type") {
            const f = fields[currentIdx];
            if (f.type === 'email') {
                speak("Please type your email using the keyboard. Voice is not accurate for email addresses.");
            } else if (f.type === 'password') {
                speak("Please type your password using the keyboard. Say READ to confirm the character count.");
            } else if (f.type === 'radio') {
                speak("Say MALE or FEMALE to choose your gender.");
            } else if (f.type === 'file') {
                speak("This is a file upload field. Press Enter to open the file picker.");
            } else {
                speak("Please type into the " + f.label + " field using the keyboard. Say READ to confirm.");
            }
            if (f.el) f.el.focus();
            return;
        }
        if (cmd === "help") {
            speak(
                "You are on the registration page. " +
                "Say a field name to jump to it: NAME, ADDRESS, DATE OF BIRTH, GENDER, EMAIL, PHONE, PHOTO, PASSWORD, CONFIRM PASSWORD, or SECURITY ANSWER. " +
                "Say NEXT or BACK to move between fields. " +
                "Say READ to hear what you have entered. " +
                "Say CLEAR to erase a field. " +
                "Say MALE or FEMALE to choose gender. " +
                "Say REGISTER to create your account. " +
                "Always type email and password with the keyboard."
            );
            return;
        }
 
        speak("Command not recognised. Say HELP for all available commands.");
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
        recognition.onerror  = (e) => { if (e.error === "no-speech" || e.error === "network") setTimeout(() => { if (micOn) recognition.start(); }, 500); };
        recognition.onend    = () => { if (micOn) setTimeout(() => recognition.start(), 300); };
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
        if      (key === "m") toggleMic();
        else if (key === "n") { if (currentIdx < fields.length - 1) focusField(currentIdx + 1); }
        else if (key === "b") { if (currentIdx > 0) focusField(currentIdx - 1); }
        else if (key === "r") readField();
    });
 
    /* ─── TOAST HELPERS ─── */
    function closeToast(btn) {
        let toast = btn.closest('.toast-card');
        toast.style.transform = "translateX(120%)";
        toast.style.transition = "0.5s ease";
        setTimeout(() => toast.remove(), 500);
    }
 
    /* ─── ON LOAD ─── */
    document.addEventListener("DOMContentLoaded", function () {
        // set max date for dob
        document.getElementById('f-dob').setAttribute('max', new Date().toISOString().split("T")[0]);
 
        // track field focus from mouse/tab
        fields.forEach((f, i) => {
            if (f.el) f.el.addEventListener("focus", () => { currentIdx = i; });
        });
 
        // toast auto-dismiss
        document.querySelectorAll('.toast-card').forEach(toast => {
            setTimeout(() => {
                toast.style.transform = "translateX(120%)";
                toast.style.transition = "0.5s ease";
                setTimeout(() => toast.remove(), 500);
            }, 5000);
        });
 
        // speak any Django alert then welcome
        const alertMsg = document.querySelector('.django-msg')?.textContent.trim();
        if (alertMsg) {
            speak(alertMsg + ". Press M to activate the microphone.");
        } else {
            speak(
                "Registration page. " +
                "There are 9 fields to complete. " +
                "Press M to activate the microphone for voice commands. " +
                "Say HELP for all commands. " +
                "Say NAME to begin. " +
                "Remember: always type your email and password using the keyboard."
            );
        }
 
        focusField(0);
    });