/* ═══════════════════════════════════════════════════════
   BLIND EMAIL — Voice Engine
   Commands: SPEAK, READ, TYPE <text>, CLEAR, ENTER, NEXT, BACK
   ═══════════════════════════════════════════════════════ */

window.VoiceEngine = (function () {
  let recognition = null;
  let isMicOn = false;
  let currentFieldIndex = 0;
  let fields = [];
  let statusEl = null;
  let micBtn = null;
  let onEnterCallback = null;

  const VOICE = "UK English Female";
  const RATE  = 0.88;

  /* ── speak ── */
  function speak(text, onDone) {
    if (!window.responsiveVoice) return;
    responsiveVoice.cancel();
    responsiveVoice.speak(text, VOICE, { rate: RATE, onend: onDone });
  }

  /* ── update mic UI ── */
  function setStatus(text) {
    if (statusEl) statusEl.textContent = text;
  }

  /* ── read current field ── */
  function readCurrentField() {
    const f = fields[currentFieldIndex];
    if (!f) return;
    const label = f.getAttribute("aria-label") || f.placeholder || f.name || "field";
    const val   = f.value.trim();
    const msg   = val
      ? `${label}. Current value: ${val}.`
      : `${label}. Currently empty.`;
    speak(msg);
    f.focus();
  }

  /* ── move focus ── */
  function focusField(idx) {
    if (idx < 0 || idx >= fields.length) return;
    currentFieldIndex = idx;
    readCurrentField();
  }

  /* ── type into current field ── */
  function typeIntoField(text) {
    const f = fields[currentFieldIndex];
    if (!f) return;
    const label = f.getAttribute("aria-label") || f.placeholder || "field";
    if (f.tagName === "TEXTAREA") {
      f.value += (f.value ? " " : "") + text;
    } else {
      f.value = text;
    }
    speak(`Typed "${text}" into ${label}. Say READ to confirm.`);
  }

  /* ── clear current field ── */
  function clearField() {
    const f = fields[currentFieldIndex];
    if (!f) return;
    f.value = "";
    const label = f.getAttribute("aria-label") || f.placeholder || "field";
    speak(`${label} cleared.`);
  }

  /* ── handle recognised command ── */
  function handleCommand(raw) {
    const cmd = raw.trim().toLowerCase();
    setStatus(`"${raw}"`);

    if (cmd === "read" || cmd === "red") {
      readCurrentField();

    } else if (cmd === "clear") {
      clearField();

    } else if (cmd === "enter" || cmd === "submit") {
      speak("Submitting form.", () => {
        if (onEnterCallback) onEnterCallback();
        else document.querySelector("form")?.submit();
      });

    } else if (cmd === "next") {
      focusField(Math.min(currentFieldIndex + 1, fields.length - 1));

    } else if (cmd === "back" || cmd === "previous") {
      focusField(Math.max(currentFieldIndex - 1, 0));

    } else if (cmd.startsWith("type ")) {
      typeIntoField(raw.slice(5));

    } else if (cmd.startsWith("go to ")) {
      // navigation e.g. "go to login"
      const dest = cmd.replace("go to ", "").trim();
      speak(`Navigating to ${dest}.`, () => {
        const links = document.querySelectorAll("a");
        links.forEach(l => {
          if (l.textContent.toLowerCase().includes(dest)) l.click();
        });
      });

    } else if (cmd === "help") {
      speak(
        "Available commands: " +
        "Say TYPE followed by your text to fill this field. " +
        "Say READ to hear what you have typed. " +
        "Say CLEAR to erase this field. " +
        "Say NEXT to move to the next field. " +
        "Say BACK to go to the previous field. " +
        "Say ENTER to submit the form. " +
        "Say GO TO followed by a page name to navigate."
      );

    } else {
      // treat anything else as dictation into current field
      typeIntoField(raw);
    }
  }

  /* ── start recognition ── */
  function startMic() {
    if (!("webkitSpeechRecognition" in window || "SpeechRecognition" in window)) {
      speak("Speech recognition is not supported in this browser. Please use Google Chrome.");
      return;
    }
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SR();
    recognition.lang = "en-GB";
    recognition.continuous = true;
    recognition.interimResults = false;

    recognition.onstart = () => {
      isMicOn = true;
      if (micBtn) micBtn.classList.add("mic-active");
      setStatus("Listening…");
    };

    recognition.onresult = (e) => {
      const transcript = e.results[e.results.length - 1][0].transcript;
      handleCommand(transcript);
    };

    recognition.onerror = (e) => {
      setStatus("Mic error: " + e.error);
    };

    recognition.onend = () => {
      isMicOn = false;
      if (micBtn) micBtn.classList.remove("mic-active");
      setStatus("Mic off");
    };

    recognition.start();
  }

  function stopMic() {
    if (recognition) recognition.stop();
  }

  function toggleMic() {
    if (isMicOn) stopMic();
    else startMic();
  }

  /* ── init ── */
  function init({ fieldSelectors, micBtnId, statusId, welcomeMsg, onEnter }) {
    statusEl = document.getElementById(statusId);
    micBtn   = document.getElementById(micBtnId);
    onEnterCallback = onEnter || null;

    // collect fields in tab order
    fields = Array.from(
      document.querySelectorAll(fieldSelectors || "input:not([type=submit]):not([type=checkbox]):not([type=radio]):not([disabled]), textarea, select")
    ).filter(f => !f.closest("[disabled]") && f.type !== "hidden");

    // click each field → update index
    fields.forEach((f, i) => {
      f.addEventListener("focus", () => { currentFieldIndex = i; });
    });

    // mic button
    if (micBtn) micBtn.addEventListener("click", toggleMic);

    // keyboard shortcut: M = toggle mic
    document.addEventListener("keydown", e => {
      if (e.key.toLowerCase() === "m" && document.activeElement.tagName !== "INPUT" && document.activeElement.tagName !== "TEXTAREA") {
        toggleMic();
      }
    });

    // welcome speech on load
    if (welcomeMsg) {
      setTimeout(() => speak(welcomeMsg), 600);
    }

    // auto-focus first field
    if (fields[0]) fields[0].focus();
  }

  return { init, speak, toggleMic, startMic, stopMic };
})();