import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    APP_NAME = 'SevaSetu'
    APP_NAME_TELUGU = 'సేవాసేతు'
    SECRET_KEY = os.environ.get('SECRET_KEY', 'sevasetu-hyperlocal-secret-key-2026')
    DATABASE_PATH = os.path.join(BASE_DIR, 'localserve.db')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'prescriptions')
    PROBLEM_UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'problem_photos')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    
    # Community Reference Coordinates (Default: Gudlavalleru, PIN: 521356, Krishna District, AP)
    DEFAULT_LAT = 16.3486
    DEFAULT_LNG = 81.0442
    DEFAULT_RADIUS_KM = 25.0
    LOCATION_NAME = "Gudlavalleru"
    PINCODE = "521356"
    DISTRICT = "Krishna District, Andhra Pradesh"

    # Multi-Town Regional Service Coverage Hubs
    LOCATIONS = [
        {
            "id": "gudlavalleru",
            "name": "Gudlavalleru",
            "telugu_name": "గుడ్లవల్లేరు",
            "pincode": "521356",
            "lat": 16.3486,
            "lng": 81.0442,
            "badge": "Mandal & College Hub",
            "description": "SRGEC Campus & Panchayat Central Hub"
        },
        {
            "id": "gudivada",
            "name": "Gudivada",
            "telugu_name": "గుడివాడ",
            "pincode": "521301",
            "lat": 16.4410,
            "lng": 80.9926,
            "badge": "Commercial Center (12 km)",
            "description": "Major Market, RTC Depot & Railway Junction"
        },
        {
            "id": "machilipatnam",
            "name": "Machilipatnam",
            "telugu_name": "మచిలీపట్నం",
            "pincode": "521001",
            "lat": 16.1875,
            "lng": 81.1389,
            "badge": "District HQ (26 km)",
            "description": "District Hospital, Port Area & Govt Offices"
        }
    ]

