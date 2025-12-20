"""
Supabase 데이터베이스 클라이언트

Supabase를 사용한 데이터베이스 연결 및 관리를 담당합니다.
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# Supabase 클라이언트 인스턴스 (싱글톤)
_supabase_client: Client = None
_supabase_admin_client: Client = None


def get_supabase_client() -> Client:
    """
    Supabase 클라이언트 인스턴스를 반환합니다. (anon key 사용)

    Returns:
        Client: Supabase 클라이언트 인스턴스

    Raises:
        ValueError: Supabase URL 또는 KEY가 설정되지 않은 경우
    """
    global _supabase_client

    if _supabase_client is None:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')

        if not supabase_url or not supabase_key:
            raise ValueError(
                "SUPABASE_URL과 SUPABASE_KEY 환경 변수가 설정되어야 합니다. "
                ".env 파일을 확인해주세요."
            )

        _supabase_client = create_client(supabase_url, supabase_key)

    return _supabase_client


def get_supabase_admin_client() -> Client:
    """
    Supabase 관리자 클라이언트 인스턴스를 반환합니다. (service_role key 사용)

    관리자 작업 (admins 테이블 CRUD 등)에 사용됩니다.

    Returns:
        Client: Supabase 관리자 클라이언트 인스턴스

    Raises:
        ValueError: Supabase URL 또는 SERVICE_ROLE_KEY가 설정되지 않은 경우
    """
    global _supabase_admin_client

    if _supabase_admin_client is None:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

        if not supabase_url or not supabase_service_key:
            raise ValueError(
                "SUPABASE_URL과 SUPABASE_SERVICE_ROLE_KEY 환경 변수가 설정되어야 합니다. "
                ".env 파일을 확인해주세요."
            )

        _supabase_admin_client = create_client(supabase_url, supabase_service_key)

    return _supabase_admin_client


def init_supabase(app=None):
    """
    Flask 앱과 함께 Supabase를 초기화합니다.

    Args:
        app: Flask 애플리케이션 인스턴스 (선택사항)
    """
    client = get_supabase_client()
    admin_client = get_supabase_admin_client()

    if app:
        # Flask 앱 컨텍스트에 Supabase 클라이언트 저장
        app.supabase = client
        app.supabase_admin = admin_client

    return client
