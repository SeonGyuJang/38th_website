"""
Supabase 데이터베이스 클라이언트

Supabase를 사용한 데이터베이스 연결 및 관리를 담당합니다.
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# 중요: .env 파일이 존재할 때만 로드합니다. 
# Heroku 서버에는 .env가 없어야 하며, 시스템 환경 변수(Config Vars)를 직접 사용하도록 합니다.
if os.path.exists('.env'):
    load_dotenv()

# Supabase 클라이언트 인스턴스 (싱글톤)
_supabase_client: Client = None
_supabase_admin_client: Client = None


def get_supabase_client() -> Client:
    """
    Supabase 클라이언트 인스턴스를 반환합니다. (anon key 사용)
    """
    global _supabase_client

    if _supabase_client is None:
        # os.getenv는 .env 파일이나 Heroku Config Vars에서 값을 가져옵니다.
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')

        # 디버깅용 로그 (Heroku logs --tail에서 확인 가능)
        # 보안을 위해 키의 앞부분 10자리만 출력합니다.
        if supabase_key:
            print(f"DEBUG: Supabase Key detected (Starts with: {supabase_key[:10]}...)")
        else:
            print("DEBUG: Supabase Key is missing!")

        if not supabase_url or not supabase_key:
            raise ValueError(
                "SUPABASE_URL과 SUPABASE_KEY 환경 변수가 설정되지 않았습니다. "
                "Heroku Config Vars 또는 로컬 .env 파일을 확인하세요."
            )

        # 실제 클라이언트 생성
        _supabase_client = create_client(supabase_url, supabase_key)

    return _supabase_client


def get_supabase_admin_client() -> Client:
    """
    Supabase 관리자 클라이언트 인스턴스를 반환합니다. (service_role key 사용)
    """
    global _supabase_admin_client

    if _supabase_admin_client is None:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

        if not supabase_url or not supabase_service_key:
            raise ValueError(
                "SUPABASE_URL과 SUPABASE_SERVICE_ROLE_KEY 환경 변수가 설정되지 않았습니다."
            )

        _supabase_admin_client = create_client(supabase_url, supabase_service_key)

    return _supabase_admin_client


def init_supabase(app=None):
    """
    Flask 앱과 함께 Supabase를 초기화합니다.
    """
    # 에러 발생 시 로그에 명확히 남기기 위해 try-except 사용
    try:
        client = get_supabase_client()
        admin_client = get_supabase_admin_client()

        if app:
            app.supabase = client
            app.supabase_admin = admin_client
        
        return client
    except Exception as e:
        print(f"CRITICAL ERROR: Supabase initialization failed - {str(e)}")
        raise e