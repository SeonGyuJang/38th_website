import os
from datetime import timedelta

class Config:
    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Database configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///student_council.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

    # Upload folder configuration
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'hwp', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'zip'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

    # Ensure upload directories exist
    @staticmethod
    def init_app(app):
        # Create subdirectories for organized storage
        folders = ['files', 'images', 'profiles', 'minutes', 'regulations', 'programs', 'banners']
        for folder in folders:
            os.makedirs(os.path.join(Config.UPLOAD_FOLDER, folder), exist_ok=True)