// Main Application Scripts

// 1. Rural / Easy Mode Toggle
function toggleRuralMode() {
  const isRural = document.body.classList.toggle('rural-mode');
  localStorage.setItem('localserve_rural_mode', isRural ? 'true' : 'false');
  updateRuralToggleUI(isRural);

  // Audio confirmation
  const msg = isRural
    ? (currentLang === 'te' ? 'గ్రామీణ సులభ మోడ్ ఆన్ చేయబడింది. పెద్ద అక్షరాలు మరియు బొమ్మలు కనిపిస్తాయి.' : 'Rural Easy Mode activated. Large picture cards and voice support are enabled.')
    : (currentLang === 'te' ? 'సాధారణ మోడ్ ఆన్ చేయబడింది.' : 'Standard Mode activated.');
  speakText(msg, currentLang);
}

function updateRuralToggleUI(isRural) {
  const btn = document.getElementById('ruralModeToggleBtn');
  if (btn) {
    if (isRural) {
      btn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles"></i> <span data-i18n="standard_mode">Standard Mode</span>`;
      btn.classList.add('btn-warning');
      btn.classList.remove('btn-outline-warning');
    } else {
      btn.innerHTML = `<i class="fa-solid fa-people-roof"></i> <span data-i18n="rural_mode">Rural Easy Mode</span>`;
      btn.classList.add('btn-outline-warning');
      btn.classList.remove('btn-warning');
    }
  }
}

// 2. Geolocation Detector
function detectCurrentLocation() {
  if (!navigator.geolocation) {
    alert("Geolocation is not supported by your browser.");
    return;
  }

  const promptMsg = currentLang === 'te' ? 'మీ ప్రస్తుత స్థానాన్ని గుర్తిస్తున్నాము...' : 'Detecting your GPS location...';
  speakText(promptMsg, currentLang);

  navigator.geolocation.getCurrentPosition(
    (position) => {
      const lat = position.coords.latitude;
      const lng = position.coords.longitude;

      fetch('/api/set-location', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lat: lat, lng: lng })
      })
      .then(res => res.json())
      .then(data => {
        const successMsg = currentLang === 'te' ? 'మీ స్థానం విజయవంతంగా గుర్తించబడింది!' : 'Location updated successfully!';
        speakText(successMsg, currentLang);
        setTimeout(() => {
          // Append lat/lng to current query params and reload
          const url = new URL(window.location.href);
          url.searchParams.set('lat', lat);
          url.searchParams.set('lng', lng);
          window.location.href = url.toString();
        }, 800);
      });
    },
    (error) => {
      console.warn("GPS detection failed, fallback to default center:", error.message);
      const fallbackMsg = currentLang === 'te' ? 'జీపీఎస్ అనుమతి లభించలేదు. సాధారణ స్థానం ఉపయోగించబడుతోంది.' : 'Could not access GPS. Using default community center.';
      speakText(fallbackMsg, currentLang);
    },
    { timeout: 10000, enableHighAccuracy: true }
  );
}

// Document Ready Initialization
document.addEventListener('DOMContentLoaded', () => {
  // Check persisted rural mode preference (default ON on mobile or if previously chosen)
  const isMobile = window.innerWidth <= 768;
  const savedRural = localStorage.getItem('localserve_rural_mode');
  
  // Default to rural mode if first time on mobile or previously set to true
  if (savedRural === 'true' || (savedRural === null && isMobile)) {
    document.body.classList.add('rural-mode');
    updateRuralToggleUI(true);
  } else {
    updateRuralToggleUI(false);
  }

  // Bind speech buttons with data attributes
  document.querySelectorAll('.btn-speaker').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      readCardAloud(btn);
    });
  });
});
