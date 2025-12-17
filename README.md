# 고려대학교 38대 총학생회 웹사이트

고려대학교 38대 총학생회의 공식 웹사이트입니다. 학생회의 일정, 조직도, 공약 이행 현황, 회의록, 회칙, 교내 프로그램 정보 등을 학우들에게 투명하게 공개하고 관리할 수 있는 플랫폼입니다.

## 주요 기능

### 학우 대상 기능
- **홈페이지**: 최근 일정, 공약 이행률, 교내 프로그램 한눈에 보기
- **일정**: 학생회 주요 일정 확인
- **조직도**: 38대 총학생회 임원진 소개
- **공약**: 공약 목록 및 이행률 조회, 공약별 상세 정보 및 진행 상황
- **회의록**: 학생회 회의 내용 투명 공개
- **회칙**: 각 단위 회칙 열람
- **교내 프로그램**: 다양한 교내 프로그램 정보 공유

### 관리자 기능
- **관리자 인증**: 안전한 로그인 시스템
- **일정 관리**: 일정 추가, 수정, 삭제
- **조직도 관리**: 임원진 정보 관리
- **공약 관리**: 공약 추가, 수정, 이행률 업데이트, 진행 상황 추가
- **회의록 관리**: 회의록 작성, 수정, 삭제
- **회칙 관리**: 회칙 등록 및 수정
- **프로그램 관리**: 교내 프로그램 정보 관리

## 디자인 특징

- **고려대학교 브랜드 컬러**: 크림슨 레드(#961A32) 적용
- **애플 스타일**: 깔끔하고 세련된 UI/UX
- **모바일 우선 반응형 디자인**: 모든 기기에서 최적화된 화면
- **직관적인 네비게이션**: 쉽고 빠른 정보 접근

## 기술 스택

### Backend
- **Flask 3.0.0**: Python 웹 프레임워크
- **Flask-SQLAlchemy**: ORM을 통한 데이터베이스 관리
- **Flask-Login**: 사용자 인증 관리
- **SQLite**: 경량 데이터베이스

### Frontend
- **HTML5**: 웹 구조
- **CSS3**: 모던 스타일링 (CSS Variables, Flexbox, Grid)
- **Vanilla JavaScript**: 인터랙티브 기능

## 설치 및 실행

### 1. 저장소 클론
\`\`\`bash
git clone <repository-url>
cd 38th_website
\`\`\`

### 2. 가상환경 생성 및 활성화 (권장)
\`\`\`bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\\Scripts\\activate  # Windows
\`\`\`

### 3. 의존성 설치
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 4. 데이터베이스 초기화
\`\`\`bash
flask --app app init-db
\`\`\`

이 명령어는 SQLite 데이터베이스를 생성하고 기본 관리자 계정을 만듭니다:
- **아이디**: admin
- **비밀번호**: admin

⚠️ **중요**: 운영 환경에서는 반드시 비밀번호를 변경하세요!

### 5. 애플리케이션 실행
\`\`\`bash
python app.py
\`\`\`

또는

\`\`\`bash
flask --app app run
\`\`\`

웹 브라우저에서 `http://localhost:5000`으로 접속하세요.

## 프로젝트 구조

\`\`\`
38th_website/
├── app.py                 # 메인 Flask 애플리케이션
├── models.py              # 데이터베이스 모델
├── config.py              # 설정 파일
├── requirements.txt       # Python 의존성
├── README.md              # 프로젝트 문서
├── static/                # 정적 파일
│   ├── css/
│   │   └── style.css      # 메인 스타일시트
│   ├── js/
│   │   └── main.js        # JavaScript 파일
│   └── images/            # 이미지 파일
└── templates/             # HTML 템플릿
    ├── base.html          # 기본 레이아웃
    ├── index.html         # 홈페이지
    ├── schedule.html      # 일정 페이지
    ├── organization.html  # 조직도 페이지
    ├── promises.html      # 공약 목록
    ├── promise_detail.html # 공약 상세
    ├── minutes.html       # 회의록 목록
    ├── minute_detail.html # 회의록 상세
    ├── regulations.html   # 회칙 페이지
    ├── programs.html      # 프로그램 페이지
    └── admin/             # 관리자 페이지
        ├── login.html
        ├── dashboard.html
        ├── schedules.html
        ├── schedule_form.html
        ├── promises.html
        ├── promise_form.html
        ├── promise_progress_form.html
        ├── minutes.html
        ├── minute_form.html
        ├── programs.html
        ├── program_form.html
        ├── organization.html
        ├── organization_form.html
        ├── regulations.html
        └── regulation_form.html
\`\`\`

## 관리자 사용 가이드

### 로그인
1. 브라우저에서 `/admin/login` 접속
2. 기본 계정으로 로그인 (admin/admin)
3. 관리자 대시보드 접근

### 콘텐츠 관리
- **일정 추가**: 관리자 대시보드 > 일정 관리 > 일정 추가
- **공약 관리**: 공약 추가 후 진행 상황 업데이트 가능
- **회의록 작성**: 회의 후 상세 내용 기록
- **프로그램 등록**: 교내 프로그램 정보 입력 및 활성화/비활성화

### 보안 주의사항
- 기본 관리자 비밀번호는 반드시 변경하세요
- 관리자 계정 정보를 안전하게 보관하세요
- 정기적으로 백업을 수행하세요

## 데이터베이스 스키마

### Admin (관리자)
- username, password_hash, name

### Schedule (일정)
- title, description, start_date, end_date, location, category

### Promise (공약)
- category, title, description, detailed_description, progress_rate, status, order

### PromiseProgress (공약 진행 상황)
- promise_id, title, content, date

### MeetingMinutes (회의록)
- title, meeting_type, meeting_date, attendees, agenda, content, decisions, file_url

### Regulation (회칙)
- category, title, content, file_url, order

### Program (교내 프로그램)
- title, category, description, organizer, target, start_date, end_date, application_start, application_end, location, link, image_url, is_active

### Organization (조직도)
- name, position, department, major, student_id, phone, email, photo_url, order

## 개발 환경 설정

### 디버그 모드
개발 시 자동 리로드를 위해 디버그 모드 활성화:

\`\`\`bash
export FLASK_ENV=development  # Linux/Mac
set FLASK_ENV=development     # Windows
flask --app app run --debug
\`\`\`

### 환경 변수
\`.env\` 파일을 생성하여 환경 변수 설정:

\`\`\`
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
\`\`\`

## 배포

### 운영 환경 체크리스트
- [ ] SECRET_KEY 변경
- [ ] DEBUG 모드 비활성화
- [ ] 기본 관리자 비밀번호 변경
- [ ] HTTPS 적용
- [ ] 데이터베이스 백업 설정
- [ ] 프로덕션 웹 서버 사용 (Gunicorn, uWSGI 등)

### 권장 배포 스택
- **웹 서버**: Nginx
- **WSGI 서버**: Gunicorn
- **프로세스 관리**: Supervisor 또는 systemd
- **데이터베이스**: PostgreSQL (운영 환경 권장)

## 라이선스

이 프로젝트는 고려대학교 38대 총학생회를 위해 제작되었습니다.

## 문의

고려대학교 38대 총학생회
- 이메일: student@korea.ac.kr
- 전화: 02-XXXX-XXXX

---

© 2025 고려대학교 38대 총학생회. All rights reserved.
