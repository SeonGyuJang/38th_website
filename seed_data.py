"""
임시 데이터 생성 스크립트
모든 기능을 테스트할 수 있도록 demo 데이터를 생성합니다.
"""

from app import app, db
from models import Schedule, Promise, PromiseProgress, MeetingMinutes, Regulation, Program, Organization, Banner, Admin
from datetime import datetime, timedelta
import random

def clear_all_data():
    """기존 데이터 모두 삭제 (Admin 제외)"""
    print("기존 데이터 삭제 중...")
    Banner.query.delete()
    PromiseProgress.query.delete()
    Promise.query.delete()
    Schedule.query.delete()
    MeetingMinutes.query.delete()
    Regulation.query.delete()
    Program.query.delete()
    Organization.query.delete()
    db.session.commit()
    print("✓ 기존 데이터 삭제 완료")

def create_schedules():
    """일정 데이터 생성"""
    print("\n일정 데이터 생성 중...")
    categories = ['회의', '행사', '프로젝트', '기타']
    schedules_data = [
        {
            'title': '정기 총학생회 회의',
            'description': '2월 정기 총학생회 회의입니다. 새학기 주요 안건을 논의합니다.',
            'start_date': datetime.now() + timedelta(days=3),
            'end_date': datetime.now() + timedelta(days=3, hours=2),
            'location': '학생회관 201호',
            'category': '회의'
        },
        {
            'title': '신입생 환영회',
            'description': '2025학년도 신입생을 환영하는 행사입니다.',
            'start_date': datetime.now() + timedelta(days=7),
            'end_date': datetime.now() + timedelta(days=7, hours=3),
            'location': '중앙광장',
            'category': '행사'
        },
        {
            'title': '학생복지 개선 프로젝트 회의',
            'description': '학생 복지 시설 개선을 위한 기획 회의',
            'start_date': datetime.now() + timedelta(days=10),
            'end_date': datetime.now() + timedelta(days=10, hours=2),
            'location': '학생회관 301호',
            'category': '프로젝트'
        },
        {
            'title': '중간고사 응원 이벤트',
            'description': '중간고사 기간 학우들을 위한 응원 이벤트',
            'start_date': datetime.now() + timedelta(days=14),
            'end_date': datetime.now() + timedelta(days=14, hours=4),
            'location': '중앙도서관 앞',
            'category': '행사'
        },
        {
            'title': '학생회 임원 워크샵',
            'description': '학생회 임원진 역량 강화 워크샵',
            'start_date': datetime.now() + timedelta(days=20),
            'end_date': datetime.now() + timedelta(days=21),
            'location': '세미나실',
            'category': '기타'
        },
        {
            'title': '총학생회 임시 회의',
            'description': '긴급 안건 논의를 위한 임시 회의',
            'start_date': datetime.now() - timedelta(days=5),
            'end_date': datetime.now() - timedelta(days=5, hours=-2),
            'location': '학생회관 201호',
            'category': '회의'
        },
    ]

    for data in schedules_data:
        schedule = Schedule(**data)
        db.session.add(schedule)

    db.session.commit()
    print(f"✓ {len(schedules_data)}개의 일정 생성 완료")

def create_promises():
    """공약 데이터 생성"""
    print("\n공약 데이터 생성 중...")

    promises_data = [
        # 학술 복지
        {
            'category': '학술 복지',
            'title': '24시간 스터디 카페 운영',
            'description': '학생들의 학습권 보장을 위한 24시간 스터디 공간 마련',
            'detailed_description': '중앙도서관 B1층을 리모델링하여 24시간 이용 가능한 스터디 카페를 조성합니다. 쾌적한 학습 환경을 위해 개인 좌석, 그룹 스터디룸, 무료 음료 제공 등을 계획하고 있습니다.',
            'progress_rate': 75,
            'status': '진행중',
            'order': 1
        },
        {
            'category': '학술 복지',
            'title': '전공 서적 대여 프로그램',
            'description': '고가의 전공 서적을 무료로 대여할 수 있는 프로그램 운영',
            'detailed_description': '학과별 주요 전공 서적을 구입하여 학생들에게 무료로 대여합니다. 온라인 예약 시스템을 통해 편리하게 이용할 수 있습니다.',
            'progress_rate': 60,
            'status': '진행중',
            'order': 2
        },
        {
            'category': '학술 복지',
            'title': '튜터링 프로그램 확대',
            'description': '선후배 간 학습 멘토링 프로그램 운영 및 확대',
            'detailed_description': '전공별 우수 선배가 후배들의 학습을 돕는 튜터링 프로그램을 운영합니다. 기존 10개 전공에서 25개 전공으로 확대 운영 예정입니다.',
            'progress_rate': 40,
            'status': '진행중',
            'order': 3
        },

        # 생활 복지
        {
            'category': '생활 복지',
            'title': '학식 메뉴 개선 및 가격 인하',
            'description': '학생 식당의 메뉴 다양화와 합리적인 가격 조정',
            'detailed_description': '학생들의 의견을 반영하여 학식 메뉴를 개선하고, 일부 메뉴의 가격을 인하합니다. 월 1회 스페셜 메뉴도 추가 운영합니다.',
            'progress_rate': 85,
            'status': '진행중',
            'order': 4
        },
        {
            'category': '생활 복지',
            'title': '기숙사 시설 개선',
            'description': '낡은 기숙사 시설 보수 및 편의시설 확충',
            'detailed_description': '기숙사 내부 시설을 전면 개보수하고, 세탁실 및 휴게 공간을 확충합니다. 학생들의 쾌적한 생활 환경을 보장합니다.',
            'progress_rate': 55,
            'status': '진행중',
            'order': 5
        },
        {
            'category': '생활 복지',
            'title': '무료 생리대 비치',
            'description': '여학생 화장실에 무료 생리대 비치',
            'detailed_description': '생리대 구입에 부담을 느끼는 학생들을 위해 주요 건물 여자 화장실에 무료 생리대를 비치합니다.',
            'progress_rate': 100,
            'status': '완료',
            'order': 6
        },

        # 문화 복지
        {
            'category': '문화 복지',
            'title': '교내 축제 확대 운영',
            'description': '다양한 문화 행사와 축제 기획 및 운영',
            'detailed_description': '봄/가을 대동제를 더욱 풍성하게 만들고, 소규모 문화 행사를 정기적으로 개최합니다. 학생들의 문화 향유권을 보장합니다.',
            'progress_rate': 70,
            'status': '진행중',
            'order': 7
        },
        {
            'category': '문화 복지',
            'title': '동아리 지원금 확대',
            'description': '학생 동아리 활동 활성화를 위한 지원금 증액',
            'detailed_description': '동아리 활동을 장려하기 위해 지원금을 30% 증액하고, 우수 동아리에 대한 추가 인센티브를 제공합니다.',
            'progress_rate': 90,
            'status': '진행중',
            'order': 8
        },
        {
            'category': '문화 복지',
            'title': '문화 공연 할인 티켓',
            'description': '뮤지컬, 콘서트 등 문화 공연 할인 티켓 제공',
            'detailed_description': '제휴를 통해 다양한 문화 공연을 학생 특별가로 관람할 수 있도록 합니다. 월 평균 10개 이상의 공연 정보를 제공합니다.',
            'progress_rate': 80,
            'status': '진행중',
            'order': 9
        },

        # 권익 증진
        {
            'category': '권익 증진',
            'title': '학생 의견 수렴 시스템 구축',
            'description': '온라인 플랫폼을 통한 학생 의견 실시간 수렴',
            'detailed_description': '모바일 앱과 웹사이트를 통해 학생들의 의견을 실시간으로 수렴하고, 투명하게 처리 과정을 공개합니다.',
            'progress_rate': 65,
            'status': '진행중',
            'order': 10
        },
        {
            'category': '권익 증진',
            'title': '학생 권리 상담소 운영',
            'description': '학생들의 권리 보호를 위한 전문 상담소 운영',
            'detailed_description': '학내 부당한 처우나 차별에 대한 상담 및 해결을 지원하는 전문 상담소를 운영합니다.',
            'progress_rate': 50,
            'status': '진행중',
            'order': 11
        },
        {
            'category': '권익 증진',
            'title': '장학금 확대 운영',
            'description': '교내 장학금 종류 및 수혜 인원 확대',
            'detailed_description': '경제적으로 어려운 학생들을 위한 다양한 장학금 프로그램을 신설하고, 기존 장학금의 수혜 인원을 50% 확대합니다.',
            'progress_rate': 45,
            'status': '진행중',
            'order': 12
        },

        # 취업 지원
        {
            'category': '취업 지원',
            'title': '취업 특강 및 멘토링',
            'description': '선배 및 전문가 초청 취업 특강과 멘토링 프로그램',
            'detailed_description': '각 분야 선배 및 전문가를 초청하여 취업 노하우를 공유하고, 1:1 멘토링을 진행합니다.',
            'progress_rate': 70,
            'status': '진행중',
            'order': 13
        },
        {
            'category': '취업 지원',
            'title': '이력서 사진 무료 촬영',
            'description': '전문 스튜디오 제휴를 통한 무료 증명사진 촬영',
            'detailed_description': '취업 준비생들을 위해 전문 스튜디오와 제휴하여 무료로 이력서 사진을 촬영할 수 있도록 지원합니다.',
            'progress_rate': 100,
            'status': '완료',
            'order': 14
        },
        {
            'category': '취업 지원',
            'title': '기업 탐방 프로그램',
            'description': '주요 기업 방문 및 채용 담당자 만남의 기회 제공',
            'detailed_description': '학기당 5개 이상의 주요 기업을 방문하여 기업 문화를 체험하고 채용 담당자와 만날 수 있는 기회를 제공합니다.',
            'progress_rate': 35,
            'status': '진행중',
            'order': 15
        },
    ]

    for data in promises_data:
        promise = Promise(**data)
        db.session.add(promise)

    db.session.commit()
    print(f"✓ {len(promises_data)}개의 공약 생성 완료")

    # 공약 진행 상황 업데이트 생성
    print("\n공약 진행 상황 업데이트 생성 중...")
    all_promises = Promise.query.all()
    progress_count = 0

    for promise in all_promises[:8]:  # 처음 8개 공약에만 진행상황 추가
        num_updates = random.randint(1, 3)
        for i in range(num_updates):
            progress = PromiseProgress(
                promise_id=promise.id,
                title=f"{promise.title} 진행 업데이트 {i+1}",
                content=f"현재까지 {promise.progress_rate}% 진행되었습니다. 주요 성과: {'예산 확보 완료' if i==0 else '실행 계획 수립' if i==1 else '일부 시범 운영'}",
                date=datetime.now() - timedelta(days=30*(i+1))
            )
            db.session.add(progress)
            progress_count += 1

    db.session.commit()
    print(f"✓ {progress_count}개의 공약 진행상황 생성 완료")

def create_meeting_minutes():
    """회의록 데이터 생성"""
    print("\n회의록 데이터 생성 중...")

    minutes_data = [
        {
            'title': '2025년 2월 정기 총학생회 회의',
            'meeting_type': '정기회의',
            'meeting_date': datetime.now() - timedelta(days=7),
            'attendees': '회장, 부회장, 기획국장, 재정국장, 홍보국장, 복지국장',
            'agenda': '1. 신입생 환영회 준비\n2. 학생복지 개선안 논의\n3. 1분기 예산 집행 현황 보고',
            'content': '1. 신입생 환영회는 3월 첫째 주에 진행하기로 결정\n2. 학생복지 개선안으로 24시간 스터디 카페 운영 추진\n3. 1분기 예산 집행률 65% 달성',
            'decisions': '- 신입생 환영회 예산 500만원 승인\n- 스터디 카페 설치 장소로 중앙도서관 B1층 확정\n- 홍보물 제작 업체 선정'
        },
        {
            'title': '학생복지위원회 임시 회의',
            'meeting_type': '임시회의',
            'meeting_date': datetime.now() - timedelta(days=14),
            'attendees': '부회장, 복지국장, 학생복지위원 5명',
            'agenda': '1. 학식 메뉴 개선안 논의\n2. 기숙사 시설 개선 요청사항 정리',
            'content': '학생들의 설문조사 결과를 바탕으로 학식 메뉴 개선안을 마련하고, 학교 측에 건의할 기숙사 시설 개선 요청사항을 정리함',
            'decisions': '- 학식 메뉴 개선안 학교 측에 공식 건의\n- 기숙사 시설 개선 예산 확보 요청'
        },
        {
            'title': '2024년 12월 정기 총학생회 회의',
            'meeting_type': '정기회의',
            'meeting_date': datetime.now() - timedelta(days=60),
            'attendees': '회장, 부회장, 각 국장 전원',
            'agenda': '1. 2024년 사업 결산\n2. 2025년 사업 계획 수립\n3. 겨울 방학 중 추진 사업 점검',
            'content': '2024년 한 해 동안의 주요 사업을 결산하고, 2025년 새로운 사업 계획을 수립함. 겨울 방학 중에도 지속적으로 추진할 사업들을 점검함',
            'decisions': '- 2024년 공약 이행률 78% 달성\n- 2025년 중점 사업 5개 선정\n- 방학 중 스터디 카페 설치 공사 진행'
        },
        {
            'title': '동아리연합회 간담회',
            'meeting_type': '간담회',
            'meeting_date': datetime.now() - timedelta(days=21),
            'attendees': '회장, 부회장, 동아리연합회장, 주요 동아리 대표 15명',
            'agenda': '1. 동아리 지원금 증액 건\n2. 동아리방 배정 문제\n3. 축제 참여 동아리 모집',
            'content': '동아리 활동 활성화를 위한 지원 방안을 논의하고, 동아리방 배정 및 관리 문제에 대한 해결책을 모색함',
            'decisions': '- 동아리 지원금 30% 증액 승인\n- 동아리방 신규 배정 기준 마련\n- 봄 축제 참여 동아리 20개팀 모집'
        },
        {
            'title': '학생권익위원회 정기회의',
            'meeting_type': '정기회의',
            'meeting_date': datetime.now() - timedelta(days=28),
            'attendees': '부회장, 권익국장, 학생권익위원 8명',
            'agenda': '1. 학생 의견 수렴 현황\n2. 권리 상담소 운영 계획\n3. 장학금 확대 방안',
            'content': '온라인 플랫폼을 통해 수렴된 학생 의견을 검토하고, 권리 상담소 운영 계획을 수립함. 장학금 확대를 위한 구체적인 방안을 논의함',
            'decisions': '- 학생 권리 상담소 3월부터 정식 운영\n- 장학금 수혜 인원 50% 확대 추진\n- 학생 의견 처리 프로세스 개선'
        },
    ]

    for data in minutes_data:
        minute = MeetingMinutes(**data)
        db.session.add(minute)

    db.session.commit()
    print(f"✓ {len(minutes_data)}개의 회의록 생성 완료")

def create_regulations():
    """회칙 데이터 생성"""
    print("\n회칙 데이터 생성 중...")

    regulations_data = [
        {
            'category': '총학생회',
            'title': '고려대학교 총학생회 회칙',
            'content': '제1장 총칙\n제1조(명칭) 본 회는 고려대학교 총학생회라 칭한다.\n제2조(목적) 본 회는 학생 복지 증진과 권익 향상을 목적으로 한다.\n\n제2장 조직\n제3조(구성) 본 회는 총학생회장, 부총학생회장 및 각 국으로 구성된다.',
            'order': 1
        },
        {
            'category': '총학생회',
            'title': '총학생회 선거 관리 규정',
            'content': '제1조(목적) 이 규정은 총학생회장 및 부총학생회장 선거의 공정한 관리를 목적으로 한다.\n제2조(선거권) 재학 중인 모든 학부생은 선거권을 가진다.\n제3조(피선거권) 선거일 기준 2학기 이상 재학한 학부생은 피선거권을 가진다.',
            'order': 2
        },
        {
            'category': '동아리연합회',
            'title': '동아리연합회 회칙',
            'content': '제1장 총칙\n제1조(명칭) 본 회는 고려대학교 동아리연합회라 칭한다.\n제2조(목적) 본 회는 교내 동아리의 건전한 발전과 회원 간 친목 도모를 목적으로 한다.',
            'order': 3
        },
        {
            'category': '동아리연합회',
            'title': '동아리 등록 및 관리 규정',
            'content': '제1조(등록 요건) 동아리로 등록하기 위해서는 10명 이상의 회원이 필요하다.\n제2조(지원금) 정식 등록된 동아리는 학기별 지원금을 신청할 수 있다.\n제3조(동아리방) 동아리방은 선착순 및 활동 실적을 고려하여 배정한다.',
            'order': 4
        },
        {
            'category': '학생복지위원회',
            'title': '학생복지위원회 운영 규정',
            'content': '제1조(목적) 학생들의 복지 증진을 위한 정책을 수립하고 집행한다.\n제2조(구성) 위원장 1명과 위원 10명 이내로 구성한다.\n제3조(회의) 정기회의는 월 1회 개최하며, 필요시 임시회의를 소집할 수 있다.',
            'order': 5
        },
    ]

    for data in regulations_data:
        regulation = Regulation(**data)
        db.session.add(regulation)

    db.session.commit()
    print(f"✓ {len(regulations_data)}개의 회칙 생성 완료")

def create_programs():
    """프로그램 데이터 생성"""
    print("\n프로그램 데이터 생성 중...")

    programs_data = [
        {
            'title': '글로벌 리더십 프로그램',
            'category': '학술',
            'description': '해외 대학과의 교류를 통한 글로벌 리더십 함양 프로그램입니다. 선발된 학생들은 2주간 해외 대학에서 특별 커리큘럼을 이수하게 됩니다.',
            'organizer': '국제교류원',
            'target': '전체 학부생',
            'start_date': datetime.now() + timedelta(days=60),
            'end_date': datetime.now() + timedelta(days=74),
            'application_start': datetime.now() + timedelta(days=5),
            'application_end': datetime.now() + timedelta(days=30),
            'location': '해외 파트너 대학',
            'link': 'https://example.com/global-leadership',
            'is_active': True
        },
        {
            'title': '스타트업 창업 캠프',
            'category': '취업',
            'description': '예비 창업가를 위한 3주간의 집중 창업 교육 프로그램입니다. 비즈니스 모델 수립부터 투자 유치까지 전 과정을 실습합니다.',
            'organizer': '창업지원단',
            'target': '창업에 관심있는 학생',
            'start_date': datetime.now() + timedelta(days=45),
            'end_date': datetime.now() + timedelta(days=66),
            'application_start': datetime.now() + timedelta(days=1),
            'application_end': datetime.now() + timedelta(days=25),
            'location': '창업보육센터',
            'link': 'https://example.com/startup-camp',
            'is_active': True
        },
        {
            'title': '여름 해외 봉사 프로그램',
            'category': '문화',
            'description': '동남아시아 지역 저개발 국가에서 2주간 봉사 활동을 진행하는 프로그램입니다.',
            'organizer': '사회봉사단',
            'target': '전체 학부생',
            'start_date': datetime.now() + timedelta(days=90),
            'end_date': datetime.now() + timedelta(days=104),
            'application_start': datetime.now() + timedelta(days=10),
            'application_end': datetime.now() + timedelta(days=40),
            'location': '동남아시아',
            'link': 'https://example.com/volunteer',
            'is_active': True
        },
        {
            'title': '코딩 부트캠프',
            'category': '학술',
            'description': 'Python, JavaScript 등 실무 프로그래밍 언어를 집중적으로 학습하는 4주 과정입니다.',
            'organizer': '정보대학',
            'target': '프로그래밍 초중급자',
            'start_date': datetime.now() + timedelta(days=30),
            'end_date': datetime.now() + timedelta(days=58),
            'application_start': datetime.now() - timedelta(days=5),
            'application_end': datetime.now() + timedelta(days=15),
            'location': '정보관 실습실',
            'link': 'https://example.com/coding-bootcamp',
            'is_active': True
        },
        {
            'title': '취업 멘토링 프로그램',
            'category': '취업',
            'description': '각 분야 선배 및 현직자와 1:1 멘토링을 진행하는 프로그램입니다. 이력서 첨삭, 면접 준비 등을 지원합니다.',
            'organizer': '취업지원센터',
            'target': '3, 4학년 재학생',
            'start_date': datetime.now() + timedelta(days=20),
            'end_date': datetime.now() + timedelta(days=80),
            'application_start': datetime.now(),
            'application_end': datetime.now() + timedelta(days=15),
            'location': '온라인 및 오프라인',
            'link': 'https://example.com/job-mentoring',
            'is_active': True
        },
    ]

    for data in programs_data:
        program = Program(**data)
        db.session.add(program)

    db.session.commit()
    print(f"✓ {len(programs_data)}개의 프로그램 생성 완료")

def create_organization():
    """조직도 데이터 생성"""
    print("\n조직도 데이터 생성 중...")

    organization_data = [
        # 회장단
        {'name': '김민수', 'position': '총학생회장', 'department': '회장단', 'major': '경영학과', 'student_id': '2021****', 'email': 'president@korea.ac.kr', 'phone': '010-****-****', 'order': 1},
        {'name': '이서연', 'position': '부총학생회장', 'department': '회장단', 'major': '경제학과', 'student_id': '2021****', 'email': 'vicepresident@korea.ac.kr', 'phone': '010-****-****', 'order': 2},

        # 본부 위원장
        {'name': '박지훈', 'position': '기획위원장', 'department': '본부', 'major': '행정학과', 'student_id': '2022****', 'email': 'planning@korea.ac.kr', 'phone': '010-****-****', 'order': 3},
        {'name': '최유진', 'position': '재정위원장', 'department': '본부', 'major': '회계학과', 'student_id': '2022****', 'email': 'finance@korea.ac.kr', 'phone': '010-****-****', 'order': 4},
        {'name': '정민재', 'position': '홍보위원장', 'department': '본부', 'major': '미디어학과', 'student_id': '2022****', 'email': 'pr@korea.ac.kr', 'phone': '010-****-****', 'order': 5},

        # 산하위원회 위원장
        {'name': '강현우', 'position': '복지위원장', 'department': '산하위원회', 'major': '사회학과', 'student_id': '2022****', 'email': 'welfare@korea.ac.kr', 'phone': '010-****-****', 'order': 6},
        {'name': '윤서희', 'position': '문화위원장', 'department': '산하위원회', 'major': '문화콘텐츠학과', 'student_id': '2022****', 'email': 'culture@korea.ac.kr', 'phone': '010-****-****', 'order': 7},
        {'name': '임동현', 'position': '권익위원장', 'department': '산하위원회', 'major': '법학과', 'student_id': '2022****', 'email': 'rights@korea.ac.kr', 'phone': '010-****-****', 'order': 8},

        # 기획국 국원
        {'name': '조은비', 'position': '국장', 'department': '기획국', 'major': '정치외교학과', 'student_id': '2023****', 'order': 9},
        {'name': '신태양', 'position': '차장', 'department': '기획국', 'major': '행정학과', 'student_id': '2023****', 'order': 10},

        # 재정국 국원
        {'name': '한지민', 'position': '국장', 'department': '재정국', 'major': '경제학과', 'student_id': '2023****', 'order': 11},
        {'name': '오성빈', 'position': '차장', 'department': '재정국', 'major': '경영학과', 'student_id': '2023****', 'order': 12},

        # 홍보국 국원
        {'name': '송민지', 'position': '국장', 'department': '홍보국', 'major': '신문방송학과', 'student_id': '2023****', 'order': 13},
        {'name': '배준혁', 'position': '차장', 'department': '홍보국', 'major': '미디어학과', 'student_id': '2023****', 'order': 14},

        # 복지국 국원
        {'name': '고은아', 'position': '국장', 'department': '복지국', 'major': '사회복지학과', 'student_id': '2023****', 'order': 15},
        {'name': '남궁찬', 'position': '차장', 'department': '복지국', 'major': '심리학과', 'student_id': '2023****', 'order': 16},
    ]

    for data in organization_data:
        member = Organization(**data)
        db.session.add(member)

    db.session.commit()
    print(f"✓ {len(organization_data)}명의 조직도 멤버 생성 완료")

def create_banners():
    """배너 데이터 생성"""
    print("\n배너 데이터 생성 중...")

    banners_data = [
        {
            'title': '2025 신입생 환영회',
            'image_url': '/static/images/banner1.jpg',
            'link': '/schedule',
            'is_active': True,
            'is_event_banner': True,
            'order': 1
        },
        {
            'title': '학생복지 설문조사',
            'image_url': '/static/images/banner2.jpg',
            'link': 'https://forms.gle/example',
            'is_active': True,
            'is_event_banner': False,
            'order': 2
        },
        {
            'title': '동아리 박람회',
            'image_url': '/static/images/banner3.jpg',
            'link': '/programs',
            'is_active': True,
            'is_event_banner': True,
            'order': 3
        },
    ]

    for data in banners_data:
        banner = Banner(**data)
        db.session.add(banner)

    db.session.commit()
    print(f"✓ {len(banners_data)}개의 배너 생성 완료")

def main():
    """메인 실행 함수"""
    with app.app_context():
        print("\n" + "="*60)
        print("고려대학교 38대 총학생회 - 임시 데이터 생성 스크립트")
        print("="*60)

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

        print("\n" + "="*60)
        print("✓ 모든 임시 데이터 생성 완료!")
        print("="*60)
        print("\n생성된 데이터:")
        print(f"  - 일정: {Schedule.query.count()}개")
        print(f"  - 공약: {Promise.query.count()}개")
        print(f"  - 공약 진행상황: {PromiseProgress.query.count()}개")
        print(f"  - 회의록: {MeetingMinutes.query.count()}개")
        print(f"  - 회칙: {Regulation.query.count()}개")
        print(f"  - 프로그램: {Program.query.count()}개")
        print(f"  - 조직도: {Organization.query.count()}명")
        print(f"  - 배너: {Banner.query.count()}개")
        print("\n관리자 계정으로 로그인하여 데이터를 확인하고 수정할 수 있습니다.")
        print("기본 관리자 계정: admin / admin\n")

if __name__ == '__main__':
    main()
