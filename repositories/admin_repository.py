"""
관리자(Admin) Repository
"""
from typing import Optional, Dict, Any
from werkzeug.security import generate_password_hash, check_password_hash
from .base_repository import BaseRepository


class AdminRepository(BaseRepository):
    """관리자 관련 데이터 접근 클래스"""

    def __init__(self):
        super().__init__("admin")

    def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        사용자명으로 관리자 조회

        Args:
            username: 사용자명

        Returns:
            Optional[Dict[str, Any]]: 관리자 정보 또는 None
        """
        response = (
            self.supabase.table(self.table)
            .select("*")
            .eq("username", username)
            .execute()
        )
        return response.data[0] if response.data else None

    def create_admin(self, username: str, password: str, name: str) -> Optional[Dict[str, Any]]:
        """
        관리자 생성 (비밀번호 해싱 포함)

        Args:
            username: 사용자명
            password: 비밀번호 (평문)
            name: 이름

        Returns:
            Optional[Dict[str, Any]]: 생성된 관리자 정보 또는 None
        """
        password_hash = generate_password_hash(password)
        data = {
            "username": username,
            "password_hash": password_hash,
            "name": name,
        }
        return self.create(data)

    def verify_password(self, admin: Dict[str, Any], password: str) -> bool:
        """
        비밀번호 검증

        Args:
            admin: 관리자 정보 딕셔너리
            password: 검증할 비밀번호 (평문)

        Returns:
            bool: 비밀번호 일치 여부
        """
        return check_password_hash(admin.get('password_hash', ''), password)

    def update_password(self, admin_id: int, new_password: str) -> Optional[Dict[str, Any]]:
        """
        비밀번호 변경

        Args:
            admin_id: 관리자 ID
            new_password: 새 비밀번호 (평문)

        Returns:
            Optional[Dict[str, Any]]: 수정된 관리자 정보 또는 None
        """
        password_hash = generate_password_hash(new_password)
        return self.update(admin_id, {"password_hash": password_hash})
