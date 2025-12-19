"""
SQLite에서 Supabase로 데이터 마이그레이션 스크립트

실행 전 준비사항:
1. Supabase 프로젝트 생성 및 스키마 생성 완료
2. .env 파일에 SUPABASE_URL, SUPABASE_KEY 설정
3. 기존 SQLite 데이터베이스 백업

실행 방법:
    python migrate_data.py
"""
import sqlite3
from datetime import datetime
from database import get_supabase_client


def migrate_table(sqlite_table: str, supabase_table: str, transform_fn=None):
    """
    SQLite 테이블 데이터를 Supabase로 마이그레이션

    Args:
        sqlite_table: SQLite 테이블 이름
        supabase_table: Supabase 테이블 이름
        transform_fn: 데이터 변환 함수 (선택사항)
    """
    supabase = get_supabase_client()

    # SQLite 연결
    try:
        conn = sqlite3.connect('student_council.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
    except Exception as e:
        print(f"❌ SQLite 연결 실패: {e}")
        return

    # 데이터 조회
    try:
        cursor.execute(f"SELECT * FROM {sqlite_table}")
        rows = cursor.fetchall()
    except Exception as e:
        print(f"❌ 테이블 조회 실패 ({sqlite_table}): {e}")
        conn.close()
        return

    print(f"\n{'='*60}")
    print(f"마이그레이션 중: {sqlite_table} -> {supabase_table}")
    print(f"레코드 수: {len(rows)}")
    print(f"{'='*60}")

    success_count = 0
    error_count = 0

    # 데이터 변환 및 삽입
    for idx, row in enumerate(rows, 1):
        data = dict(row)

        # ID 제거 (Supabase에서 자동 생성)
        if 'id' in data:
            del data['id']

        # 커스텀 변환 함수 적용
        if transform_fn:
            data = transform_fn(data)

        # datetime 변환
        for key, value in list(data.items()):
            if value and isinstance(value, str) and ('date' in key.lower() or key in ['created_at', 'updated_at']):
                try:
                    # SQLite datetime 형식을 ISO 형식으로 변환
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    data[key] = dt.isoformat()
                except:
                    pass

        # Supabase에 삽입
        try:
            supabase.table(supabase_table).insert(data).execute()
            success_count += 1
            print(f"  [{idx}/{len(rows)}] ✅ 성공", end='\r')
        except Exception as e:
            error_count += 1
            print(f"\n  ❌ 에러 (row {idx}): {e}")
            print(f"     데이터: {data}")

    conn.close()

    print(f"\n완료: {success_count} 성공, {error_count} 실패")


def main():
    """메인 마이그레이션 함수"""
    print("\n" + "="*60)
    print("SQLite → Supabase 데이터 마이그레이션")
    print("="*60)
    print("\n⚠️  경고: 이 작업은 기존 Supabase 데이터를 덮어씁니다.")
    confirm = input("계속하시겠습니까? (yes/no): ")

    if confirm.lower() != 'yes':
        print("마이그레이션 취소됨")
        return

    # Supabase 연결 테스트
    print("\nSupabase 연결 테스트 중...")
    supabase = get_supabase_client()
    try:
        supabase.table("admin").select("id").limit(1).execute()
        print("✅ Supabase 연결 성공\n")
    except Exception as e:
        print(f"❌ Supabase 연결 실패: {e}")
        return

    # SQLite 파일 존재 확인
    import os
    if not os.path.exists('student_council.db'):
        print("❌ student_council.db 파일을 찾을 수 없습니다.")
        return

    # 각 테이블 마이그레이션
    # 순서가 중요: 외래 키 참조가 있는 테이블은 나중에 처리
    tables = [
        ('admin', 'admin'),
        ('schedule', 'schedule'),
        ('promise', 'promise'),
        ('meeting_minutes', 'meeting_minutes'),
        ('regulation', 'regulation'),
        ('program', 'program'),
        ('organization', 'organization'),
        ('banner', 'banner'),
        ('archive', 'archive'),
    ]

    for sqlite_table, supabase_table in tables:
        migrate_table(sqlite_table, supabase_table)

    # 외래 키가 있는 테이블은 마지막에 처리
    foreign_key_tables = [
        ('promise_progress', 'promise_progress'),
        ('archive_image', 'archive_image'),
    ]

    for sqlite_table, supabase_table in foreign_key_tables:
        migrate_table(sqlite_table, supabase_table)

    print("\n" + "="*60)
    print("✅ 마이그레이션 완료!")
    print("="*60)
    print("\n다음 단계:")
    print("1. Supabase 대시보드에서 데이터 확인")
    print("2. 애플리케이션 테스트")
    print("3. 문제 없으면 SQLite 백업 보관")


if __name__ == "__main__":
    main()
