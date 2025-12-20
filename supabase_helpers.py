"""
Supabase 헬퍼 함수

데이터베이스 작업을 간소화하는 유틸리티 함수들을 제공합니다.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from database import get_supabase_client, get_supabase_admin_client
from werkzeug.security import generate_password_hash, check_password_hash


class SupabaseHelper:
    """Supabase 데이터베이스 작업을 위한 헬퍼 클래스"""

    def __init__(self):
        self.client = get_supabase_client()
        self.admin_client = get_supabase_admin_client()

    # ============ Admin 관련 ============
    def get_admin_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """사용자명으로 관리자 조회"""
        response = self.admin_client.table('admins').select('*').eq('username', username).execute()
        return response.data[0] if response.data else None

    def check_admin_password(self, password_hash: str, password: str) -> bool:
        """관리자 비밀번호 확인"""
        return check_password_hash(password_hash, password)

    def create_admin(self, username: str, name: str, password: str) -> Optional[Dict[str, Any]]:
        """관리자 생성"""
        password_hash = generate_password_hash(password)
        data = {
            'username': username,
            'name': name,
            'password_hash': password_hash
        }
        response = self.admin_client.table('admins').insert(data).execute()
        return response.data[0] if response.data else None

    # ============ Schedule 관련 ============
    def get_all_schedules(self, order_by: str = 'start_date', ascending: bool = False) -> List[Dict[str, Any]]:
        """모든 일정 조회"""
        response = self.client.table('schedules').select('*').order(order_by, desc=not ascending).execute()
        return response.data

    def get_upcoming_schedules(self, limit: int = 2) -> List[Dict[str, Any]]:
        """다가오는 일정 조회"""
        now = datetime.now().isoformat()
        response = self.client.table('schedules').select('*').gte('start_date', now).order('start_date').limit(limit).execute()
        return response.data

    def get_schedule_by_id(self, schedule_id: int) -> Optional[Dict[str, Any]]:
        """ID로 일정 조회"""
        response = self.client.table('schedules').select('*').eq('id', schedule_id).execute()
        return response.data[0] if response.data else None

    def create_schedule(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """일정 생성"""
        response = self.client.table('schedules').insert(data).execute()
        return response.data[0] if response.data else None

    def update_schedule(self, schedule_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """일정 수정"""
        response = self.client.table('schedules').update(data).eq('id', schedule_id).execute()
        return response.data[0] if response.data else None

    def delete_schedule(self, schedule_id: int) -> bool:
        """일정 삭제"""
        response = self.client.table('schedules').delete().eq('id', schedule_id).execute()
        return len(response.data) > 0

    def count_schedules(self) -> int:
        """일정 개수 조회"""
        response = self.client.table('schedules').select('*', count='exact').execute()
        return response.count

    # ============ Promise 관련 ============
    def get_all_promises(self, order_by: str = 'order') -> List[Dict[str, Any]]:
        """모든 공약 조회"""
        response = self.client.table('promises').select('*').order(order_by).execute()
        return response.data

    def get_promise_by_id(self, promise_id: int) -> Optional[Dict[str, Any]]:
        """ID로 공약 조회"""
        response = self.client.table('promises').select('*').eq('id', promise_id).execute()
        return response.data[0] if response.data else None

    def create_promise(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """공약 생성"""
        response = self.client.table('promises').insert(data).execute()
        return response.data[0] if response.data else None

    def update_promise(self, promise_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """공약 수정"""
        response = self.client.table('promises').update(data).eq('id', promise_id).execute()
        return response.data[0] if response.data else None

    def delete_promise(self, promise_id: int) -> bool:
        """공약 삭제"""
        response = self.client.table('promises').delete().eq('id', promise_id).execute()
        return len(response.data) > 0

    def count_promises(self) -> int:
        """공약 개수 조회"""
        response = self.client.table('promises').select('*', count='exact').execute()
        return response.count

    # ============ PromiseProgress 관련 ============
    def get_promise_progress(self, promise_id: int) -> List[Dict[str, Any]]:
        """공약 진행 상황 조회"""
        response = self.client.table('promise_progress').select('*').eq('promise_id', promise_id).order('date', desc=True).execute()
        return response.data

    def create_promise_progress(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """공약 진행 상황 생성"""
        response = self.client.table('promise_progress').insert(data).execute()
        return response.data[0] if response.data else None

    # ============ MeetingMinutes 관련 ============
    def get_all_minutes(self, order_by: str = 'meeting_date', ascending: bool = False) -> List[Dict[str, Any]]:
        """모든 회의록 조회"""
        response = self.client.table('meeting_minutes').select('*').order(order_by, desc=not ascending).execute()
        return response.data

    def get_recent_minutes(self, limit: int = 2) -> List[Dict[str, Any]]:
        """최근 회의록 조회"""
        response = self.client.table('meeting_minutes').select('*').order('meeting_date', desc=True).limit(limit).execute()
        return response.data

    def get_minute_by_id(self, minute_id: int) -> Optional[Dict[str, Any]]:
        """ID로 회의록 조회"""
        response = self.client.table('meeting_minutes').select('*').eq('id', minute_id).execute()
        return response.data[0] if response.data else None

    def create_minute(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """회의록 생성"""
        response = self.client.table('meeting_minutes').insert(data).execute()
        return response.data[0] if response.data else None

    def update_minute(self, minute_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """회의록 수정"""
        response = self.client.table('meeting_minutes').update(data).eq('id', minute_id).execute()
        return response.data[0] if response.data else None

    def delete_minute(self, minute_id: int) -> bool:
        """회의록 삭제"""
        response = self.client.table('meeting_minutes').delete().eq('id', minute_id).execute()
        return len(response.data) > 0

    def count_minutes(self) -> int:
        """회의록 개수 조회"""
        response = self.client.table('meeting_minutes').select('*', count='exact').execute()
        return response.count

    # ============ Regulation 관련 ============
    def get_all_regulations(self, order_by: str = 'order') -> List[Dict[str, Any]]:
        """모든 회칙 조회"""
        response = self.client.table('regulations').select('*').order(order_by).execute()
        return response.data

    def get_regulation_by_id(self, regulation_id: int) -> Optional[Dict[str, Any]]:
        """ID로 회칙 조회"""
        response = self.client.table('regulations').select('*').eq('id', regulation_id).execute()
        return response.data[0] if response.data else None

    def create_regulation(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """회칙 생성"""
        response = self.client.table('regulations').insert(data).execute()
        return response.data[0] if response.data else None

    def update_regulation(self, regulation_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """회칙 수정"""
        response = self.client.table('regulations').update(data).eq('id', regulation_id).execute()
        return response.data[0] if response.data else None

    def delete_regulation(self, regulation_id: int) -> bool:
        """회칙 삭제"""
        response = self.client.table('regulations').delete().eq('id', regulation_id).execute()
        return len(response.data) > 0

    # ============ Program 관련 ============
    def get_all_programs(self, is_active: bool = True, order_by: str = 'created_at', ascending: bool = False) -> List[Dict[str, Any]]:
        """모든 프로그램 조회"""
        query = self.client.table('programs').select('*')
        if is_active is not None:
            query = query.eq('is_active', is_active)
        response = query.order(order_by, desc=not ascending).execute()
        return response.data

    def get_program_by_id(self, program_id: int) -> Optional[Dict[str, Any]]:
        """ID로 프로그램 조회"""
        response = self.client.table('programs').select('*').eq('id', program_id).execute()
        return response.data[0] if response.data else None

    def create_program(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """프로그램 생성"""
        response = self.client.table('programs').insert(data).execute()
        return response.data[0] if response.data else None

    def update_program(self, program_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """프로그램 수정"""
        response = self.client.table('programs').update(data).eq('id', program_id).execute()
        return response.data[0] if response.data else None

    def delete_program(self, program_id: int) -> bool:
        """프로그램 삭제"""
        response = self.client.table('programs').delete().eq('id', program_id).execute()
        return len(response.data) > 0

    def count_active_programs(self) -> int:
        """활성 프로그램 개수 조회"""
        response = self.client.table('programs').select('*', count='exact').eq('is_active', True).execute()
        return response.count

    # ============ Organization 관련 ============
    def get_all_organizations(self, order_by: str = 'order') -> List[Dict[str, Any]]:
        """모든 조직도 멤버 조회"""
        response = self.client.table('organizations').select('*').order(order_by).execute()
        return response.data

    def get_organizations_by_position(self, position_contains: str) -> List[Dict[str, Any]]:
        """직책으로 조직도 멤버 조회"""
        response = self.client.table('organizations').select('*').ilike('position', f'%{position_contains}%').order('order').execute()
        return response.data

    def get_organization_by_id(self, member_id: int) -> Optional[Dict[str, Any]]:
        """ID로 조직도 멤버 조회"""
        response = self.client.table('organizations').select('*').eq('id', member_id).execute()
        return response.data[0] if response.data else None

    def create_organization(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """조직도 멤버 생성"""
        response = self.client.table('organizations').insert(data).execute()
        return response.data[0] if response.data else None

    def update_organization(self, member_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """조직도 멤버 수정"""
        response = self.client.table('organizations').update(data).eq('id', member_id).execute()
        return response.data[0] if response.data else None

    def delete_organization(self, member_id: int) -> bool:
        """조직도 멤버 삭제"""
        response = self.client.table('organizations').delete().eq('id', member_id).execute()
        return len(response.data) > 0

    # ============ Banner 관련 ============
    def get_all_banners(self, is_active: bool = True, order_by: str = 'order') -> List[Dict[str, Any]]:
        """모든 배너 조회"""
        query = self.client.table('banners').select('*')
        if is_active is not None:
            query = query.eq('is_active', is_active)
        response = query.order('is_event_banner', desc=True).order(order_by).execute()
        return response.data

    def get_banner_by_id(self, banner_id: int) -> Optional[Dict[str, Any]]:
        """ID로 배너 조회"""
        response = self.client.table('banners').select('*').eq('id', banner_id).execute()
        return response.data[0] if response.data else None

    def create_banner(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """배너 생성"""
        response = self.client.table('banners').insert(data).execute()
        return response.data[0] if response.data else None

    def update_banner(self, banner_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """배너 수정"""
        response = self.client.table('banners').update(data).eq('id', banner_id).execute()
        return response.data[0] if response.data else None

    def delete_banner(self, banner_id: int) -> bool:
        """배너 삭제"""
        response = self.client.table('banners').delete().eq('id', banner_id).execute()
        return len(response.data) > 0

    # ============ Archive 관련 ============
    def get_all_archives(self, is_active: bool = True, order_by: str = 'event_date', ascending: bool = False) -> List[Dict[str, Any]]:
        """모든 아카이브 조회"""
        query = self.client.table('archives').select('*')
        if is_active is not None:
            query = query.eq('is_active', is_active)
        response = query.order(order_by, desc=not ascending).execute()
        return response.data

    def get_archive_by_id(self, archive_id: int) -> Optional[Dict[str, Any]]:
        """ID로 아카이브 조회 (이미지 포함)"""
        # 아카이브 정보 조회
        archive_response = self.client.table('archives').select('*').eq('id', archive_id).execute()
        if not archive_response.data:
            return None

        archive = archive_response.data[0]

        # 아카이브 이미지 조회
        images_response = self.client.table('archive_images').select('*').eq('archive_id', archive_id).order('order').execute()
        archive['images'] = images_response.data

        return archive

    def create_archive(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """아카이브 생성"""
        response = self.client.table('archives').insert(data).execute()
        return response.data[0] if response.data else None

    def update_archive(self, archive_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """아카이브 수정"""
        response = self.client.table('archives').update(data).eq('id', archive_id).execute()
        return response.data[0] if response.data else None

    def delete_archive(self, archive_id: int) -> bool:
        """아카이브 삭제"""
        response = self.client.table('archives').delete().eq('id', archive_id).execute()
        return len(response.data) > 0

    # ============ ArchiveImage 관련 ============
    def get_archive_images(self, archive_id: int) -> List[Dict[str, Any]]:
        """아카이브 이미지 조회"""
        response = self.client.table('archive_images').select('*').eq('archive_id', archive_id).order('order').execute()
        return response.data

    def create_archive_image(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """아카이브 이미지 생성"""
        response = self.client.table('archive_images').insert(data).execute()
        return response.data[0] if response.data else None

    def delete_archive_image(self, image_id: int) -> bool:
        """아카이브 이미지 삭제"""
        response = self.client.table('archive_images').delete().eq('id', image_id).execute()
        return len(response.data) > 0
