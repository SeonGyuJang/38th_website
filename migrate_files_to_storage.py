"""
로컬 파일을 Supabase Storage로 마이그레이션하는 스크립트

static/uploads 폴더의 모든 파일을 Supabase Storage로 업로드하고,
데이터베이스의 파일 URL을 업데이트합니다.
"""
import os
from database import get_supabase_admin_client
from storage_helper import storage
from config import Config


def migrate_files():
    """모든 로컬 파일을 Supabase Storage로 마이그레이션"""
    print("\n" + "="*60)
    print("로컬 파일 -> Supabase Storage 마이그레이션")
    print("="*60 + "\n")

    client = get_supabase_admin_client()
    uploads_dir = Config.UPLOAD_FOLDER

    if not os.path.exists(uploads_dir):
        print(f"⚠ 업로드 폴더가 없습니다: {uploads_dir}")
        return

    # 마이그레이션할 폴더와 대응하는 테이블
    migrations = {
        'banners': {'table': 'banners', 'field': 'image_url'},
        'regulations': {'table': 'regulations', 'field': 'file_url'},
        'archives': {'table': 'archive_images', 'field': 'image_url'},
        # 필요에 따라 추가
    }

    total_migrated = 0

    for subfolder, config in migrations.items():
        folder_path = os.path.join(uploads_dir, subfolder)

        if not os.path.exists(folder_path):
            print(f"⚠ 폴더가 없습니다: {subfolder}")
            continue

        print(f"\n📁 {subfolder} 폴더 마이그레이션 중...")

        # 폴더 내 모든 파일 처리
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)

            if not os.path.isfile(file_path):
                continue

            # Supabase Storage로 업로드
            public_url = storage.migrate_local_file(file_path, subfolder)

            if public_url:
                total_migrated += 1

                # 데이터베이스 업데이트
                old_url = f'/static/uploads/{subfolder}/{filename}'

                try:
                    # 기존 URL을 가진 레코드 찾기
                    table_name = config['table']
                    field_name = config['field']

                    # 레코드 조회
                    records = client.table(table_name).select('*').eq(field_name, old_url).execute()

                    if records.data:
                        # URL 업데이트
                        for record in records.data:
                            client.table(table_name).update({
                                field_name: public_url
                            }).eq('id', record['id']).execute()
                            print(f"  ✓ 데이터베이스 업데이트: {filename}")
                    else:
                        print(f"  ⚠ 데이터베이스에서 레코드를 찾을 수 없음: {filename}")

                except Exception as e:
                    print(f"  ❌ 데이터베이스 업데이트 오류 ({filename}): {e}")

    print("\n" + "="*60)
    print(f"✓ 마이그레이션 완료: 총 {total_migrated}개 파일")
    print("="*60 + "\n")


def verify_storage_bucket():
    """Supabase Storage 버킷 확인 및 생성"""
    print("\n버킷 확인 중...")

    try:
        client = get_supabase_admin_client()

        # 버킷 목록 조회
        buckets = client.storage.list_buckets()
        bucket_names = [b.name for b in buckets]

        if 'uploads' not in bucket_names:
            print("⚠ 'uploads' 버킷이 없습니다.")
            print("\nSupabase 대시보드에서 다음 단계를 수행해주세요:")
            print("1. Storage 섹션으로 이동")
            print("2. 'New bucket' 클릭")
            print("3. 버킷 이름: uploads")
            print("4. Public bucket 체크")
            print("5. Create bucket 클릭")
            return False
        else:
            print("✓ 'uploads' 버킷 확인 완료")
            return True

    except Exception as e:
        print(f"❌ 버킷 확인 오류: {e}")
        return False


def main():
    """메인 실행 함수"""
    if not verify_storage_bucket():
        print("\n먼저 Supabase 대시보드에서 버킷을 생성해주세요.")
        return

    print("\n로컬 파일을 Supabase Storage로 마이그레이션합니다.")
    response = input("계속하시겠습니까? (y/N): ")

    if response.lower() == 'y':
        migrate_files()
    else:
        print("마이그레이션이 취소되었습니다.")


if __name__ == '__main__':
    main()
