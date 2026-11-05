// SevaSetu Main Utilities & Interactivity

// 1. Rural Mode Toggle
function toggleRuralMode() {
  const body = document.body;
  const isRural = body.classList.toggle('rural-mode');
  localStorage.setItem('localserve_rural_mode', isRural ? 'true' : 'false');
  updateRuralToggleUI(isRural);
}

function updateRuralToggleUI(isRural) {
  const btn = document.getElementById('ruralModeToggleBtn');
  const btnMobile = document.getElementById('ruralModeToggleBtnMobile');

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

// 2. Geolocation Detector (Live GPS with 30 km Radius)
function detectCurrentLocation() {
  if (!navigator.geolocation) {
    alert("Geolocation is not supported by your browser.");
    return;
  }

  const promptMsg = currentLang === 'te' ? 'మీ ప్రస్తుత జీపీఎస్ స్థానాన్ని గుర్తిస్తున్నాము...' : 'Detecting your device GPS location...';
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
        const placeName = data.name || 'Your Location';
        const successMsg = currentLang === 'te' 
          ? `మీ స్థానం ${placeName} గా గుర్తించబడింది. 30 కిలోమీటర్ల పరిధిలో సేవలు చూపబడుతున్నాయి.` 
          : `Location set to ${placeName}. Showing verified services within 30 km radius.`;
        speakText(successMsg, currentLang);
        setTimeout(() => {
          const url = new URL(window.location.href);
          url.searchParams.set('lat', lat);
          url.searchParams.set('lng', lng);
          window.location.href = url.toString();
        }, 700);
      });
    },
    (error) => {
      console.warn("GPS detection failed, fallback to default center:", error.message);
      const fallbackMsg = currentLang === 'te' 
        ? 'జీపీఎస్ అనుమతి లభించలేదు. దయచేసి గ్రామం లేదా పిన్‌కోడ్ శోధించండి.' 
        : 'Could not access device GPS. Please search for your village, town or pincode.';
      speakText(fallbackMsg, currentLang);
    },
    { timeout: 10000, enableHighAccuracy: true }
  );
}

// 3. Universal Location Geocoding & Autocomplete
let geocodeSearchTimer = null;
function handleLocationSearch(query) {
  clearTimeout(geocodeSearchTimer);
  const resultsContainer = document.getElementById('locationSearchResults');
  if (!resultsContainer) return;

  const term = query.trim();
  if (term.length < 2) {
    resultsContainer.classList.add('d-none');
    resultsContainer.innerHTML = '';
    return;
  }

  geocodeSearchTimer = setTimeout(() => {
    resultsContainer.classList.remove('d-none');
    resultsContainer.innerHTML = '<div class="list-group-item text-muted small"><span class="spinner-border spinner-border-sm me-2 text-primary"></span> Searching locations across India...</div>';

    fetch(`/api/geocode?q=${encodeURIComponent(term)}`)
      .then(res => res.json())
      .then(data => {
        resultsContainer.innerHTML = '';
        if (data.results && data.results.length > 0) {
          data.results.forEach(loc => {
            const item = document.createElement('button');
            item.type = 'button';
            item.className = 'list-group-item list-group-item-action py-2 text-start';
            item.innerHTML = `
              <div class="d-flex justify-content-between align-items-center">
                <span class="fw-bold text-dark"><i class="fa-solid fa-location-dot text-danger me-2"></i>${loc.name}</span>
                <span class="badge bg-primary bg-opacity-10 text-primary small">30 km Radius</span>
              </div>
              <div class="text-muted small text-truncate">${loc.display_name}</div>
            `;
            item.onclick = () => selectUniversalLocation(loc);
            resultsContainer.appendChild(item);
          });
        } else {
          resultsContainer.innerHTML = '<div class="list-group-item text-muted small">No location matched. Try another village, city, or 6-digit PIN code.</div>';
        }
      })
      .catch(err => {
        resultsContainer.innerHTML = '<div class="list-group-item text-danger small">Error searching locations. Please try again.</div>';
      });
  }, 300);
}

function selectUniversalLocation(loc) {
  fetch('/api/set-location', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ lat: loc.lat, lng: loc.lng, name: loc.name })
  })
  .then(res => res.json())
  .then(data => {
    const successMsg = currentLang === 'te' 
      ? `${loc.name} స్థానంగా మార్చబడింది. 30 కి.మీ పరిధిలో సేవలు లోడ్ అవుతున్నాయి.` 
      : `Location changed to ${loc.name}. Loading verified services within 30 km radius.`;
    speakText(successMsg, currentLang);
    setTimeout(() => {
      const url = new URL(window.location.href);
      url.searchParams.set('lat', loc.lat);
      url.searchParams.set('lng', loc.lng);
      window.location.href = url.toString();
    }, 600);
  });
}

// Document Ready Initialization
document.addEventListener('DOMContentLoaded', () => {
  const isMobile = window.innerWidth <= 768;
  const savedRural = localStorage.getItem('localserve_rural_mode');
  
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
