import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'grwm-super-secret-fashion-key-2026')
    DATABASE = os.path.join(basedir, 'database', 'grwm.db')
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    PROFILE_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'profiles')
    WARDROBE_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'wardrobe')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    TRYON_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'tryon_results')
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY', 'grwm-csrf-secret-key-2026')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
