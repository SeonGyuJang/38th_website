"""
Flask-Login을 위한 Admin User 클래스

Supabase를 사용하면서 Flask-Login과 호환되도록 User 객체를 정의합니다.
"""
from flask_login import UserMixin
from config import Config


class AdminUser(UserMixin):
    """Flask-Login을 위한 Admin User 클래스"""

    def __init__(self, admin_data: dict):
        """
        Args:
            admin_data: Supabase에서 가져온 admin 데이터 딕셔너리
        """
        self.id = admin_data.get('id')
        self.username = admin_data.get('username')
        self.name = admin_data.get('name')
        self.password_hash = admin_data.get('password_hash')
        self.created_at = admin_data.get('created_at')
        is_super_admin = admin_data.get('is_super_admin', False)
        if isinstance(is_super_admin, str):
            is_super_admin = is_super_admin.strip().lower() in {'true', 't', '1', 'yes', 'y'}

        super_admin_usernames = {
            name.strip()
            for name in (Config.SUPER_ADMIN_USERNAMES or "").split(',')
            if name.strip()
        }
        self.is_super_admin = bool(is_super_admin) or (self.username in super_admin_usernames)

    def get_id(self):
        """Flask-Login이 사용하는 ID 반환"""
        return str(self.id)

    @property
    def is_authenticated(self):
        """사용자가 인증되었는지 여부"""
        return True

    @property
    def is_active(self):
        """사용자가 활성화되었는지 여부"""
        return True

    @property
    def is_anonymous(self):
        """익명 사용자인지 여부"""
        return False
