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
    MAX_CONTENT_LENGTH = 200 * 1024 * 1024  # 200MB max file size

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

    # PayAction (무통장입금 자동확인) 설정
    # https://payaction.app/developer 의 대시보드 > API 메뉴에서 발급받은 값을 사용합니다.
    PAYACTION_API_KEY = os.environ.get('PAYACTION_API_KEY')
    PAYACTION_MALL_ID = os.environ.get('PAYACTION_MALL_ID')
    PAYACTION_WEBHOOK_KEY = os.environ.get('PAYACTION_WEBHOOK_KEY')
    PAYACTION_BASE_URL = os.environ.get('PAYACTION_BASE_URL', 'https://api.payaction.app')

    # 버스 예약 무통장입금 계좌 정보 (결제 안내 화면에 표시)
    BUS_BANK_NAME = os.environ.get('BUS_BANK_NAME', '은행명 미설정')
    BUS_BANK_ACCOUNT_NUMBER = os.environ.get('BUS_BANK_ACCOUNT_NUMBER', '계좌번호 미설정')
    BUS_BANK_ACCOUNT_HOLDER = os.environ.get('BUS_BANK_ACCOUNT_HOLDER', '예금주 미설정')

    # Ensure upload directories exist
    @staticmethod
    def init_app(app):
        # Create subdirectories for organized storage
        folders = ['files', 'images', 'profiles', 'minutes', 'regulations', 'programs', 'banners', 'archives']
        for folder in folders:
            os.makedirs(os.path.join(Config.UPLOAD_FOLDER, folder), exist_ok=True)
