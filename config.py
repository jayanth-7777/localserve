import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'localserve-hyperlocal-secret-key-2026')
    DATABASE_PATH = os.path.join(BASE_DIR, 'localserve.db')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'prescriptions')
    PROBLEM_UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'problem_photos')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    
    # Community Reference Coordinates (Default: Gudlavalleru, PIN: 521356, Krishna District, AP)
    DEFAULT_LAT = 16.3486
    DEFAULT_LNG = 81.0442
    DEFAULT_RADIUS_KM = 15.0
    LOCATION_NAME = "Gudlavalleru"
    PINCODE = "521356"
    DISTRICT = "Krishna District, Andhra Pradesh"
