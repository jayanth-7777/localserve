// Multi-language Translation Engine (English, Telugu, Hindi)
const translations = {
  en: {
    app_title: "SevaSetu - Hyperlocal Essential Services & Medicine Availability",
    tagline: "Connecting Villages & Communities to Nearby Services and Verified Medicines",
    services: "Services",
    medicines: "Medicines",
    request_medicine: "Request Medicine",
    login: "Login",
    register: "Register",
    logout: "Logout",
    dashboard: "Dashboard",
    rural_mode: "Rural Easy Mode",
    standard_mode: "Standard Mode",
    detect_location: "Detect My Location",
    search_placeholder_service: "Search electrician, plumber, mechanic...",
    search_placeholder_medicine: "Search Paracetamol, ORS, Cetirizine...",
    within: "Within",
    all_categories: "All Services",
    call_now: "Call Directly",
    whatsapp: "WhatsApp",
    view_details: "View Details",
    book_now: "Book Service",
    listen: "Listen",
    emergency_title: "Village Emergency Helpline",
    emergency_ambulance: "Ambulance (108)",
    emergency_police: "Police (100)",
    status_available: "Available",
    status_low_stock: "Low Stock",
    status_unavailable: "Unavailable",
    reported_by_pharmacy: "Reported by pharmacy",
    need_unlisted_med: "Cannot find your medicine at nearby pharmacies?",
    request_availability_btn: "Request Medicine from Local Pharmacies",
    ratings: "Ratings",
    experience: "Years Experience",
    charges: "Visiting Charges",
    how_it_works: "How It Works",
    skillshare: "SkillShare",
    courses: "Vocational Courses",
    workshops: "Community Workshops",
    emergency: "Emergency Help"
  },
  te: {
    app_title: "లోకల్ సర్వ్ - నిత్యావసర సేవలు మరియు మందుల లభ్యత",
    tagline: "గ్రామాలు, కాలనీల ప్రజలకు దగ్గర్లోని సేవా నిపుణులు మరియు మెడికల్ షాపులు",
    services: "సేవలు",
    medicines: "మందుల సమాచారం",
    request_medicine: "మందును కోరండి",
    login: "లాగిన్",
    register: "ఖాతా తెరవండి",
    logout: "లాగౌట్",
    dashboard: "నా వివరాలు",
    rural_mode: "గ్రామీణ సులభ మోడ్",
    standard_mode: "సాధారణ మోడ్",
    detect_location: "📍 నా ఊరు / స్థానం గుర్తించు",
    search_placeholder_service: "ఎలక్ట్రీషియన్, ప్లంబర్, మెకానిక్...",
    search_placeholder_medicine: "పారాసిటమాల్, జ్వరం మందు, ఓ.ఆర్.ఎస్...",
    within: "పరిధి",
    all_categories: "అన్ని రకాల సేవలు",
    call_now: "📞 నేరుగా ఫోన్ చేయండి",
    whatsapp: "💬 వాట్సాప్",
    view_details: "వివరాలు చూడండి",
    book_now: "సేవను బుక్ చేయండి",
    listen: "🔊 వినండి",
    emergency_title: "గ్రామీణ అత్యవసర సహాయం",
    emergency_ambulance: "అంబులెన్స్ (108)",
    emergency_police: "పోలీస్ (100)",
    status_available: "మందు ఉంది",
    status_low_stock: "తక్కువ నిల్వ ఉంది",
    status_unavailable: "ప్రస్తుతం లేదు",
    reported_by_pharmacy: "మెడికల్ షాప్ ద్వారా తెలపబడినది",
    need_unlisted_med: "మీకు కావాల్సిన మందు మెడికల్ షాపుల్లో దొరకలేదా?",
    request_availability_btn: "దగ్గర్లోని మెడికల్ షాపుల నుండి మందును కోరండి",
    ratings: "రేటింగ్స్",
    experience: "ఏళ్ల అనుభవం",
    charges: "విజిటింగ్ ఛార్జీలు",
    how_it_works: "ఇది ఎలా పనిచేస్తుంది",
    skillshare: "నైపుణ్యాల శిక్షణ",
    courses: "వృత్తి విద్యా కోర్సులు",
    workshops: "గ్రామీణ వర్క్‌షాప్‌లు",
    emergency: "అత్యవసర సహాయం"
  },
  hi: {
    app_title: "लोकल सर्व - आवश्यक सेवाएं और दवा उपलब्धता",
    tagline: "गांवों और कस्बों को नजदीकी कारीगरों और मेडिकल स्टोर्स से जोड़ना",
    services: "सेवाएं",
    medicines: "दवाइयां",
    request_medicine: "दवा का अनुरोध करें",
    login: "लॉगिन",
    register: "नया खाता",
    logout: "लॉगआउट",
    dashboard: "डैशबोर्ड",
    rural_mode: "ग्रामीण सरल मोड",
    standard_mode: "सामान्य मोड",
    detect_location: "📍 मेरा स्थान खोजें",
    search_placeholder_service: "बिजली मिस्त्री, प्लंबर, मैकेनिक खोजें...",
    search_placeholder_medicine: "पैरासिटामोल, बुखार की दवा, ओआरएस...",
    within: "दूरी",
    all_categories: "सभी सेवाएं",
    call_now: "📞 सीधे फोन करें",
    whatsapp: "💬 व्हाट्सएप",
    view_details: "विवरण देखें",
    book_now: "बुक करें",
    listen: "🔊 सुनें",
    emergency_title: "आपातकालीन सहायता",
    emergency_ambulance: "एंबुलेंस (108)",
    emergency_police: "पुलिस (100)",
    status_available: "दवा उपलब्ध है",
    status_low_stock: "कम स्टॉक है",
    status_unavailable: "उपलब्ध नहीं है",
    reported_by_pharmacy: "मेडिकल स्टोर द्वारा सूचित",
    need_unlisted_med: "क्या आपकी जरूरत की दवा नजदीकी दुकानों पर नहीं मिली?",
    request_availability_btn: "नजदीकी मेडिकल स्टोर्स से दवा का अनुरोध करें",
    ratings: "रेटिंग",
    experience: "वर्षों का अनुभव",
    charges: "विजिट शुल्क",
    how_it_works: "यह कैसे काम करता है",
    skillshare: "कौशल प्रशिक्षण",
    courses: "व्यावसायिक पाठ्यक्रम",
    workshops: "सामुदायिक कार्यशाला",
    emergency: "आपातकालीन सहायता"
  }
};

let currentLang = localStorage.getItem('localserve_lang') || 'en';

function setLanguage(lang) {
  if (!translations[lang]) return;
  currentLang = lang;
  localStorage.setItem('localserve_lang', lang);
  
  // Update active state in UI buttons
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-lang') === lang);
  });

  applyTranslations();
}

function t(key) {
  if (translations[currentLang] && translations[currentLang][key]) {
    return translations[currentLang][key];
  }
  return translations['en'][key] || key;
}

function applyTranslations() {
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    const translation = t(key);
    if (translation) {
      if (el.tagName === 'INPUT' && el.getAttribute('placeholder')) {
        el.setAttribute('placeholder', translation);
      } else {
        el.innerText = translation;
      }
    }
  });

  // Also translate HTML lang attribute
  document.documentElement.lang = currentLang;
}

document.addEventListener('DOMContentLoaded', () => {
  setLanguage(currentLang);
});
