// Leaflet.js Interactive Hyperlocal Map

function initServiceMap(mapElementId, userLat, userLng, providers, pharmacies) {
  const mapContainer = document.getElementById(mapElementId);
  if (!mapContainer) return;

  const lat = parseFloat(userLat) || 16.3486;
  const lng = parseFloat(userLng) || 81.0442;

  const map = L.map(mapElementId).setView([lat, lng], 14);

  // OpenStreetMap Tile Layer
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 18
  }).addTo(map);

  // Custom Icon for User Location
  const userIcon = L.divIcon({
    className: 'custom-user-marker',
    html: `<div style="background-color: #2563eb; color: #fff; width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 3px solid #ffffff; box-shadow: 0 4px 10px rgba(0,0,0,0.3); font-size: 16px;"><i class="fa-solid fa-person-circle-check"></i></div>`,
    iconSize: [34, 34],
    iconAnchor: [17, 17]
  });

  const userMarker = L.marker([lat, lng], { icon: userIcon }).addTo(map);
  userMarker.bindPopup(`<b>Your Location</b><br>Searching within community radius.`).openPopup();

  const bounds = [[lat, lng]];

  // Add Provider Markers
  if (providers && providers.length) {
    providers.forEach(p => {
      if (p.latitude && p.longitude) {
        const pLat = parseFloat(p.latitude);
        const pLng = parseFloat(p.longitude);
        bounds.push([pLat, pLng]);

        const providerIcon = L.divIcon({
          className: 'custom-provider-marker',
          html: `<div style="background-color: #f97316; color: #fff; width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 3px solid #ffffff; box-shadow: 0 4px 10px rgba(0,0,0,0.3); font-size: 15px;"><i class="fa-solid ${p.icon || 'fa-wrench'}"></i></div>`,
          iconSize: [34, 34],
          iconAnchor: [17, 17]
        });

        const popupContent = `
          <div style="min-width: 180px;">
            <h6 style="margin: 0 0 4px 0; font-weight: 700;">${p.name}</h6>
            <div style="font-size: 0.85rem; color: #64748b; margin-bottom: 6px;">
              <i class="fa-solid fa-tag"></i> ${p.category} &bull; <b>₹${p.charges_per_hr}/hr</b>
            </div>
            <div style="font-size: 0.85rem; color: #0284c7; font-weight: 600; margin-bottom: 8px;">
              <i class="fa-solid fa-location-dot"></i> ${p.distance} km away
            </div>
            <div style="display: flex; gap: 6px;">
              <a href="tel:${p.phone}" class="btn btn-sm btn-success" style="flex: 1; padding: 4px; font-size: 0.8rem;">
                <i class="fa-solid fa-phone"></i> Call
              </a>
              <a href="/provider/${p.provider_id}" class="btn btn-sm btn-primary" style="flex: 1; padding: 4px; font-size: 0.8rem;">
                Book
              </a>
            </div>
          </div>
        `;

        L.marker([pLat, pLng], { icon: providerIcon }).addTo(map).bindPopup(popupContent);
      }
    });
  }

  // Add Pharmacy Markers
  if (pharmacies && pharmacies.length) {
    pharmacies.forEach(ph => {
      if (ph.latitude && ph.longitude) {
        const phLat = parseFloat(ph.latitude);
        const phLng = parseFloat(ph.longitude);
        bounds.push([phLat, phLng]);

        const pharmacyIcon = L.divIcon({
          className: 'custom-pharmacy-marker',
          html: `<div style="background-color: #10b981; color: #fff; width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 3px solid #ffffff; box-shadow: 0 4px 10px rgba(0,0,0,0.3); font-size: 15px;"><i class="fa-solid fa-prescription"></i></div>`,
          iconSize: [34, 34],
          iconAnchor: [17, 17]
        });

        const popupContent = `
          <div style="min-width: 180px;">
            <h6 style="margin: 0 0 4px 0; font-weight: 700; color: #047857;">${ph.name}</h6>
            <div style="font-size: 0.8rem; color: #64748b; margin-bottom: 4px;">
              <i class="fa-solid fa-clock"></i> ${ph.timings || '8:00 AM - 10:00 PM'}
            </div>
            <div style="font-size: 0.85rem; color: #0284c7; font-weight: 600; margin-bottom: 8px;">
              <i class="fa-solid fa-location-dot"></i> ${ph.distance || ''} km away
            </div>
            <a href="tel:${ph.phone}" class="btn btn-sm btn-success w-100" style="padding: 4px; font-size: 0.8rem;">
              <i class="fa-solid fa-phone"></i> Call Medical Store
            </a>
          </div>
        `;

        L.marker([phLat, phLng], { icon: pharmacyIcon }).addTo(map).bindPopup(popupContent);
      }
    });
  }

  // Fit bounds if multiple points
  if (bounds.length > 1) {
    map.fitBounds(bounds, { padding: [40, 40] });
  }

  return map;
}
