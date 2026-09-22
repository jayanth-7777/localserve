import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'localserve-hyperlocal-secret-key-2026')
    DATABASE_PATH = os.path.join(BASE_DIR, 'localserve.db')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'prescriptions')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    
    # Community Reference Coordinates (Default: Local Town / Community Center)
    DEFAULT_LAT = 17.385044
    DEFAULT_LNG = 78.486671
    DEFAULT_RADIUS_KM = 15.0
