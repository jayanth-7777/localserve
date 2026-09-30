// LOCALServe 2.0 - Smart Service Assistant
// Natural Language & Voice Intent Matching for Hyperlocal Services, Medicines & Skills

document.addEventListener('DOMContentLoaded', function () {
  const assistantBtn = document.getElementById('assistantTriggerBtn');
  const assistantModalEl = document.getElementById('assistantModal');
  const assistantInput = document.getElementById('assistantInput');
  const assistantSendBtn = document.getElementById('assistantSendBtn');
  const assistantMicBtn = document.getElementById('assistantMicBtn');
  const assistantChatBody = document.getElementById('assistantChatBody');
  const assistantChips = document.querySelectorAll('.assistant-chip');

  if (!assistantModalEl) return;

  const assistantModal = new bootstrap.Modal(assistantModalEl);

  if (assistantBtn) {
    assistantBtn.addEventListener('click', function () {
      assistantModal.show();
    });
  }

  // Pre-set suggestion chips
  assistantChips.forEach(chip => {
    chip.addEventListener('click', function () {
      const query = this.getAttribute('data-query');
      if (query) {
        processQuery(query);
      }
    });
  });

  if (assistantSendBtn && assistantInput) {
    assistantSendBtn.addEventListener('click', function () {
      const q = assistantInput.value.trim();
      if (q) {
        processQuery(q);
        assistantInput.value = '';
      }
    });

    assistantInput.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        const q = assistantInput.value.trim();
        if (q) {
          processQuery(q);
          assistantInput.value = '';
        }
      }
    });
  }

  // Speech Recognition integration
  if (assistantMicBtn) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;

      // Determine speech language based on app language
      const currentLang = localStorage.getItem('localserve_lang') || 'en';
      if (currentLang === 'te') {
        recognition.lang = 'te-IN';
      } else if (currentLang === 'hi') {
        recognition.lang = 'hi-IN';
      } else {
        recognition.lang = 'en-IN';
      }

      assistantMicBtn.addEventListener('click', function () {
        try {
          recognition.start();
          assistantMicBtn.classList.add('btn-danger', 'animate-pulse');
          assistantMicBtn.innerHTML = '<i class="fa-solid fa-microphone-lines"></i> Listening...';
        } catch (err) {
          console.warn("Speech recognition error:", err);
        }
      });

      recognition.onresult = function (event) {
        assistantMicBtn.classList.remove('btn-danger', 'animate-pulse');
        assistantMicBtn.classList.add('btn-outline-primary');
        assistantMicBtn.innerHTML = '<i class="fa-solid fa-microphone"></i>';
        const transcript = event.results[0][0].transcript;
        if (transcript) {
          processQuery(transcript);
        }
      };

      recognition.onerror = function () {
        assistantMicBtn.classList.remove('btn-danger', 'animate-pulse');
        assistantMicBtn.classList.add('btn-outline-primary');
        assistantMicBtn.innerHTML = '<i class="fa-solid fa-microphone"></i>';
      };

      recognition.onend = function () {
        assistantMicBtn.classList.remove('btn-danger', 'animate-pulse');
        assistantMicBtn.classList.add('btn-outline-primary');
        assistantMicBtn.innerHTML = '<i class="fa-solid fa-microphone"></i>';
      };
    } else {
      assistantMicBtn.style.display = 'none';
    }
  }

  function appendMessage(sender, text, isHtml = false, actionButtons = []) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `d-flex mb-3 ${sender === 'user' ? 'justify-content-end' : 'justify-content-start'}`;

    let innerContent = '';
    if (sender === 'user') {
      innerContent = `
        <div class="bg-primary text-white p-2 px-3 rounded-4 shadow-sm" style="max-width: 80%;">
          <div>${escapeHtml(text)}</div>
        </div>
      `;
    } else {
      let btnsHtml = '';
      if (actionButtons && actionButtons.length > 0) {
        btnsHtml = '<div class="mt-2 d-flex flex-wrap gap-1">';
        actionButtons.forEach(btn => {
          btnsHtml += `<a href="${btn.url}" class="btn btn-sm ${btn.btnClass || 'btn-outline-primary'} py-1 px-2" style="font-size: 0.8rem;">
            ${btn.icon ? `<i class="${btn.icon} me-1"></i>` : ''}${escapeHtml(btn.label)}
          </a>`;
        });
        btnsHtml += '</div>';
      }

      innerContent = `
        <div class="d-flex align-items-start gap-2" style="max-width: 85%;">
          <div class="bg-warning text-dark p-2 rounded-circle fs-6 d-flex align-items-center justify-content-center" style="width: 32px; height: 32px;">
            <i class="fa-solid fa-robot"></i>
          </div>
          <div class="bg-light border text-dark p-3 rounded-4 shadow-sm">
            <div>${isHtml ? text : escapeHtml(text)}</div>
            ${btnsHtml}
            <div class="text-end mt-1">
              <button class="btn btn-sm btn-link p-0 text-muted" onclick="speakAssistantText(this)" title="Read out" style="font-size: 0.75rem;">
                <i class="fa-solid fa-volume-high"></i> Read aloud
              </button>
            </div>
          </div>
        </div>
      `;
    }

    msgDiv.innerHTML = innerContent;
    assistantChatBody.appendChild(msgDiv);
    assistantChatBody.scrollTop = assistantChatBody.scrollHeight;
  }

  function processQuery(query) {
    appendMessage('user', query);

    // Show typing indicator
    const typingIndicator = document.createElement('div');
    typingIndicator.id = 'assistantTyping';
    typingIndicator.className = 'd-flex align-items-center gap-2 mb-3 text-muted small';
    typingIndicator.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin text-primary"></i> <span>LOCALServe Assistant is analyzing...</span>';
    assistantChatBody.appendChild(typingIndicator);
    assistantChatBody.scrollTop = assistantChatBody.scrollHeight;

    const lat = window.userLat || 17.3850;
    const lng = window.userLng || 78.4867;

    fetch('/api/assistant', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query: query, lat: lat, lng: lng })
    })
    .then(res => res.json())
    .then(data => {
      const typingEl = document.getElementById('assistantTyping');
      if (typingEl) typingEl.remove();

      let replyHtml = `<p class="mb-1">${escapeHtml(data.reply)}</p>`;
      const actionButtons = [];

      if (data.intent === 'emergency') {
        replyHtml += `<div class="alert alert-danger py-1 px-2 mb-2 small fw-bold"><i class="fa-solid fa-triangle-exclamation"></i> Emergency Mode Triggered!</div>`;
        actionButtons.push({
          label: 'Open Emergency Dial',
          url: data.redirect_url || '/emergency',
          icon: 'fa-solid fa-phone-volume',
          btnClass: 'btn-danger'
        });
      } else if (data.intent === 'service' && data.category) {
        actionButtons.push({
          label: `View ${data.category}s`,
          url: data.redirect_url || `/services?category=${encodeURIComponent(data.category)}`,
          icon: 'fa-solid fa-wrench',
          btnClass: 'btn-primary'
        });
      } else if (data.intent === 'medicine') {
        actionButtons.push({
          label: 'Search Medicines',
          url: data.redirect_url || `/medicines?search=${encodeURIComponent(data.medicine_keyword || '')}`,
          icon: 'fa-solid fa-prescription-bottle-medical',
          btnClass: 'btn-success'
        });
        actionButtons.push({
          label: 'Request Medicine',
          url: '/medicine-request',
          icon: 'fa-solid fa-file-prescription',
          btnClass: 'btn-outline-secondary'
        });
      } else if (data.intent === 'skill') {
        actionButtons.push({
          label: 'Explore Skill Courses',
          url: '/skillshare/courses',
          icon: 'fa-solid fa-graduation-cap',
          btnClass: 'btn-info text-dark'
        });
      }

      // If recommendations returned
      if (data.recommendations && data.recommendations.length > 0) {
        replyHtml += '<div class="mt-2 border-top pt-2"><div class="fw-bold small text-muted mb-1">Recommended Matches:</div>';
        data.recommendations.slice(0, 3).forEach(item => {
          if (item.name) {
            replyHtml += `
              <div class="d-flex justify-content-between align-items-center py-1 border-bottom small">
                <div>
                  <strong>${escapeHtml(item.name)}</strong>
                  <div class="text-muted" style="font-size: 0.75rem;">⭐ ${item.rating || '5.0'} &bull; ${item.distance_km || 0.5} km away</div>
                </div>
                ${item.phone ? `<a href="tel:${item.phone}" class="btn btn-sm btn-outline-success py-0 px-2" style="font-size: 0.75rem;"><i class="fa-solid fa-phone"></i> Call</a>` : ''}
              </div>
            `;
          }
        });
        replyHtml += '</div>';
      }

      appendMessage('bot', replyHtml, true, actionButtons);
    })
    .catch(err => {
      console.error(err);
      const typingEl = document.getElementById('assistantTyping');
      if (typingEl) typingEl.remove();
      appendMessage('bot', "Sorry, I couldn't reach the assistant service right now. Please browse services or medicines from the main menu.");
    });
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  window.speakAssistantText = function (btnEl) {
    const parent = btnEl.closest('.bg-light');
    if (!parent) return;
    const textToSpeak = parent.querySelector('p')?.innerText || parent.innerText;
    if (window.readAloudText) {
      window.readAloudText(textToSpeak);
    } else if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(textToSpeak);
      window.speechSynthesis.speak(utterance);
    }
  };
});
