import os
from datetime import timedelta
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Supabase configuration
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
    SUPABASE_SERVICE_ROLE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    SUPER_ADMIN_USERNAMES = os.environ.get('SUPER_ADMIN_USERNAMES')

    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

    # Upload folder configuration
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')

    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'hwp', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'zip'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

    # Email configuration (SMTP)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', os.environ.get('MAIL_USERNAME'))
    ADMIN_EMAILS = [
        'hongwook5179@korea.ac.kr',
        'ekdus0510@korea.ac.kr',
        'rhajaejoon02@naver.com'
    ]
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'dsng3419@korea.ac.kr')

    # Ensure upload directories exist
    @staticmethod
    def init_app(app):
        # Create subdirectories for organized storage
        folders = ['files', 'images', 'profiles', 'minutes', 'regulations', 'programs', 'banners', 'archives']
        for folder in folders:
            os.makedirs(os.path.join(Config.UPLOAD_FOLDER, folder), exist_ok=True)
