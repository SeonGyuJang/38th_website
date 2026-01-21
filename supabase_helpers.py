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

    @staticmethod
    def parse_datetime(date_string: str) -> Optional[datetime]:
        """ISO 형식 문자열을 datetime 객체로 변환"""
        if not date_string:
            return None
        try:
            # ISO 형식 파싱 (Supabase에서 반환하는 형식)
            return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None

    def convert_schedule_dates(self, schedule: Dict[str, Any]) -> Dict[str, Any]:
        """일정 데이터의 날짜 문자열을 datetime 객체로 변환"""
        if schedule:
            if 'start_date' in schedule:
                schedule['start_date'] = self.parse_datetime(schedule['start_date'])
            if 'end_date' in schedule:
                schedule['end_date'] = self.parse_datetime(schedule['end_date'])
            if 'created_at' in schedule:
                schedule['created_at'] = self.parse_datetime(schedule['created_at'])
        return schedule

    def convert_meeting_dates(self, meeting: Dict[str, Any]) -> Dict[str, Any]:
        """회의록 데이터의 날짜 문자열을 datetime 객체로 변환"""
        if meeting:
            if 'meeting_date' in meeting:
                meeting['meeting_date'] = self.parse_datetime(meeting['meeting_date'])
            if 'created_at' in meeting:
                meeting['created_at'] = self.parse_datetime(meeting['created_at'])
        return meeting

    def convert_program_dates(self, program: Dict[str, Any]) -> Dict[str, Any]:
        """프로그램 데이터의 날짜 문자열을 datetime 객체로 변환"""
        if program:
            if 'start_date' in program:
                program['start_date'] = self.parse_datetime(program['start_date'])
            if 'end_date' in program:
                program['end_date'] = self.parse_datetime(program['end_date'])
            if 'application_start' in program:
                program['application_start'] = self.parse_datetime(program['application_start'])
            if 'application_end' in program:
                program['application_end'] = self.parse_datetime(program['application_end'])
            if 'created_at' in program:
                program['created_at'] = self.parse_datetime(program['created_at'])
        return program

    def convert_promise_progress_dates(self, progress: Dict[str, Any]) -> Dict[str, Any]:
        """공약 진행 상황 데이터의 날짜 문자열을 datetime 객체로 변환"""
        if progress:
            if 'date' in progress:
                progress['date'] = self.parse_datetime(progress['date'])
            if 'created_at' in progress:
                progress['created_at'] = self.parse_datetime(progress['created_at'])
        return progress

    def convert_archive_dates(self, archive: Dict[str, Any]) -> Dict[str, Any]:
        """아카이브 데이터의 날짜 문자열을 datetime 객체로 변환"""
        if archive:
            if 'event_date' in archive:
                archive['event_date'] = self.parse_datetime(archive['event_date'])
            if 'created_at' in archive:
                archive['created_at'] = self.parse_datetime(archive['created_at'])
            if 'updated_at' in archive:
                archive['updated_at'] = self.parse_datetime(archive['updated_at'])
        return archive

    def convert_history_dates(self, history: Dict[str, Any]) -> Dict[str, Any]:
        """히스토리 로그 데이터의 날짜 문자열을 datetime 객체로 변환"""
        if history:
            if 'created_at' in history:
                history['created_at'] = self.parse_datetime(history['created_at'])
            if 'checked_at' in history:
                history['checked_at'] = self.parse_datetime(history['checked_at'])
        return history

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
        return [self.convert_schedule_dates(schedule) for schedule in response.data]

    def get_upcoming_schedules(self, limit: int = 2) -> List[Dict[str, Any]]:
        """다가오는 일정 조회"""
        now = datetime.now().isoformat()
        response = self.client.table('schedules').select('*').gte('start_date', now).order('start_date').limit(limit).execute()
        return [self.convert_schedule_dates(schedule) for schedule in response.data]

    def get_schedule_by_id(self, schedule_id: int) -> Optional[Dict[str, Any]]:
        """ID로 일정 조회"""
        response = self.client.table('schedules').select('*').eq('id', schedule_id).execute()
        if response.data:
            return self.convert_schedule_dates(response.data[0])
        return None

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
        return [self.convert_promise_progress_dates(progress) for progress in response.data]

    def get_all_promise_progress(self) -> Dict[int, List[Dict[str, Any]]]:
        """모든 공약의 진행 상황을 한 번에 조회하여 promise_id로 그룹화 (N+1 쿼리 방지)"""
        response = self.client.table('promise_progress').select('*').order('date', desc=True).execute()

        # promise_id로 그룹화
        grouped = {}
        for progress in response.data:
            promise_id = progress['promise_id']
            if promise_id not in grouped:
                grouped[promise_id] = []
            grouped[promise_id].append(self.convert_promise_progress_dates(progress))

        return grouped

    def create_promise_progress(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """공약 진행 상황 생성"""
        response = self.client.table('promise_progress').insert(data).execute()
        return response.data[0] if response.data else None

    def get_promise_progress_by_id(self, progress_id: int) -> Optional[Dict[str, Any]]:
        """ID로 공약 진행 상황 조회"""
        response = self.client.table('promise_progress').select('*').eq('id', progress_id).execute()
        if response.data:
            return self.convert_promise_progress_dates(response.data[0])
        return None

    def update_promise_progress(self, progress_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """공약 진행 상황 수정"""
        response = self.client.table('promise_progress').update(data).eq('id', progress_id).execute()
        return response.data[0] if response.data else None

    def delete_promise_progress(self, progress_id: int) -> bool:
        """공약 진행 상황 삭제"""
        try:
            self.client.table('promise_progress').delete().eq('id', progress_id).execute()
            return True
        except Exception as e:
            print(f"Error deleting promise progress: {e}")
            return False

    # ============ MeetingMinutes 관련 ============
    def get_all_minutes(self, order_by: str = 'meeting_date', ascending: bool = False) -> List[Dict[str, Any]]:
        """모든 회의록 조회"""
        response = self.client.table('meeting_minutes').select('*').order(order_by, desc=not ascending).execute()
        return [self.convert_meeting_dates(meeting) for meeting in response.data]

    def get_recent_minutes(self, limit: int = 2) -> List[Dict[str, Any]]:
        """최근 회의록 조회"""
        response = self.client.table('meeting_minutes').select('*').order('meeting_date', desc=True).limit(limit).execute()
        return [self.convert_meeting_dates(meeting) for meeting in response.data]

    def get_minute_by_id(self, minute_id: int) -> Optional[Dict[str, Any]]:
        """ID로 회의록 조회"""
        response = self.client.table('meeting_minutes').select('*').eq('id', minute_id).execute()
        if response.data:
            return self.convert_meeting_dates(response.data[0])
        return None

    def create_minute(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """회의록 생성"""
        response = self.client.table('meeting_minutes').insert(data).execute()
        return response.data[0] if response.data else None

    def update_minute(self, minute_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """회의록 수정"""
        response = self.client.table('meeting_minutes').update(data).eq('id', minute_id).execute()
        return response.data[0] if response.data else None

    def delete_minute(self, minute_id: int) -> bool:
        """회의록 삭제 (파일 포함)"""
        # 삭제 전에 데이터 조회하여 파일 URL 확인
        minute = self.get_minute_by_id(minute_id)
        if minute and minute.get('file_url'):
            # 파일 삭제
            from storage_helper import storage
            storage.delete_file(minute['file_url'])

        # 데이터베이스에서 삭제
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
        """회칙 삭제 (파일 포함)"""
        # 삭제 전에 데이터 조회하여 파일 URL 확인
        regulation = self.get_regulation_by_id(regulation_id)
        if regulation and regulation.get('file_url'):
            # 파일 삭제
            from storage_helper import storage
            storage.delete_file(regulation['file_url'])

        # 데이터베이스에서 삭제
        response = self.client.table('regulations').delete().eq('id', regulation_id).execute()
        return len(response.data) > 0

    # ============ Program 관련 ============
    def get_all_programs(self, is_active: bool = True, order_by: str = 'created_at', ascending: bool = False) -> List[Dict[str, Any]]:
        """모든 프로그램 조회"""
        query = self.client.table('programs').select('*')
        if is_active is not None:
            query = query.eq('is_active', is_active)
        response = query.order(order_by, desc=not ascending).execute()
        return [self.convert_program_dates(program) for program in response.data]

    def get_program_by_id(self, program_id: int) -> Optional[Dict[str, Any]]:
        """ID로 프로그램 조회"""
        response = self.client.table('programs').select('*').eq('id', program_id).execute()
        if response.data:
            return self.convert_program_dates(response.data[0])
        return None

    def create_program(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """프로그램 생성"""
        response = self.client.table('programs').insert(data).execute()
        return response.data[0] if response.data else None

    def update_program(self, program_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """프로그램 수정"""
        response = self.client.table('programs').update(data).eq('id', program_id).execute()
        return response.data[0] if response.data else None

    def delete_program(self, program_id: int) -> bool:
        """프로그램 삭제 (이미지 포함)"""
        # 삭제 전에 데이터 조회하여 이미지 URL 확인
        program = self.get_program_by_id(program_id)
        if program and program.get('image_url'):
            # 이미지 삭제
            from storage_helper import storage
            storage.delete_file(program['image_url'])

        # 데이터베이스에서 삭제
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
        """조직도 멤버 삭제 (사진 포함)"""
        # 삭제 전에 데이터 조회하여 사진 URL 확인
        member = self.get_organization_by_id(member_id)
        if member and member.get('photo_url'):
            # 사진 삭제
            from storage_helper import storage
            storage.delete_file(member['photo_url'])

        # 데이터베이스에서 삭제
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
        """배너 삭제 (이미지 포함)"""
        # 삭제 전에 데이터 조회하여 이미지 URL 확인
        banner = self.get_banner_by_id(banner_id)
        if banner and banner.get('image_url'):
            # 이미지 삭제
            from storage_helper import storage
            storage.delete_file(banner['image_url'])

        # 데이터베이스에서 삭제
        response = self.client.table('banners').delete().eq('id', banner_id).execute()
        return len(response.data) > 0

    # ============ Archive 관련 ============
    def get_all_archives(self, is_active: bool = True, order_by: str = 'event_date', ascending: bool = False) -> List[Dict[str, Any]]:
        """모든 아카이브 조회"""
        query = self.client.table('archives').select('*')
        if is_active is not None:
            query = query.eq('is_active', is_active)
        response = query.order(order_by, desc=not ascending).execute()
        return [self.convert_archive_dates(archive) for archive in response.data]

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

        # 날짜 변환
        return self.convert_archive_dates(archive)

    def create_archive(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """아카이브 생성"""
        response = self.client.table('archives').insert(data).execute()
        return response.data[0] if response.data else None

    def update_archive(self, archive_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """아카이브 수정"""
        response = self.client.table('archives').update(data).eq('id', archive_id).execute()
        return response.data[0] if response.data else None

    def delete_archive(self, archive_id: int) -> bool:
        """아카이브 삭제 (연결된 모든 이미지 포함)"""
        # 삭제 전에 연결된 모든 이미지 조회 및 삭제
        images = self.client.table('archive_images').select('*').eq('archive_id', archive_id).execute()
        if images.data:
            from storage_helper import storage
            for image in images.data:
                if image.get('image_url'):
                    storage.delete_file(image['image_url'])
                # 이미지 레코드 삭제
                self.client.table('archive_images').delete().eq('id', image['id']).execute()

        # 아카이브 삭제
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
        """아카이브 이미지 삭제 (파일 포함)"""
        # 삭제 전에 데이터 조회하여 이미지 URL 확인
        image = self.get_archive_image_by_id(image_id)
        if image and image.get('image_url'):
            # 이미지 파일 삭제
            from storage_helper import storage
            storage.delete_file(image['image_url'])

        # 데이터베이스에서 삭제
        response = self.client.table('archive_images').delete().eq('id', image_id).execute()
        return len(response.data) > 0

    def get_archive_image_by_id(self, image_id: int) -> Optional[Dict[str, Any]]:
        """ID로 아카이브 이미지 조회"""
        response = self.client.table('archive_images').select('*').eq('id', image_id).execute()
        return response.data[0] if response.data else None

    # ============ HistoryLog 관련 ============
    def get_all_history_logs(self, order_by: str = 'created_at', ascending: bool = False) -> List[Dict[str, Any]]:
        """모든 히스토리 로그 조회"""
        response = self.client.table('history_logs').select('*').order(order_by, desc=not ascending).execute()
        return [self.convert_history_dates(history) for history in response.data]

    def get_history_log_by_id(self, log_id: int) -> Optional[Dict[str, Any]]:
        """ID로 히스토리 로그 조회"""
        response = self.client.table('history_logs').select('*').eq('id', log_id).execute()
        if response.data:
            return self.convert_history_dates(response.data[0])
        return None

    def create_history_log(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """히스토리 로그 생성"""
        response = self.client.table('history_logs').insert(data).execute()
        return response.data[0] if response.data else None

    def update_history_log(self, log_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """히스토리 로그 수정"""
        response = self.client.table('history_logs').update(data).eq('id', log_id).execute()
        return response.data[0] if response.data else None
