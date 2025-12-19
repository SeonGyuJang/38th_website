"""
Supabase 데이터베이스 클라이언트

이 모듈은 Supabase 클라이언트를 초기화하고 전역적으로 사용 가능하게 합니다.
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# Supabase 설정
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "SUPABASE_URL and SUPABASE_KEY must be set in environment variables.\n"
        "Please create a .env file with these variables."
    )

# Supabase 클라이언트 초기화
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_supabase_client() -> Client:
    """
    Supabase 클라이언트 인스턴스를 반환합니다.

    Returns:
        Client: Supabase 클라이언트 객체
    """
    return supabase


def test_connection() -> bool:
    """
    Supabase 연결을 테스트합니다.

    Returns:
        bool: 연결 성공 시 True, 실패 시 False
    """
    try:
        # 간단한 쿼리로 연결 테스트
        response = supabase.table("admin").select("id").limit(1).execute()
        print("✅ Supabase 연결 성공!")
        return True
    except Exception as e:
        print(f"❌ Supabase 연결 실패: {e}")
        return False


if __name__ == "__main__":
    # 직접 실행 시 연결 테스트
    test_connection()
