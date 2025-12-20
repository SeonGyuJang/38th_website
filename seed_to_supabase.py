"""
Supabase 데이터베이스에 seed 데이터를 삽입하는 스크립트

기존 seed_data.py의 데이터를 Supabase로 마이그레이션합니다.
"""

from database import get_supabase_admin_client
from datetime import datetime, timedelta
import random

def get_client():
    """Supabase 관리자 클라이언트 가져오기"""
    return get_supabase_admin_client()

def clear_all_data():
    """기존 데이터 모두 삭제 (Admin 제외)"""
    print("기존 데이터 삭제 중...")
    client = get_client()

    # 순서대로 삭제 (외래키 제약 고려)
    tables = [
        'archive_images',
        'archives',
        'banners',
        'organizations',
        'programs',
        'regulations',
        'meeting_minutes',
        'promise_progress',
        'promises',
        'schedules'
    ]

    for table in tables:
        try:
            client.table(table).delete().neq('id', 0).execute()
            print(f"  ✓ {table} 삭제 완료")
        except Exception as e:
            print(f"  ⚠ {table} 삭제 중 오류 (무시): {e}")

    print("✓ 기존 데이터 삭제 완료\n")

def create_schedules():
    """일정 데이터 생성"""
    print("일정 데이터 생성 중...")
    client = get_client()

    schedules_data = [
        {
            'title': '정기 총학생회 회의',
            'description': '2월 정기 총학생회 회의입니다. 새학기 주요 안건을 논의합니다.',
            'start_date': (datetime.now() + timedelta(days=3)).isoformat(),
            'end_date': (datetime.now() + timedelta(days=3, hours=2)).isoformat(),
            'location': '학생회관 201호',
            'category': '회의'
        },
        {
            'title': '신입생 환영회',
            'description': '2025학년도 신입생을 환영하는 행사입니다.',
            'start_date': (datetime.now() + timedelta(days=7)).isoformat(),
            'end_date': (datetime.now() + timedelta(days=7, hours=3)).isoformat(),
            'location': '중앙광장',
            'category': '행사'
        },
        {
            'title': '학생복지 개선 프로젝트 회의',
            'description': '학생 복지 시설 개선을 위한 기획 회의',
            'start_date': (datetime.now() + timedelta(days=10)).isoformat(),
            'end_date': (datetime.now() + timedelta(days=10, hours=2)).isoformat(),
            'location': '학생회관 301호',
            'category': '프로젝트'
        },
        {
            'title': '중간고사 응원 이벤트',
            'description': '중간고사 기간 학우들을 위한 응원 이벤트',
            'start_date': (datetime.now() + timedelta(days=14)).isoformat(),
            'end_date': (datetime.now() + timedelta(days=14, hours=4)).isoformat(),
            'location': '중앙도서관 앞',
            'category': '행사'
        },
        {
            'title': '학생회 임원 워크샵',
            'description': '학생회 임원진 역량 강화 워크샵',
            'start_date': (datetime.now() + timedelta(days=20)).isoformat(),
            'end_date': (datetime.now() + timedelta(days=21)).isoformat(),
            'location': '세미나실',
            'category': '기타'
        },
        {
            'title': '총학생회 임시 회의',
            'description': '긴급 안건 논의를 위한 임시 회의',
            'start_date': (datetime.now() - timedelta(days=5)).isoformat(),
            'end_date': (datetime.now() - timedelta(days=5, hours=-2)).isoformat(),
            'location': '학생회관 201호',
            'category': '회의'
        },
    ]

    result = client.table('schedules').insert(schedules_data).execute()
    print(f"✓ {len(result.data)}개의 일정 생성 완료\n")
    return result.data

def create_promises():
    """공약 데이터 생성"""
    print("공약 데이터 생성 중...")
    client = get_client()

    # 공약 데이터는 너무 많으므로 일부만 샘플로 추가
    promises_data = [
        {
            'category': '학술/복지',
            'title': '시험기간 패트롤 사업 운영',
            'description': '중간고사 및 기말고사 기간 패트롤 운영을 통해 학생 시험공부 편의 제공',
            'detailed_description': '1학기/2학기 중간고사와 기말고사 기간에 총학생회 인원이 학술정보원 패트롤을 운영하여 학생들의 시험 준비를 지원합니다.',
            'progress_rate': 50,
            'status': '진행중',
            'order': 1
        },
        {
            'category': '학술/복지',
            'title': '야간카페 운영',
            'description': '학술정보원 내 그라찌에 카페를 통한 야간카페 운영으로 학생 휴식 공간 제공',
            'detailed_description': '1학기/2학기 각각 중간고사와 기말고사 기간에 총학생회 인원이 야간카페를 운영합니다.',
            'progress_rate': 0,
            'status': '진행 예정',
            'order': 2
        },
        {
            'category': '시설/환경 개선',
            'title': '농심국제관 주변환경 개선',
            'description': '농심국제관 주변 환경을 쾌적하게 개선',
            'detailed_description': '농심국제관 주변의 노후된 시설과 환경을 전면 개선합니다.',
            'progress_rate': 0,
            'status': '진행 예정',
            'order': 8
        },
        {
            'category': '학생 참여/소통',
            'title': '소통 채널 활성화',
            'description': '학생회 활동 투명 공개 및 소통 채널 다양화',
            'detailed_description': '학생회 활동을 투명하게 공개하고, 다양한 소통 채널을 활성화합니다.',
            'progress_rate': 50,
            'status': '진행중',
            'order': 19
        },
    ]

    result = client.table('promises').insert(promises_data).execute()
    print(f"✓ {len(result.data)}개의 공약 생성 완료\n")

    # 공약 진행 상황 추가
    print("공약 진행 상황 생성 중...")
    progress_data = []
    for promise in result.data[:2]:  # 처음 2개만
        for i in range(2):
            progress_data.append({
                'promise_id': promise['id'],
                'title': f"{promise['title']} 진행 업데이트 {i+1}",
                'content': f"현재까지 {promise['progress_rate']}% 진행되었습니다.",
                'date': (datetime.now() - timedelta(days=30*(i+1))).isoformat()
            })

    if progress_data:
        progress_result = client.table('promise_progress').insert(progress_data).execute()
        print(f"✓ {len(progress_result.data)}개의 공약 진행상황 생성 완료\n")

    return result.data

def create_meeting_minutes():
    """회의록 데이터 생성"""
    print("회의록 데이터 생성 중...")
    client = get_client()

    minutes_data = [
        {
            'title': '2025년 2월 정기 총학생회 회의',
            'meeting_type': '정기회의',
            'meeting_date': (datetime.now() - timedelta(days=7)).isoformat(),
            'attendees': '회장, 부회장, 기획국장, 재정국장, 홍보국장, 복지국장',
            'agenda': '1. 신입생 환영회 준비\n2. 학생복지 개선안 논의\n3. 1분기 예산 집행 현황 보고',
            'content': '1. 신입생 환영회는 3월 첫째 주에 진행하기로 결정\n2. 학생복지 개선안으로 24시간 스터디 카페 운영 추진',
            'decisions': '- 신입생 환영회 예산 500만원 승인\n- 스터디 카페 설치 장소로 중앙도서관 B1층 확정'
        },
        {
            'title': '학생복지위원회 임시 회의',
            'meeting_type': '임시회의',
            'meeting_date': (datetime.now() - timedelta(days=14)).isoformat(),
            'attendees': '부회장, 복지국장, 학생복지위원 5명',
            'agenda': '1. 학식 메뉴 개선안 논의\n2. 기숙사 시설 개선 요청사항 정리',
            'content': '학생들의 설문조사 결과를 바탕으로 학식 메뉴 개선안을 마련함',
            'decisions': '- 학식 메뉴 개선안 학교 측에 공식 건의'
        },
    ]

    result = client.table('meeting_minutes').insert(minutes_data).execute()
    print(f"✓ {len(result.data)}개의 회의록 생성 완료\n")
    return result.data

def create_regulations():
    """회칙 데이터 생성"""
    print("회칙 데이터 생성 중...")
    client = get_client()

    regulations_data = [
        {
            'category': '총학생회',
            'title': '총학생회칙 및 세칙',
            'content': '고려대학교 세종캠퍼스 총학생회의 기본 회칙 및 세부 운영 세칙입니다.',
            'file_url': '/static/uploads/regulations/regulation_sejong_main.pdf',
            'order': 1
        },
        {
            'category': '총학생회',
            'title': '총학생회 일반규칙',
            'content': '총학생회의 일반적인 운영 규칙과 절차를 정의합니다.',
            'file_url': '/static/uploads/regulations/regulation_sejong_general_rules.pdf',
            'order': 2
        },
        {
            'category': '단과대학',
            'title': '과학기술대학 학생회칙',
            'content': '과학기술대학 학생회의 조직과 운영에 관한 회칙입니다.',
            'file_url': '/static/uploads/regulations/regulation_science_tech.pdf',
            'order': 4
        },
        {
            'category': '특별기구',
            'title': '총동아리연합회 학생회칙',
            'content': '총동아리연합회의 조직과 운영에 관한 회칙입니다.',
            'file_url': '/static/uploads/regulations/regulation_club_union.pdf',
            'order': 11
        },
    ]

    result = client.table('regulations').insert(regulations_data).execute()
    print(f"✓ {len(result.data)}개의 회칙 생성 완료\n")
    return result.data

def create_programs():
    """프로그램 데이터 생성"""
    print("프로그램 데이터 생성 중...")
    client = get_client()

    programs_data = [
        {
            'title': '글로벌 리더십 프로그램',
            'category': '학술',
            'description': '해외 대학과의 교류를 통한 글로벌 리더십 함양 프로그램입니다.',
            'organizer': '국제교류원',
            'target': '전체 학부생',
            'start_date': (datetime.now() + timedelta(days=60)).isoformat(),
            'end_date': (datetime.now() + timedelta(days=74)).isoformat(),
            'application_start': (datetime.now() + timedelta(days=5)).isoformat(),
            'application_end': (datetime.now() + timedelta(days=30)).isoformat(),
            'location': '해외 파트너 대학',
            'link': 'https://example.com/global-leadership',
            'is_active': True
        },
        {
            'title': '스타트업 창업 캠프',
            'category': '취업',
            'description': '예비 창업가를 위한 3주간의 집중 창업 교육 프로그램입니다.',
            'organizer': '창업지원단',
            'target': '창업에 관심있는 학생',
            'start_date': (datetime.now() + timedelta(days=45)).isoformat(),
            'end_date': (datetime.now() + timedelta(days=66)).isoformat(),
            'application_start': (datetime.now() + timedelta(days=1)).isoformat(),
            'application_end': (datetime.now() + timedelta(days=25)).isoformat(),
            'location': '창업보육센터',
            'is_active': True
        },
    ]

    result = client.table('programs').insert(programs_data).execute()
    print(f"✓ {len(result.data)}개의 프로그램 생성 완료\n")
    return result.data

def create_organization():
    """조직도 데이터 생성"""
    print("조직도 데이터 생성 중...")
    client = get_client()

    organization_data = [
        # 회장단
        {'name': '오미령', 'position': '총학생회장', 'department': '총학생회장단', 'major': '중국학전공21', 'student_id': '2021****', 'email': 'ryeong0310@korea.ac.kr', 'phone': '010-5453-8819', 'order': 1},
        {'name': '장선규', 'position': '부총학생회장', 'department': '총학생회장단', 'major': '디지털경영전공23', 'student_id': '2023390822', 'email': 'dsng3419@korea.ac.kr', 'phone': '010-6598-6414', 'order': 2},

        # 본부
        {'name': '이세민', 'position': '중앙집행위원장', 'department': '본부', 'major': '정부행정학부23', 'student_id': '2023****', 'email': 'marcia0012@korea.ac.kr', 'phone': '010-3682-1394', 'order': 3},
        {'name': '서가연', 'position': '기획정책위원장', 'department': '본부', 'major': '정부행정학부23', 'student_id': '2023****', 'email': 'sgy0120@korea.ac.kr', 'phone': '010-7139-1782', 'order': 4},

        # 미디어소통국
        {'name': '서종원', 'position': '국장', 'department': '중앙집행위원회 미디어소통국', 'major': '문화콘텐츠전공23', 'student_id': '2023400537', 'email': 'seoo0914@naver.com', 'phone': '010-4624-5404', 'order': 6},
        {'name': '김바다', 'position': '차장', 'department': '중앙집행위원회 미디어소통국', 'major': '융합경영학부25', 'student_id': '2025390625', 'email': 'bada1222@korea.ac.kr', 'phone': '010-7128-2842', 'order': 7},
    ]

    result = client.table('organizations').insert(organization_data).execute()
    print(f"✓ {len(result.data)}명의 조직도 멤버 생성 완료\n")
    return result.data

def create_banners():
    """배너 데이터 생성"""
    print("배너 데이터 생성 중...")
    client = get_client()

    banners_data = [
        {
            'title': '메인 배너 1',
            'image_url': '/static/uploads/banners/banner_1.png',
            'link': '',
            'is_active': True,
            'is_event_banner': True,
            'order': 1
        },
        {
            'title': '메인 배너 2',
            'image_url': '/static/uploads/banners/banner_2.png',
            'link': '',
            'is_active': True,
            'is_event_banner': False,
            'order': 2
        },
    ]

    result = client.table('banners').insert(banners_data).execute()
    print(f"✓ {len(result.data)}개의 배너 생성 완료\n")
    return result.data

def main():
    """메인 실행 함수"""
    print("\n" + "="*60)
    print("고려대학교 38대 총학생회 - Supabase 데이터 마이그레이션")
    print("="*60 + "\n")

    try:
        # 기존 데이터 삭제
        clear_all_data()

        # 각 카테고리별 데이터 생성
        create_schedules()
        create_promises()
        create_meeting_minutes()
        create_regulations()
        create_programs()
        create_organization()
        create_banners()

        print("="*60)
        print("✓ 모든 데이터 마이그레이션 완료!")
        print("="*60)

        # 생성된 데이터 개수 확인
        client = get_client()
        print("\n생성된 데이터:")
        tables = {
            'schedules': '일정',
            'promises': '공약',
            'promise_progress': '공약 진행상황',
            'meeting_minutes': '회의록',
            'regulations': '회칙',
            'programs': '프로그램',
            'organizations': '조직도',
            'banners': '배너'
        }

        for table, name in tables.items():
            try:
                count = len(client.table(table).select('id').execute().data)
                print(f"  - {name}: {count}개")
            except Exception as e:
                print(f"  - {name}: 조회 실패")

        print("\n관리자 페이지에서 데이터를 확인하고 수정할 수 있습니다.")
        print("기본 관리자 계정: admin / admin\n")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
