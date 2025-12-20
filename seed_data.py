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
        # 학술/복지 - 기존 총학 사업
        {
            'category': '학술/복지',
            'title': '패트롤 사업 운영 (교복)',
            'description': '중간/기말고사 기간 교복 패트롤 운영으로 학생 편의 제공',
            'detailed_description': '1학기/2학기 중간고사와 기말고사 기간에 교복이 패트롤을 운영하여 학생들의 시험 준비를 지원합니다. 총 4번의 패트롤 운영을 통해 학우들의 학습 환경을 개선합니다.',
            'progress_rate': 85,
            'status': '진행중',
            'order': 1
        },
        {
            'category': '학술/복지',
            'title': '야간카페 운영 (문기국)',
            'description': '문기국을 활용한 야간카페 운영으로 학생 휴식 공간 제공',
            'detailed_description': '1학기/2학기 각각 중간고사와 기말고사 기간에 문기국에서 야간카페를 운영합니다. 총 4번의 야간카페 운영을 통해 학생들의 휴식과 학습 균형을 지원합니다.',
            'progress_rate': 80,
            'status': '진행중',
            'order': 2
        },
        {
            'category': '학술/복지',
            'title': '귀향 버스 운영 (인복)',
            'description': '설날과 추석 귀향 버스 운영으로 학생 교통 편의 제공',
            'detailed_description': '인권복지국에서 주관하는 설날과 추석 귀향 버스 사업을 안정적으로 운영합니다. 학우들의 귀향 편의를 위해 안전하고 효율적인 교통 서비스를 제공합니다.',
            'progress_rate': 90,
            'status': '진행중',
            'order': 3
        },
        {
            'category': '학술/복지',
            'title': 'KU 멤버십 운영 (대협)',
            'description': '다양한 제휴 업체를 통한 학생 할인 서비스 제공',
            'detailed_description': '대외협력국에서 운영하는 KU 멤버십을 통해 학우들이 다양한 제휴 업체에서 할인 혜택을 받을 수 있도록 합니다. 학생들의 경제적 부담을 줄이고 실질적인 복지를 제공합니다.',
            'progress_rate': 75,
            'status': '진행중',
            'order': 4
        },
        {
            'category': '학술/복지',
            'title': '상주 및 물품대여사업 운영',
            'description': '총학생회 사무국을 통한 상주 업무와 물품 대여 서비스 제공',
            'detailed_description': '총학생회 사무국에서 상주 업무를 수행하며, 농심국제관 홍보물 관리와 물품 대여사업을 운영합니다. 학우들의 일상생활 편의를 위한 다양한 물품을 대여할 수 있습니다.',
            'progress_rate': 70,
            'status': '진행중',
            'order': 5
        },
        {
            'category': '학술/복지',
            'title': '편입생 간담회 개최 (교복)',
            'description': '편입생들을 위한 간담회 운영으로 학교 적응 지원',
            'detailed_description': '교복에서 편입생 간담회를 개최하여 새로 입학한 편입생들의 학교 생활 적응을 돕습니다. 선배들의 경험 공유와 유용한 정보 제공을 통해 원활한 학교 생활을 지원합니다.',
            'progress_rate': 60,
            'status': '진행중',
            'order': 6
        },
        {
            'category': '학술/복지',
            'title': '정기 행사 운영',
            'description': '다양한 학내 정기 행사 기획 및 운영',
            'detailed_description': '1학기: 전간수, 새터, 세종응원OT, 합동응원OT, 4.18, 대동제, 입실렌티 / 2학기: 응원OT, 고연전 등 다양한 정기 행사를 성공적으로 운영하여 학우들의 문화 생활을 풍성하게 합니다.',
            'progress_rate': 65,
            'status': '진행중',
            'order': 7
        },

        # 시설/환경 개선 - 핵심공약 및 시설 관련
        {
            'category': '시설/환경 개선',
            'title': '농심국제관 주변환경 개선',
            'description': '농심국제관 주변 환경을 쾌적하게 개선',
            'detailed_description': '농심국제관 주변의 노후된 시설과 환경을 전면 개선합니다. 학생들의 학습과 휴식 공간으로서의 기능을 강화하고 쾌적한 환경을 조성합니다.',
            'progress_rate': 40,
            'status': '진행중',
            'order': 8
        },
        {
            'category': '시설/환경 개선',
            'title': '학술정보원 주변환경 개선',
            'description': '학술정보원 주변 환경 정비 및 개선',
            'detailed_description': '학술정보원 주변의 시설과 환경을 개선하여 학생들의 학습 공간으로서의 가치를 높입니다. 접근성 향상과 편의시설 확충을 통해 더 나은 학습 환경을 제공합니다.',
            'progress_rate': 35,
            'status': '진행중',
            'order': 9
        },
        {
            'category': '시설/환경 개선',
            'title': '교내 캠퍼스맵 설치',
            'description': '교내 주요 시설 안내를 위한 캠퍼스맵 설치',
            'detailed_description': '학교 내 주요 시설과 길찾기를 돕는 캠퍼스맵을 전략적 위치에 설치합니다. 특히 신입생과 외부 방문객들이 쉽게 학교를 둘러볼 수 있도록 지원합니다.',
            'progress_rate': 55,
            'status': '진행중',
            'order': 10
        },
        {
            'category': '시설/환경 개선',
            'title': '화장실 불법 촬영 전수조사',
            'description': '캠퍼스 내 전체 화장실 불법 촬영 카메라 설치 여부 조사',
            'detailed_description': '학생들의 안전을 위해 캠퍼스 내 모든 화장실에 대한 불법 촬영 카메라 설치 여부를 전수조사합니다. 발견 시 즉각적인 조치와 예방 시스템을 구축합니다.',
            'progress_rate': 25,
            'status': '진행중',
            'order': 11
        },
        {
            'category': '시설/환경 개선',
            'title': '소방 시설 점검',
            'description': '캠퍼스 내 전체 소방 시설 정기 점검 및 유지보수',
            'detailed_description': '화재 예방과 학생 안전을 위해 캠퍼스 내 모든 소방 시설을 정기적으로 점검합니다. 노후된 설비 교체와 유지보수를 통해 안전한 학교 환경을 조성합니다.',
            'progress_rate': 70,
            'status': '진행중',
            'order': 12
        },
        {
            'category': '시설/환경 개선',
            'title': 'AED 설치 및 안내',
            'description': '교내 주요 장소에 자동심장충격기 설치 및 안내 시스템 구축',
            'detailed_description': '응급상황 발생 시 신속한 대응을 위해 교내 주요 장소에 AED를 설치하고, 사용법 교육과 위치 안내 시스템을 구축합니다.',
            'progress_rate': 45,
            'status': '진행중',
            'order': 13
        },
        {
            'category': '시설/환경 개선',
            'title': '흡연 구역 재정비 및 클린 캠페인',
            'description': '흡연 구역 재정비와 캠퍼스 청결 유지 캠페인 실시',
            'detailed_description': '흡연 구역을 체계적으로 재정비하고, 클린 캠페인을 통해 캠퍼스 청결을 유지합니다. 특히 시험기간 담배꽁초 투표를 통해 학생 의견을 수렴합니다.',
            'progress_rate': 60,
            'status': '진행중',
            'order': 14
        },
        {
            'category': '시설/환경 개선',
            'title': '교내 청결 유지 시스템 강화',
            'description': '교내 청결 유지와 환경 개선 시스템 구축',
            'detailed_description': '교내 청결을 위한 시스템을 강화하고, 학생 참여를 유도하는 다양한 프로그램을 운영합니다. 깨끗하고 쾌적한 캠퍼스 환경 조성을 목표로 합니다.',
            'progress_rate': 50,
            'status': '진행중',
            'order': 15
        },

        # 학생 참여/소통
        {
            'category': '학생 참여/소통',
            'title': '부총장 토크 콘서트 개최',
            'description': '부총장과의 소통을 위한 토크 콘서트 및 간담회 개최',
            'detailed_description': '학생들과 부총장 간의 소통 강화를 위해 정기적인 토크 콘서트와 간담회를 개최합니다. 학생들의 의견을 직접 청취하고 학교 발전 방향을 논의합니다.',
            'progress_rate': 30,
            'status': '진행중',
            'order': 16
        },
        {
            'category': '학생 참여/소통',
            'title': '세종캠퍼스 총학생회칙 전면 개정',
            'description': '세종캠퍼스 총학생회칙의 전면 개정 작업 추진',
            'detailed_description': '세종캠퍼스 학생들의 의견을 반영하여 총학생회칙을 전면 개정합니다. 더 민주적이고 효율적인 학생자치 시스템을 구축합니다.',
            'progress_rate': 20,
            'status': '진행중',
            'order': 17
        },
        {
            'category': '학생 참여/소통',
            'title': '학생 수렴형 전체학생대표자회의',
            'description': '학생들의 의견을 적극 수렴하는 전체학생대표자회의 운영',
            'detailed_description': '학생 대표자들이 참여하는 회의를 통해 다양한 학생 의견을 수렴하고, 학교 정책 결정 과정에 반영합니다. 투명하고 민주적인 의사결정 시스템을 구축합니다.',
            'progress_rate': 40,
            'status': '진행중',
            'order': 18
        },
        {
            'category': '학생 참여/소통',
            'title': '소통 채널 활성화',
            'description': '학생회 활동 투명 공개 및 소통 채널 다양화',
            'detailed_description': '학생회 활동을 투명하게 공개하고, 다양한 소통 채널을 활성화합니다. SNS, 앱, 웹사이트 등을 통해 실시간 소통을 강화합니다.',
            'progress_rate': 75,
            'status': '진행중',
            'order': 19
        },
        {
            'category': '학생 참여/소통',
            'title': '학생회관 TF팀 운영',
            'description': '학생회관 개선을 위한 태스크포스팀 구성 및 운영',
            'detailed_description': '학생회관의 효율적 운영과 개선을 위해 TF팀을 구성합니다. 학생들의 의견을 수렴하여 실질적인 개선 방안을 마련하고 실행합니다.',
            'progress_rate': 35,
            'status': '진행중',
            'order': 20
        },

        # 행사/프로그램
        {
            'category': '행사/프로그램',
            'title': '연합 취업박람회 개최',
            'description': '고려대학교 연합 취업박람회 기획 및 운영',
            'detailed_description': '다양한 기업들이 참여하는 연합 취업박람회를 개최하여 학생들의 취업 기회를 확대합니다. 기업 설명회, 면접 코칭, 네트워킹 프로그램을 운영합니다.',
            'progress_rate': 45,
            'status': '진행중',
            'order': 21
        },
        {
            'category': '행사/프로그램',
            'title': '예비군 이벤트 진행',
            'description': '예비군 대상 다양한 이벤트 및 프로그램 운영',
            'detailed_description': '예비군들의 사기 진작과 복지 향상을 위해 다양한 이벤트와 프로그램을 기획합니다. 문화 행사, 건강 프로그램, 휴식 공간 제공 등을 운영합니다.',
            'progress_rate': 55,
            'status': '진행중',
            'order': 22
        },
        {
            'category': '행사/프로그램',
            'title': '연합 사회봉사 추진',
            'description': '고려대학교 연합 사회봉사 프로그램 기획 및 운영',
            'detailed_description': '다양한 사회봉사 프로그램을 기획하여 학생들의 사회적 책임감을 높이고, 지역사회와의 유대를 강화합니다. 정기적인 봉사 활동을 통해 나눔 문화를 확산합니다.',
            'progress_rate': 50,
            'status': '진행중',
            'order': 23
        },
        {
            'category': '행사/프로그램',
            'title': '교내 프로그램 정보 통합 제공',
            'description': '공모전, 교내대회 등 교내 프로그램 정보 통합 시스템 구축',
            'detailed_description': '다양한 공모전, 교내대회, 프로그램 정보를 한 곳에서 확인할 수 있는 통합 시스템을 구축합니다. 학생들의 참여 기회를 확대하고 정보 접근성을 향상합니다.',
            'progress_rate': 65,
            'status': '진행중',
            'order': 24
        },

        # 편의/안전 시설
        {
            'category': '편의/안전 시설',
            'title': '기존 핵심 복지 사업 안정 운영',
            'description': '기존 핵심 복지 사업의 안정적 운영 및 발전',
            'detailed_description': '학생회에서 운영하는 핵심 복지 사업들을 안정적으로 운영하면서 지속적인 발전 방안을 모색합니다. 학생들의 만족도 향상을 위해 서비스 품질을 개선합니다.',
            'progress_rate': 80,
            'status': '진행중',
            'order': 25
        },
        {
            'category': '편의/안전 시설',
            'title': '학생 맞춤 제휴 다각화',
            'description': '학생들의 니즈에 맞는 다양한 제휴 서비스 확대',
            'detailed_description': '학식, 교통, 문화, 의료 등 다양한 분야에서 학생 맞춤형 제휴 서비스를 확대합니다. 실질적인 혜택을 제공하여 학생들의 경제적 부담을 줄입니다.',
            'progress_rate': 60,
            'status': '진행중',
            'order': 26
        },
        {
            'category': '편의/안전 시설',
            'title': '총학생회 회의실 대여사업',
            'description': '총학생회 회의실을 활용한 대여사업 운영',
            'detailed_description': '총학생회 회의실을 학생 단체 및 동아리에 대여하여 효율적으로 활용합니다. 수익 창출과 함께 학생 단체 활동을 지원하는 선순환 시스템을 구축합니다.',
            'progress_rate': 40,
            'status': '진행중',
            'order': 27
        },
        {
            'category': '편의/안전 시설',
            'title': '정부세종청사 셔틀버스 노선 추가',
            'description': '정부세종청사까지 운행하는 셔틀버스 노선 신설',
            'detailed_description': '세종캠퍼스 학생들의 교통 편의를 위해 정부세종청사까지 운행하는 셔틀버스 노선을 추가합니다. 출퇴근과 실습 등 다양한 목적으로 활용할 수 있습니다.',
            'progress_rate': 25,
            'status': '진행중',
            'order': 28
        },
        {
            'category': '편의/안전 시설',
            'title': '셔틀버스 트래킹 시스템 공식화',
            'description': '셔틀버스 실시간 위치 추적 시스템 도입',
            'detailed_description': '셔틀버스의 실시간 위치를 확인할 수 있는 트래킹 시스템을 공식화합니다. 앱과 웹사이트를 통해 버스 도착 시간을 예측하고 효율적으로 이용할 수 있습니다.',
            'progress_rate': 70,
            'status': '진행중',
            'order': 29
        },
        {
            'category': '편의/안전 시설',
            'title': '공유 킥보드 주차 문제 논의',
            'description': '캠퍼스 내 공유 킥보드 주차 문제 해결 방안 모색',
            'detailed_description': '캠퍼스 내 공유 킥보드의 무분별한 주차 문제를 해결하기 위해 관련 기관과 논의를 진행합니다. 적절한 주차 구역 지정과 이용자 교육을 통해 쾌적한 캠퍼스 환경을 조성합니다.',
            'progress_rate': 30,
            'status': '진행중',
            'order': 30
        },
        {
            'category': '편의/안전 시설',
            'title': '비상약 대여사업',
            'description': '비상시 필요한 약품 대여 서비스 운영',
            'detailed_description': '갑작스러운 질병이나 상해 발생 시 사용할 수 있는 비상약을 대여하는 서비스를 운영합니다. 학생들의 건강과 안전을 위한 예방적 조치입니다.',
            'progress_rate': 55,
            'status': '진행중',
            'order': 31
        },
        {
            'category': '편의/안전 시설',
            'title': '학생 주차권 할인 논의',
            'description': '학생 주차권 할인 혜택 도입을 위한 논의 착수',
            'detailed_description': '통학하는 학생들의 주차 비용 부담을 줄이기 위해 주차권 할인 혜택 도입을 추진합니다. 관련 기관과의 협의를 통해 실질적인 혜택을 제공합니다.',
            'progress_rate': 15,
            'status': '진행중',
            'order': 32
        },
        {
            'category': '편의/안전 시설',
            'title': '정기적 시설 점검',
            'description': '캠퍼스 시설의 정기적 점검 및 학생 의견 수렴',
            'detailed_description': '캠퍼스 내 모든 시설에 대한 정기적인 점검을 실시하고, 학생들의 의견을 수렴하여 즉각적인 개선을 진행합니다. 쾌적하고 안전한 학교 환경을 유지합니다.',
            'progress_rate': 65,
            'status': '진행중',
            'order': 33
        },

        # 기타
        {
            'category': '기타',
            'title': '새미기픈물 운영',
            'description': '새미기픈물 사업 운영으로 학생 편의 제공',
            'detailed_description': '학생들의 일상생활 편의를 위한 새미기픈물 사업을 운영합니다. 필요한 물품을 저렴하게 구입할 수 있는 시스템을 구축합니다.',
            'progress_rate': 75,
            'status': '진행중',
            'order': 34
        },
        {
            'category': '기타',
            'title': '시험기간 담배꽁초 투표',
            'description': '시험기간 흡연 구역 지정 및 클린 캠페인을 위한 투표 실시',
            'detailed_description': '시험기간 동안의 흡연 구역 지정과 클린 캠페인 방향을 결정하기 위해 학생 투표를 실시합니다. 학생들의 의견을 직접 반영하여 정책을 수립합니다.',
            'progress_rate': 85,
            'status': '진행중',
            'order': 35
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
            'title': '총학생회칙 및 세칙',
            'content': '고려대학교 세종캠퍼스 총학생회의 기본 회칙 및 세부 운영 세칙입니다.',
            'pdf_filename': r'static\uploads\regulations\regulation_sejong_main.pdf',
            'order': 1
        },
        {
            'category': '총학생회',
            'title': '총학생회 일반규칙',
            'content': '총학생회의 일반적인 운영 규칙과 절차를 정의합니다.',
            'pdf_filename': r'static\uploads\regulations\regulation_sejong_general_rules.pdf',
            'order': 2
        },
        {
            'category': '총학생회',
            'title': '총학생회 세칙에 부수된 규칙',
            'content': '총학생회 세칙을 보완하는 부속 규칙입니다.',
            'pdf_filename': r'static\uploads\regulations\regulation_sejong_additional_rules.pdf',
            'order': 3
        },
        {
            'category': '단과대학',
            'title': '과학기술대학 학생회칙',
            'content': '과학기술대학 학생회의 조직과 운영에 관한 회칙입니다.',
            'pdf_filename': r'static\uploads\regulations\regulation_science_tech.pdf',
            'order': 4
        },
        {
            'category': '단과대학',
            'title': '글로벌비즈니스대학 학생회칙',
            'content': '글로벌비즈니스대학 학생회의 조직과 운영에 관한 회칙입니다.',
            'pdf_filename': r'static\uploads\regulations\regulation_global_biz.pdf',
            'order': 5
        },
        {
            'category': '단과대학',
            'title': '문화스포츠대학 학생회칙',
            'content': '문화스포츠대학 학생회의 조직과 운영에 관한 회칙입니다.',
            'pdf_filename': r'static\uploads\regulations\regulation_culture_sports.pdf',
            'order': 6
        },
        {
            'category': '단과대학',
            'title': '약학대학 학생회칙',
            'content': '약학대학 학생회의 조직과 운영에 관한 회칙입니다.',
            'pdf_filename': r'static\uploads\regulations\regulation_sejong_main.pdf',
            'order': 7
        },
        {
            'category': '단과대학',
            'title': '공공정책대학 학생회칙',
            'content': '공공정책대학 학생회의 조직과 운영에 관한 회칙입니다.',
            'pdf_filename': r'static\uploads\regulations\regulation_sejong_main.pdf',
            'order': 8
        },
        {
            'category': '단과대학',
            'title': '스마트도시대학 학생회칙',
            'content': '스마트도시대학 학생회의 조직과 운영에 관한 회칙입니다.',
            'pdf_filename': r'static\uploads\regulations\regulation_sejong_main.pdf',
            'order': 9
        },
        {
            'category': '특별기구',
            'title': '총예비역회 학생회칙',
            'content': '총예비역회의 조직과 운영에 관한 회칙입니다.',
            'pdf_filename': r'static\uploads\regulations\regulation_sejong_main.pdf',
            'order': 10
        },
        {
            'category': '특별기구',
            'title': '총동아리연합회 학생회칙',
            'content': '총동아리연합회의 조직과 운영에 관한 회칙입니다.',
            'pdf_filename': r'static\uploads\regulations\regulation_club_union.pdf',
            'order': 11
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
        # 0순위 - 회장단
        {'name': '오미령', 'position': '총학생회장', 'department': '총학생회장단', 'major': '중국학전공21', 'student_id': '2021****', 'email': 'ryeong0310@korea.ac.kr', 'phone': '010-5453-8819', 'order': 1},
        {'name': '장선규', 'position': '부총학생회장', 'department': '총학생회장단', 'major': '디지털경영전공23', 'student_id': '2023390822', 'email': 'dsng3419@korea.ac.kr', 'phone': '010-6598-6414', 'order': 2},

        # 1순위 - 본부
        {'name': '이세민', 'position': '중앙집행위원장', 'department': '본부', 'major': '정부행정학부23', 'student_id': '2023****', 'email': 'marcia0012@korea.ac.kr', 'phone': '010-3682-1394', 'order': 3},
        {'name': '서가연', 'position': '기획정책위원장', 'department': '본부', 'major': '정부행정학부23', 'student_id': '2023****', 'email': 'sgy0120@korea.ac.kr', 'phone': '010-7139-1782', 'order': 4},

        # 1순위 - 산하위원회
        {'name': '서홍욱', 'position': '산하위원장', 'department': '산하위원회', 'major': '문화유산융합학부21', 'student_id': '202140041', 'email': 'hongwook5179@naver.com', 'phone': '010-3068-5179', 'order': 5},

        # 2순위 - 중집위 국들
        # 미디어소통국
        {'name': '서종원', 'position': '국장', 'department': '중앙집행위원회 미디어소통국', 'major': '문화콘텐츠전공23', 'student_id': '2023400537', 'email': 'seoo0914@naver.com', 'phone': '010-4624-5404', 'order': 6},
        {'name': '김바다', 'position': '차장', 'department': '중앙집행위원회 미디어소통국', 'major': '융합경영학부25', 'student_id': '2025390625', 'email': 'bada1222@korea.ac.kr', 'phone': '010-7128-2842', 'order': 7},
        {'name': '공석', 'position': '국원', 'department': '중앙집행위원회 미디어소통국', 'major': '공석', 'student_id': '-', 'email': 'none@korea.ac.kr', 'phone': '', 'order': 8},

        # 사무국
        {'name': '장서영', 'position': '국장', 'department': '중앙집행위원회 사무국', 'major': '융합경영학부25', 'student_id': '2025390610', 'email': 'sally040929@naver.com', 'phone': '010-5592-8839', 'order': 9},
        {'name': '김현지', 'position': '차장', 'department': '중앙집행위원회 사무국', 'major': '지능형반도체공학과25', 'student_id': '2025271477', 'email': '0302guswl@gmail.com', 'phone': '010-2224-9638', 'order': 10},
        {'name': '공석', 'position': '국원', 'department': '중앙집행위원회 사무국', 'major': '공석', 'student_id': '-', 'email': 'none@korea.ac.kr', 'phone': '', 'order': 11},

        # 재정국
        {'name': '조민서', 'position': '국장', 'department': '중앙집행위원회 재정국', 'major': '글로벌학부25', 'student_id': '2025390096', 'email': 'ms009264@naver.com', 'phone': '010-3848-9263', 'order': 12},
        {'name': '장은우', 'position': '차장', 'department': '중앙집행위원회 재정국', 'major': '융합경영학부25', 'student_id': '2025390592', 'email': 'selina061026@gmail.com', 'phone': '010-8619-4065', 'order': 13},
        {'name': '공석', 'position': '국원', 'department': '중앙집행위원회 재정국', 'major': '공석', 'student_id': '-', 'email': 'none@korea.ac.kr', 'phone': '', 'order': 14},

        # 기정위 국들
        # 문화기획국
        {'name': '성지연', 'position': '국장', 'department': '기획정책위원회 문화기획국', 'major': '통일외교안보전공21', 'student_id': '2021******', 'email': 'tjdwldus4523@korea.ac.kr', 'phone': '010-8727-0671', 'order': 15},
        {'name': '김준용', 'position': '차장', 'department': '기획정책위원회 문화기획국', 'major': '빅데이터사이언스학부25', 'student_id': '2025380541', 'email': 'junyonging27@gmail.com', 'phone': '010-4848-2153', 'order': 16},
        {'name': '공석', 'position': '국원', 'department': '기획정책위원회 문화기획국', 'major': '공석', 'student_id': '-', 'email': 'none@korea.ac.kr', 'phone': '', 'order': 17},

        # 대외협력국
        {'name': '최보겸', 'position': '국장', 'department': '기획정책위원회 대외협력국', 'major': '공공사회학전공24', 'student_id': '2024380332', 'email': 'bgchoi03@naver.com', 'phone': '010-3614-1581', 'order': 18},
        {'name': '이수혁', 'position': '차장', 'department': '기획정책위원회 대외협력국', 'major': '환경시스템공학과25', 'student_id': '2025271229', 'email': 'leesu5685@korea.ac.kr', 'phone': '010-2923-5685', 'order': 19},
        {'name': '공석', 'position': '국원', 'department': '기획정책위원회 대외협력국', 'major': '공석', 'student_id': '-', 'email': 'none@korea.ac.kr', 'phone': '', 'order': 20},

        # 정책국
        {'name': '김준환', 'position': '국장', 'department': '기획정책위원회 정책국', 'major': '미디어문예창작전공', 'student_id': '2023400524', 'email': 'junhwanlife@gmail.com', 'phone': '010-5712-2975', 'order': 21},
        {'name': '정다연', 'position': '차장', 'department': '기획정책위원회 정책국', 'major': '글로벌학부 한국학전공25', 'student_id': '2025390039', 'email': 'dayeon1262@naver.com', 'phone': '010-5966-1262', 'order': 22},
        {'name': '공석', 'position': '국원', 'department': '기획정책위원회 정책국', 'major': '공석', 'student_id': '-', 'email': 'none@korea.ac.kr', 'phone': '', 'order': 23},

        # 인권/복지부 국들
        # 홍보국
        {'name': '이유나', 'position': '국장', 'department': '인권/복지부 홍보국', 'major': '생명정보공학과25', 'student_id': '2025270924', 'email': 'soosaengs@naver.com', 'phone': '010-2120-8707', 'order': 24},
        {'name': '백서영', 'position': '차장', 'department': '인권/복지부 홍보국', 'major': '글로벌경영전공24', 'student_id': '2024390856', 'email': 'qortjdud76@naver.com', 'phone': '010-2126-4392', 'order': 25},
        {'name': '공석', 'position': '국원', 'department': '인권/복지부 홍보국', 'major': '공석', 'student_id': '-', 'email': 'none@korea.ac.kr', 'phone': '', 'order': 26},

        # 기획국
        {'name': '민서현', 'position': '국장', 'department': '인권/복지부 기획국', 'major': '글로벌학부 한국학전공25', 'student_id': '2025390066', 'email': 'sxxhy629@gmail.com', 'phone': '010-5354-4061', 'order': 27},
        {'name': '김종욱', 'position': '차장', 'department': '인권/복지부 기획국', 'major': '전자및정보공학과24', 'student_id': '2024270783', 'email': 'a01023097781@gmail.com', 'phone': '010-2309-7781', 'order': 28},
        {'name': '공석', 'position': '국원', 'department': '인권/복지부 기획국', 'major': '공석', 'student_id': '-', 'email': 'none@korea.ac.kr', 'phone': '', 'order': 29},

        # 사무재정국
        {'name': '김다연', 'position': '국장', 'department': '인권/복지부 사무재정국', 'major': '글로벌경영전공24', 'student_id': '2024390735', 'email': 'ekdus0510@korea.ac.kr', 'phone': '010-9970-8722', 'order': 30},
        {'name': '문재준', 'position': '차장', 'department': '인권/복지부 사무재정국', 'major': '데이터계산과학전공23', 'student_id': '2023270022', 'email': 'rhahaehoon02@naver.com', 'phone': '010-3712-4978', 'order': 31},
        {'name': '공석', 'position': '국원', 'department': '인권/복지부 사무재정국', 'major': '공석', 'student_id': '-', 'email': 'none@korea.ac.kr', 'phone': '', 'order': 32},

        # 교육/복지부 국들
        # 홍보국
        {'name': '공석', 'position': '국장', 'department': '교육/복지부 홍보국', 'major': '공석', 'student_id': '-', 'email': 'none@korea.ac.kr', 'phone': '', 'order': 33},
        {'name': '공석', 'position': '차장', 'department': '교육/복지부 홍보국', 'major': '공석', 'student_id': '-', 'email': 'none@korea.ac.kr', 'phone': '', 'order': 34},
        {'name': '공석', 'position': '국원', 'department': '교육/복지부 홍보국', 'major': '공석', 'student_id': '-', 'email': 'none@korea.ac.kr', 'phone': '', 'order': 35},

        # 기획국
        {'name': '이호영', 'position': '국장', 'department': '교육/복지부 기획국', 'major': '약학과23', 'student_id': '2023290022', 'email': 'dlghdud0324@naver.com', 'phone': '010-3569-8227', 'order': 36},
        {'name': '정승훈', 'position': '차장', 'department': '교육/복지부 기획국', 'major': '통일외교안보전공25', 'student_id': '2025380155', 'email': 'jsh7968@korea.ac.kr', 'phone': '010-7178-7968', 'order': 37},
        {'name': '공석', 'position': '국원', 'department': '교육/복지부 기획국', 'major': '공석', 'student_id': '-', 'email': 'none@korea.ac.kr', 'phone': '', 'order': 38},

        # 사무재정국
        {'name': '공석', 'position': '국장', 'department': '교육/복지부 사무재정국', 'major': '공석', 'student_id': '-', 'email': 'none@korea.ac.kr', 'phone': '', 'order': 39},
        {'name': '공석', 'position': '차장', 'department': '교육/복지부 사무재정국', 'major': '공석', 'student_id': '-', 'email': 'none@korea.ac.kr', 'phone': '', 'order': 40},
        {'name': '공석', 'position': '국원', 'department': '교육/복지부 사무재정국', 'major': '공석', 'student_id': '-', 'email': 'none@korea.ac.kr', 'phone': '', 'order': 41},
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
            'title': ' ',
            'image_url': r'static\uploads\banners\banner_1.png',
            'link': '',
            'is_active': True,
            'is_event_banner': True,
            'order': 1
        },
        {
            'title': ' ',
            'image_url': r'static\uploads\banners\banner_2.png',
            'link': '',
            'is_active': True,
            'is_event_banner': False,
            'order': 2
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
