# Supabase 설정 가이드

고려대학교 38대 총학생회 웹사이트를 Supabase 데이터베이스로 연동하는 완벽한 가이드입니다.

## 목차

1. [Supabase 프로젝트 생성](#1-supabase-프로젝트-생성)
2. [데이터베이스 스키마 적용](#2-데이터베이스-스키마-적용)
3. [환경 변수 설정](#3-환경-변수-설정)
4. [Python 패키지 설치](#4-python-패키지-설치)
5. [기본 관리자 계정 생성](#5-기본-관리자-계정-생성)
6. [Heroku 배포 설정](#6-heroku-배포-설정)
7. [문제 해결](#7-문제-해결)

---

## 1. Supabase 프로젝트 생성

### 1.1 Supabase 계정 생성

1. [https://supabase.com](https://supabase.com)에 접속합니다.
2. "Start your project" 버튼을 클릭합니다.
3. GitHub 계정으로 로그인하거나 이메일로 회원가입합니다.

### 1.2 새 프로젝트 생성

1. Supabase 대시보드에서 "New Project" 버튼을 클릭합니다.
2. 다음 정보를 입력합니다:
   - **Name**: `koreauniv-38th-website` (또는 원하는 이름)
   - **Database Password**: 안전한 비밀번호 생성 (나중에 사용하지 않으므로 복잡해도 괜찮습니다)
   - **Region**: `Northeast Asia (Seoul)` 선택 (한국 서버)
   - **Pricing Plan**: Free (무료 플랜으로 충분합니다)
3. "Create new project" 버튼을 클릭합니다.
4. 프로젝트 생성까지 약 1-2분 정도 소요됩니다.

---

## 2. 데이터베이스 스키마 적용

### 2.1 SQL Editor 접속

1. Supabase 대시보드에서 좌측 메뉴의 **SQL Editor**를 클릭합니다.
2. "New query" 버튼을 클릭합니다.

### 2.2 스키마 SQL 실행

1. 프로젝트 루트의 `supabase_schema.sql` 파일을 엽니다.
2. 파일의 **전체 내용**을 복사합니다.
3. SQL Editor에 붙여넣습니다.
4. 우측 하단의 **"RUN"** 버튼을 클릭하여 실행합니다.
5. 실행 결과에서 "Success. No rows returned" 메시지를 확인합니다.

### 2.3 테이블 생성 확인

1. 좌측 메뉴에서 **Table Editor**를 클릭합니다.
2. 다음 11개의 테이블이 생성되었는지 확인합니다:
   - `admins` - 관리자
   - `schedules` - 일정
   - `promises` - 공약
   - `promise_progress` - 공약 진행상황
   - `meeting_minutes` - 회의록
   - `regulations` - 회칙
   - `programs` - 프로그램
   - `organizations` - 조직도
   - `banners` - 배너
   - `archives` - 아카이브
   - `archive_images` - 아카이브 이미지

---

## 3. 환경 변수 설정

### 3.1 Supabase 인증 키 가져오기

1. Supabase 대시보드에서 좌측 메뉴의 **Settings (⚙️)** > **API**를 클릭합니다.
2. "Project API keys" 섹션에서 다음 정보를 복사합니다:
   - **Project URL**: `https://your-project-id.supabase.co` 형식의 URL
   - **anon public**: `eyJ...` 형식의 긴 토큰
   - **service_role**: `eyJ...` 형식의 긴 토큰 (Show 버튼 클릭 필요)

⚠️ **주의**: `service_role` 키는 절대 공개하지 마세요! 데이터베이스에 대한 완전한 권한을 가집니다.

### 3.2 .env 파일 생성

1. 프로젝트 루트 디렉토리에 `.env` 파일을 생성합니다:

```bash
# Flask Configuration
SECRET_KEY=your-random-secret-key-here-change-this
FLASK_ENV=production
FLASK_DEBUG=False

# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-public-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# Application Configuration
PORT=1992
```

2. 각 값을 실제 값으로 교체합니다:
   - `SECRET_KEY`: 랜덤한 문자열 생성 (예: `python -c "import secrets; print(secrets.token_hex(32))"` 실행)
   - `SUPABASE_URL`: 위에서 복사한 Project URL
   - `SUPABASE_KEY`: 위에서 복사한 anon public 키
   - `SUPABASE_SERVICE_ROLE_KEY`: 위에서 복사한 service_role 키

### 3.3 .env 파일 보안

.env 파일은 이미 `.gitignore`에 추가되어 있어 Git에 커밋되지 않습니다. 절대 공개 저장소에 업로드하지 마세요!

---

## 4. Python 패키지 설치

### 4.1 가상환경 생성 (권장)

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 가상환경 활성화 (Mac/Linux)
source venv/bin/activate
```

### 4.2 패키지 설치

```bash
pip install -r requirements.txt
```

설치되는 주요 패키지:
- `Flask==3.0.0` - 웹 프레임워크
- `Flask-Login==0.6.3` - 사용자 인증
- `supabase==2.3.4` - Supabase Python 클라이언트
- `python-dotenv==1.0.0` - 환경 변수 관리

---

## 5. 기본 관리자 계정 생성

### 5.1 Flask CLI로 관리자 계정 생성

```bash
flask init-db
```

실행 결과:
```
Supabase를 사용하고 있습니다. supabase_schema.sql을 Supabase에 적용해주세요.
기본 관리자 계정 생성 완료 (admin / admin)
```

### 5.2 관리자 계정 정보

- **아이디**: `admin`
- **비밀번호**: `admin`

⚠️ **보안 경고**: 배포 전에 반드시 비밀번호를 변경하세요!

### 5.3 관리자 비밀번호 변경 (SQL로 직접 변경)

```sql
-- Supabase SQL Editor에서 실행
UPDATE admins
SET password_hash = 'pbkdf2:sha256:...' -- 새로운 해시된 비밀번호
WHERE username = 'admin';
```

Python에서 비밀번호 해시 생성:
```python
from werkzeug.security import generate_password_hash
print(generate_password_hash('your-new-password'))
```

---

## 6. Heroku 배포 설정

### 6.1 Heroku CLI 설치

1. [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) 다운로드 및 설치
2. 터미널에서 로그인:
   ```bash
   heroku login
   ```

### 6.2 Heroku 앱 생성

```bash
# Heroku 앱 생성
heroku create koreauniv-38th-website

# 또는 이름 없이 자동 생성
heroku create
```

### 6.3 환경 변수 설정

Heroku에 환경 변수를 설정합니다:

```bash
# SECRET_KEY 설정
heroku config:set SECRET_KEY=your-random-secret-key-here

# Supabase 설정
heroku config:set SUPABASE_URL=https://your-project-id.supabase.co
heroku config:set SUPABASE_KEY=your-anon-public-key-here
heroku config:set SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# Flask 환경 설정
heroku config:set FLASK_ENV=production
heroku config:set FLASK_DEBUG=False
```

설정 확인:
```bash
heroku config
```

### 6.4 Procfile 확인

프로젝트 루트에 `Procfile`이 있는지 확인합니다:

```
web: gunicorn app:app
```

없다면 생성하고, `requirements.txt`에 `gunicorn` 추가:

```bash
echo "gunicorn==21.2.0" >> requirements.txt
```

### 6.5 배포

```bash
# Git에 변경사항 커밋
git add .
git commit -m "Supabase integration complete"

# Heroku에 배포
git push heroku main

# 또는 다른 브랜치를 main으로 푸시
git push heroku your-branch:main
```

### 6.6 배포 확인

```bash
# 앱 열기
heroku open

# 로그 확인
heroku logs --tail
```

---

## 7. 문제 해결

### 7.1 "SUPABASE_URL과 SUPABASE_KEY 환경 변수가 설정되어야 합니다" 에러

**원인**: `.env` 파일이 없거나 환경 변수가 설정되지 않았습니다.

**해결방법**:
1. `.env` 파일이 프로젝트 루트에 있는지 확인
2. `.env` 파일의 내용이 올바른지 확인
3. Heroku의 경우 `heroku config` 명령어로 환경 변수 확인

### 7.2 "No module named 'supabase'" 에러

**원인**: Supabase 패키지가 설치되지 않았습니다.

**해결방법**:
```bash
pip install supabase==2.3.4
```

### 7.3 "Row Level Security" 에러로 데이터 조회/삽입 실패

**원인**: RLS(Row Level Security) 정책이 너무 엄격합니다.

**해결방법**:
1. Supabase 대시보드 > Authentication > Policies 확인
2. `supabase_schema.sql`의 RLS 정책 재확인
3. 필요시 임시로 RLS 비활성화 (개발 환경에서만):
   ```sql
   ALTER TABLE your_table_name DISABLE ROW LEVEL SECURITY;
   ```

### 7.4 관리자 로그인 실패

**원인**: 관리자 계정이 생성되지 않았거나 비밀번호가 틀렸습니다.

**해결방법**:
1. `flask init-db` 명령어 재실행
2. Supabase Table Editor에서 `admins` 테이블 확인
3. SQL로 직접 확인:
   ```sql
   SELECT * FROM admins WHERE username = 'admin';
   ```

### 7.5 Heroku 배포 실패

**원인**: 빌드 중 에러 발생

**해결방법**:
1. `requirements.txt`에 모든 패키지가 명시되어 있는지 확인
2. Python 버전 확인 (`runtime.txt` 파일 생성):
   ```
   python-3.11.0
   ```
3. Heroku 로그 확인:
   ```bash
   heroku logs --tail
   ```

### 7.6 파일 업로드가 저장되지 않음 (Heroku)

**원인**: Heroku는 ephemeral 파일 시스템을 사용하여 재시작 시 파일이 삭제됩니다.

**해결방법**: Supabase Storage 사용 (향후 기능)
1. Supabase > Storage 메뉴에서 버킷 생성
2. 파일 업로드를 Supabase Storage로 전환
3. 현재는 `static/uploads` 폴더를 Git에 포함시키거나 외부 스토리지(AWS S3, Cloudinary 등) 사용

---

## 8. 데이터베이스 관리

### 8.1 Supabase 대시보드에서 데이터 관리

1. **Table Editor**: 테이블 데이터 조회/수정/삭제
2. **SQL Editor**: SQL 쿼리 실행
3. **Database > Migrations**: 마이그레이션 관리

### 8.2 자주 사용하는 SQL 쿼리

```sql
-- 모든 공약 조회
SELECT * FROM promises ORDER BY "order";

-- 활성 배너 조회
SELECT * FROM banners WHERE is_active = true ORDER BY "order";

-- 다가오는 일정 조회
SELECT * FROM schedules
WHERE start_date >= NOW()
ORDER BY start_date
LIMIT 5;

-- 관리자 목록 조회
SELECT id, username, name, created_at FROM admins;
```

### 8.3 백업

Supabase는 자동 백업을 제공하지만, 수동 백업도 가능합니다:

1. **Settings > Database > Database backups**에서 백업 설정
2. SQL로 데이터 내보내기:
   ```bash
   # PostgreSQL dump (Supabase CLI 필요)
   supabase db dump -f backup.sql
   ```

---

## 9. 다음 단계

### 9.1 기능 추가

- [ ] Supabase Storage를 사용한 파일 업로드 개선
- [ ] Supabase Auth를 사용한 소셜 로그인
- [ ] Realtime 기능으로 실시간 데이터 업데이트
- [ ] Edge Functions로 서버리스 API 추가

### 9.2 성능 최적화

- [ ] 데이터베이스 인덱스 추가
- [ ] 쿼리 최적화
- [ ] 캐싱 전략 수립
- [ ] CDN 설정

### 9.3 보안 강화

- [ ] HTTPS 강제
- [ ] CORS 설정
- [ ] Rate Limiting
- [ ] 관리자 비밀번호 정책 강화

---

## 10. 지원 및 문서

- **Supabase 공식 문서**: https://supabase.com/docs
- **Supabase Python 클라이언트**: https://github.com/supabase/supabase-py
- **Flask 공식 문서**: https://flask.palletsprojects.com/
- **Heroku Python 가이드**: https://devcenter.heroku.com/categories/python-support

---

## 부록: 프로젝트 구조

```
38th_website/
├── app.py                      # Flask 애플리케이션 메인 파일
├── config.py                   # 설정 파일 (Supabase 설정 포함)
├── database.py                 # Supabase 클라이언트 초기화
├── supabase_helpers.py         # Supabase 헬퍼 함수들
├── admin_user.py               # Flask-Login 사용자 모델
├── supabase_schema.sql         # 데이터베이스 스키마
├── requirements.txt            # Python 패키지 목록
├── .env                        # 환경 변수 (Git에 포함되지 않음)
├── .env.example                # 환경 변수 예제
├── models.py                   # (레거시) SQLAlchemy 모델 - 더 이상 사용하지 않음
├── repositories/               # (레거시) Repository 패턴 - 참고용
├── static/                     # 정적 파일 (CSS, JS, 이미지)
│   ├── css/
│   ├── js/
│   ├── uploads/                # 업로드된 파일 (Heroku에서는 영구 보존 안 됨)
│   └── defaults/               # 기본 파일들
└── templates/                  # Jinja2 템플릿
    ├── admin/                  # 관리자 페이지 템플릿
    └── ...                     # 공개 페이지 템플릿
```

---

**마지막 업데이트**: 2025-12-20
**작성자**: Claude AI (Anthropic)
**프로젝트**: 고려대학교 38대 총학생회 웹사이트
