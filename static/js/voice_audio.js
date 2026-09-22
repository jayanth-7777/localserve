// Web Speech API: Text-to-Speech (TTS) & Speech-to-Text (STT) Voice Engine

// Text-to-Speech (Audio Readout)
function speakText(text, lang) {
  if (!('speechSynthesis' in window)) {
    alert('Voice readout is not supported in this browser. Please use Chrome or Edge.');
    return;
  }

  // Cancel any ongoing speech
  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  const targetLang = lang || currentLang || 'en';

  if (targetLang === 'te') {
    utterance.lang = 'te-IN';
  } else if (targetLang === 'hi') {
    utterance.lang = 'hi-IN';
  } else {
    utterance.lang = 'en-IN';
  }

  utterance.rate = 0.95; // Slightly slower pace for clarity in rural communities
  utterance.pitch = 1.0;

  // Attempt to select native matching voice if available
  const voices = window.speechSynthesis.getVoices();
  const matchedVoice = voices.find(v => v.lang.startsWith(utterance.lang.split('-')[0]));
  if (matchedVoice) {
    utterance.voice = matchedVoice;
  }

  window.speechSynthesis.speak(utterance);
}

// Read card or container aloud
function readCardAloud(button) {
  const card = button.closest('[data-speech-en]') || button;
  const lang = currentLang || 'en';
  let speechText = card.getAttribute(`data-speech-${lang}`);

  // Fallback to English if translation specific string not provided
  if (!speechText) {
    speechText = card.getAttribute('data-speech-en') || button.getAttribute('title') || 'Information';
  }

  // Visual feedback: animate speaker icon
  const icon = button.querySelector('i');
  if (icon) {
    icon.classList.remove('fa-volume-high');
    icon.classList.add('fa-spinner', 'fa-spin');
    setTimeout(() => {
      icon.classList.remove('fa-spinner', 'fa-spin');
      icon.classList.add('fa-volume-high');
    }, 1500);
  }

  speakText(speechText, lang);
}

// Speech-to-Text Voice Recognition
function startVoiceSearch(inputId, formId) {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    alert('Voice input is not supported in this browser. Please use Google Chrome or Microsoft Edge.');
    return;
  }

  const recognition = new SpeechRecognition();
  const lang = currentLang || 'en';

  if (lang === 'te') {
    recognition.lang = 'te-IN';
  } else if (lang === 'hi') {
    recognition.lang = 'hi-IN';
  } else {
    recognition.lang = 'en-IN';
  }

  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  const micBtn = event.currentTarget;
  const input = document.getElementById(inputId);
  const originalPlaceholder = input ? input.placeholder : '';

  if (micBtn) micBtn.classList.add('listening');
  if (input) {
    input.placeholder = lang === 'te' ? 'వినబడుతోంది... మాట్లాడండి' : (lang === 'hi' ? 'सुन रहे हैं... बोलिए' : 'Listening... speak now');
  }

  // Audio prompt to user
  const promptMessage = lang === 'te' ? 'చెప్పండి' : (lang === 'hi' ? 'बोलिए' : 'Speak now');
  speakText(promptMessage, lang);

  recognition.onresult = function(event) {
    const transcript = event.results[0][0].transcript;
    if (input) {
      input.value = transcript;
    }
    if (micBtn) micBtn.classList.remove('listening');
    if (input) input.placeholder = originalPlaceholder;

    // Speak confirmation
    const confirmMessage = lang === 'te' ? `శోధిస్తున్నాము: ${transcript}` : (lang === 'hi' ? `खोज रहे हैं: ${transcript}` : `Searching: ${transcript}`);
    speakText(confirmMessage, lang);

    // Auto submit form after 1 second if formId provided
    if (formId) {
      setTimeout(() => {
        const form = document.getElementById(formId);
        if (form) form.submit();
      }, 1000);
    }
  };

  recognition.onerror = function(event) {
    console.error('Speech recognition error:', event.error);
    if (micBtn) micBtn.classList.remove('listening');
    if (input) input.placeholder = originalPlaceholder;
    const errorMsg = lang === 'te' ? 'వాయిస్ అందలేదు, దయచేసి మళ్ళీ ప్రయత్నించండి.' : 'Could not hear voice. Please tap mic again.';
    speakText(errorMsg, lang);
  };

  recognition.onend = function() {
    if (micBtn) micBtn.classList.remove('listening');
    if (input) input.placeholder = originalPlaceholder;
  };

  recognition.start();
}

// Pre-load voices on load
if ('speechSynthesis' in window) {
  window.speechSynthesis.onvoiceschanged = () => {
    window.speechSynthesis.getVoices();
  };
}
