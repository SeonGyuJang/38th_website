"""
Supabase Storage 헬퍼

파일 업로드, 다운로드, 삭제를 관리합니다.
"""
import os
from typing import Optional
from datetime import datetime
from werkzeug.utils import secure_filename
from database import get_supabase_admin_client
from config import Config


class SupabaseStorage:
    """Supabase Storage 작업을 위한 헬퍼 클래스"""

    def __init__(self):
        self.client = get_supabase_admin_client()
        self.bucket_name = 'uploads'  # Supabase에서 생성할 버킷 이름

    def _get_file_path(self, subfolder: str, filename: str) -> str:
        """파일 경로 생성"""
        return f"{subfolder}/{filename}"

    def upload_file(self, file, subfolder: str = 'files') -> Optional[str]:
        """
        파일을 Supabase Storage에 업로드

        Args:
            file: 업로드할 파일 객체
            subfolder: 저장할 하위 폴더 (files, images, banners 등)

        Returns:
            업로드된 파일의 공개 URL 또는 None
        """
        if not file:
            return None

        # 파일 확장자 검증
        if not self._allowed_file(file.filename):
            return None

        try:
            # 안전한 파일명 생성
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            unique_filename = timestamp + filename

            # 파일 경로
            file_path = self._get_file_path(subfolder, unique_filename)

            # 파일 읽기
            file_data = file.read()

            # Supabase Storage에 업로드
            response = self.client.storage.from_(self.bucket_name).upload(
                file_path,
                file_data,
                file_options={
                    "content-type": file.content_type or "application/octet-stream",
                    "x-upsert": "false"  # 덮어쓰기 방지
                }
            )

            # 공개 URL 생성
            public_url = self.client.storage.from_(self.bucket_name).get_public_url(file_path)
            return public_url

        except Exception as e:
            print(f"파일 업로드 오류: {e}")
            return None

    def delete_file(self, file_url: str) -> bool:
        """
        파일을 Supabase Storage에서 삭제

        Args:
            file_url: 삭제할 파일의 URL

        Returns:
            삭제 성공 여부
        """
        try:
            # URL에서 파일 경로 추출
            # 예: https://xxx.supabase.co/storage/v1/object/public/uploads/banners/file.png
            # -> banners/file.png
            if '/public/uploads/' in file_url:
                file_path = file_url.split('/public/uploads/')[-1]
            elif '/uploads/' in file_url:
                file_path = file_url.split('/uploads/')[-1]
            else:
                print(f"올바르지 않은 파일 URL: {file_url}")
                return False

            # Supabase Storage에서 삭제
            self.client.storage.from_(self.bucket_name).remove([file_path])
            return True

        except Exception as e:
            print(f"파일 삭제 오류: {e}")
            return False

    def get_public_url(self, file_path: str) -> str:
        """
        파일의 공개 URL 가져오기

        Args:
            file_path: 파일 경로 (예: banners/image.png)

        Returns:
            공개 URL
        """
        return self.client.storage.from_(self.bucket_name).get_public_url(file_path)

    def list_files(self, subfolder: str = '') -> list:
        """
        특정 폴더의 파일 목록 조회

        Args:
            subfolder: 조회할 하위 폴더

        Returns:
            파일 목록
        """
        try:
            response = self.client.storage.from_(self.bucket_name).list(subfolder)
            return response
        except Exception as e:
            print(f"파일 목록 조회 오류: {e}")
            return []

    @staticmethod
    def _allowed_file(filename: str) -> bool:
        """파일 확장자 검증"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

    def migrate_local_file(self, local_path: str, subfolder: str) -> Optional[str]:
        """
        로컬 파일을 Supabase Storage로 마이그레이션

        Args:
            local_path: 로컬 파일 경로
            subfolder: 저장할 하위 폴더

        Returns:
            업로드된 파일의 공개 URL 또는 None
        """
        try:
            if not os.path.exists(local_path):
                print(f"파일이 존재하지 않습니다: {local_path}")
                return None

            # 파일 읽기
            with open(local_path, 'rb') as f:
                file_data = f.read()

            # 파일명 추출
            filename = os.path.basename(local_path)
            file_path = self._get_file_path(subfolder, filename)

            # 파일 타입 추론
            file_ext = filename.rsplit('.', 1)[-1].lower()
            content_type_map = {
                'pdf': 'application/pdf',
                'png': 'image/png',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'gif': 'image/gif',
            }
            content_type = content_type_map.get(file_ext, 'application/octet-stream')

            # Supabase Storage에 업로드
            response = self.client.storage.from_(self.bucket_name).upload(
                file_path,
                file_data,
                file_options={
                    "content-type": content_type,
                    "x-upsert": "true"  # 이미 존재하면 덮어쓰기
                }
            )

            # 공개 URL 생성
            public_url = self.client.storage.from_(self.bucket_name).get_public_url(file_path)
            print(f"✓ 마이그레이션 완료: {filename} -> {public_url}")
            return public_url

        except Exception as e:
            print(f"파일 마이그레이션 오류 ({local_path}): {e}")
            return None


# 싱글톤 인스턴스
storage = SupabaseStorage()
