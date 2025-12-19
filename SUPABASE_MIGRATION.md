# Supabase 데이터베이스 마이그레이션 가이드

## 목차
1. [마이그레이션 개요](#마이그레이션-개요)
2. [Supabase란?](#supabase란)
3. [마이그레이션 이유](#마이그레이션-이유)
4. [사전 준비](#사전-준비)
5. [데이터베이스 스키마 생성](#데이터베이스-스키마-생성)
6. [코드 구조 변경](#코드-구조-변경)
7. [데이터 마이그레이션](#데이터-마이그레이션)
8. [테스트 및 검증](#테스트-및-검증)
9. [배포 전략](#배포-전략)
10. [롤백 계획](#롤백-계획)

---

## 마이그레이션 개요

이 문서는 Flask-SQLAlchemy (SQLite) 기반의 학생회 웹사이트를 **Supabase PostgreSQL**로 마이그레이션하는 전체 과정을 설명합니다.

### 현재 스택
- **데이터베이스**: SQLite (로컬 파일: `student_council.db`)
- **ORM**: Flask-SQLAlchemy 3.1.1
- **인증**: Flask-Login 0.6.3

### 목표 스택
- **데이터베이스**: Supabase PostgreSQL (클라우드 호스팅)
- **데이터베이스 클라이언트**: Supabase Python Client
- **인증**: Supabase Auth (선택사항) 또는 기존 Flask-Login 유지

---

## Supabase란?

**Supabase**는 Firebase의 오픈소스 대안으로, PostgreSQL 데이터베이스를 기반으로 한 Backend-as-a-Service(BaaS) 플랫폼입니다.

### 주요 특징
- ✅ **PostgreSQL 기반**: 강력한 관계형 데이터베이스
- ✅ **실시간 데이터베이스**: WebSocket을 통한 실시간 업데이트
- ✅ **인증 시스템**: 이메일, OAuth, Magic Link 등 다양한 인증 방식
- ✅ **자동 API 생성**: RESTful API 및 GraphQL 자동 생성
- ✅ **파일 스토리지**: S3 호환 객체 스토리지
- ✅ **무료 티어**: 소규모 프로젝트에 충분한 무료 사용량

---

## 마이그레이션 이유

### SQLite의 한계
1. **동시성 문제**: 다수의 사용자가 동시에 접속 시 성능 저하
2. **확장성 부족**: 대용량 데이터 처리 제한적
3. **배포 제약**: 파일 기반이라 클라우드 배포 시 데이터 영속성 문제
4. **백업 복잡도**: 수동 파일 백업 필요

### Supabase의 장점
1. **확장성**: PostgreSQL 기반으로 대규모 트래픽 처리 가능
2. **클라우드 호스팅**: 자동 백업, 고가용성
3. **실시간 기능**: 공약 진행률, 일정 등 실시간 업데이트 가능
4. **보안**: Row Level Security (RLS)로 세밀한 권한 관리
5. **무료 시작**: 초기 비용 부담 없음

---

## 사전 준비

### 1. Supabase 계정 생성
1. https://supabase.com 접속
2. 계정 생성 및 로그인
3. 새 프로젝트 생성
   - **프로젝트 이름**: `koreauniv-student-council` (예시)
   - **데이터베이스 비밀번호**: 강력한 비밀번호 설정 (잘 보관!)
   - **리전**: `Northeast Asia (Seoul)` 권장

### 2. Supabase 프로젝트 정보 확인
프로젝트 생성 후 다음 정보를 복사해둡니다:

- **Project URL**: `https://xxxxx.supabase.co`
- **API Key (anon, public)**: `eyJhbGc...` (공개 키)
- **API Key (service_role)**: `eyJhbGc...` (서비스 키, 비공개!)
- **Database URL**: `postgresql://postgres:[PASSWORD]@db.xxxxx.supabase.co:5432/postgres`

### 3. 환경 변수 파일 생성
프로젝트 루트에 `.env` 파일 생성:

```bash
# Supabase Configuration
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGc...  # anon key
SUPABASE_SERVICE_KEY=eyJhbGc...  # service_role key
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.xxxxx.supabase.co:5432/postgres

# Flask Secret Key
SECRET_KEY=your-super-secret-key-change-this

# Environment
FLASK_ENV=development
```

**⚠️ 주의**: `.env` 파일은 절대 Git에 커밋하지 마세요! `.gitignore`에 추가하세요.

---

## 데이터베이스 스키마 생성

### 1. Supabase SQL Editor 접속
Supabase 대시보드 → SQL Editor → New Query

### 2. 스키마 생성 SQL 실행

```sql
-- =====================================================
-- 고려대학교 세종캠퍼스 제38대 총학생회 데이터베이스 스키마
-- =====================================================

-- 1. 관리자 테이블
CREATE TABLE admin (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(200) NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 일정 테이블
CREATE TABLE schedule (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ,
    location VARCHAR(200),
    category VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. 공약 테이블
CREATE TABLE promise (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    detailed_description TEXT,
    progress_rate INTEGER DEFAULT 0 CHECK (progress_rate >= 0 AND progress_rate <= 100),
    status VARCHAR(50) DEFAULT '진행중',
    "order" INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. 공약 진행 상황 테이블
CREATE TABLE promise_progress (
    id SERIAL PRIMARY KEY,
    promise_id INTEGER NOT NULL REFERENCES promise(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    date TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. 회의록 테이블
CREATE TABLE meeting_minutes (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    meeting_type VARCHAR(100),
    meeting_date TIMESTAMPTZ NOT NULL,
    attendees TEXT,
    agenda TEXT,
    content TEXT NOT NULL,
    decisions TEXT,
    file_url VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. 회칙 테이블
CREATE TABLE regulation (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    pdf_filename VARCHAR(500),
    file_url VARCHAR(500),
    "order" INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. 프로그램 테이블
CREATE TABLE program (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    description TEXT NOT NULL,
    organizer VARCHAR(200),
    target VARCHAR(200),
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    application_start TIMESTAMPTZ,
    application_end TIMESTAMPTZ,
    location VARCHAR(200),
    link VARCHAR(500),
    image_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. 조직도 테이블
CREATE TABLE organization (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    position VARCHAR(100) NOT NULL,
    department VARCHAR(100),
    major VARCHAR(100),
    student_id VARCHAR(20),
    phone VARCHAR(50),
    email VARCHAR(100),
    photo_url VARCHAR(500),
    "order" INTEGER DEFAULT 0,
    parent_id INTEGER REFERENCES organization(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 9. 배너 테이블
CREATE TABLE banner (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    image_url VARCHAR(500) NOT NULL,
    link VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    is_event_banner BOOLEAN DEFAULT FALSE,
    "order" INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 10. 아카이브 테이블
CREATE TABLE archive (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    event_date TIMESTAMPTZ NOT NULL,
    category VARCHAR(100),
    location VARCHAR(200),
    thumbnail_url VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    "order" INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 11. 아카이브 이미지 테이블
CREATE TABLE archive_image (
    id SERIAL PRIMARY KEY,
    archive_id INTEGER NOT NULL REFERENCES archive(id) ON DELETE CASCADE,
    image_url VARCHAR(500) NOT NULL,
    caption VARCHAR(500),
    "order" INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- 인덱스 생성 (성능 최적화)
-- =====================================================

CREATE INDEX idx_schedule_start_date ON schedule(start_date);
CREATE INDEX idx_promise_category ON promise(category);
CREATE INDEX idx_promise_progress_promise_id ON promise_progress(promise_id);
CREATE INDEX idx_meeting_minutes_date ON meeting_minutes(meeting_date);
CREATE INDEX idx_regulation_category ON regulation(category);
CREATE INDEX idx_program_active ON program(is_active);
CREATE INDEX idx_organization_department ON organization(department);
CREATE INDEX idx_organization_order ON organization("order");
CREATE INDEX idx_banner_active ON banner(is_active);
CREATE INDEX idx_archive_active ON archive(is_active);
CREATE INDEX idx_archive_image_archive_id ON archive_image(archive_id);

-- =====================================================
-- 트리거 생성 (자동 updated_at 업데이트)
-- =====================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_schedule_updated_at BEFORE UPDATE ON schedule
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_promise_updated_at BEFORE UPDATE ON promise
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_meeting_minutes_updated_at BEFORE UPDATE ON meeting_minutes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_regulation_updated_at BEFORE UPDATE ON regulation
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_program_updated_at BEFORE UPDATE ON program
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_organization_updated_at BEFORE UPDATE ON organization
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_banner_updated_at BEFORE UPDATE ON banner
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_archive_updated_at BEFORE UPDATE ON archive
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- Row Level Security (RLS) 설정 (선택사항)
-- =====================================================

-- 모든 테이블에 대해 공개 읽기, 관리자만 쓰기 설정 예시
-- 필요에 따라 커스터마이징 가능

-- ALTER TABLE schedule ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Public read access" ON schedule FOR SELECT USING (true);
-- CREATE POLICY "Admin write access" ON schedule FOR ALL USING (auth.role() = 'authenticated');

-- 위와 같은 방식으로 다른 테이블에도 적용 가능
```

### 3. 스키마 생성 확인
Supabase 대시보드 → Table Editor에서 모든 테이블이 생성되었는지 확인

---

## 코드 구조 변경

### 1. 의존성 업데이트

**requirements.txt** 수정:

```txt
Flask==3.0.0
Flask-Login==0.6.3
Werkzeug==3.0.1
python-dotenv==1.0.0
supabase==2.3.4
psycopg2-binary==2.9.9
```

설치:
```bash
pip install -r requirements.txt
```

### 2. 새로운 데이터베이스 클라이언트 생성

**`database.py`** (새 파일 생성):

```python
"""
Supabase 데이터베이스 클라이언트
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Supabase 클라이언트 초기화
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

supabase: Client = create_client(supabase_url, supabase_key)

def get_supabase_client() -> Client:
    """Supabase 클라이언트 반환"""
    return supabase
```

### 3. 모델 레이어 수정

**방법 1: 완전 마이그레이션** (Supabase만 사용)
- `models.py` 삭제
- 각 라우트에서 직접 Supabase 쿼리 사용

**방법 2: 하이브리드 접근** (권장)
- `models.py`를 유지하되, 데이터 접근 로직만 Supabase로 변경
- 기존 코드 변경 최소화

#### 방법 2 예시: Repository 패턴 사용

**`repositories/schedule_repository.py`** (새 파일):

```python
"""
일정 관련 데이터 접근 로직
"""
from database import get_supabase_client
from typing import List, Optional, Dict, Any

class ScheduleRepository:
    def __init__(self):
        self.supabase = get_supabase_client()
        self.table = "schedule"

    def get_all(self, order_by: str = "start_date", ascending: bool = False) -> List[Dict[str, Any]]:
        """모든 일정 조회"""
        query = self.supabase.table(self.table).select("*").order(order_by, desc=not ascending)
        response = query.execute()
        return response.data

    def get_by_id(self, schedule_id: int) -> Optional[Dict[str, Any]]:
        """ID로 일정 조회"""
        response = self.supabase.table(self.table).select("*").eq("id", schedule_id).execute()
        return response.data[0] if response.data else None

    def get_upcoming(self, limit: int = 10) -> List[Dict[str, Any]]:
        """다가오는 일정 조회"""
        from datetime import datetime
        now = datetime.now().isoformat()
        query = self.supabase.table(self.table).select("*").gte("start_date", now).order("start_date").limit(limit)
        response = query.execute()
        return response.data

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """일정 생성"""
        response = self.supabase.table(self.table).insert(data).execute()
        return response.data[0] if response.data else None

    def update(self, schedule_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """일정 수정"""
        response = self.supabase.table(self.table).update(data).eq("id", schedule_id).execute()
        return response.data[0] if response.data else None

    def delete(self, schedule_id: int) -> bool:
        """일정 삭제"""
        response = self.supabase.table(self.table).delete().eq("id", schedule_id).execute()
        return len(response.data) > 0
```

**다른 테이블용 Repository도 동일한 패턴으로 작성**

### 4. app.py 수정

**수정 전 (SQLAlchemy)**:
```python
@app.route('/schedule')
def schedule():
    schedules_query = Schedule.query.order_by(Schedule.start_date.desc()).all()
    # ...
```

**수정 후 (Supabase)**:
```python
from repositories.schedule_repository import ScheduleRepository

schedule_repo = ScheduleRepository()

@app.route('/schedule')
def schedule():
    schedules_query = schedule_repo.get_all(order_by="start_date", ascending=False)
    # ...
```

### 5. config.py 수정

**수정 전**:
```python
class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///student_council.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
```

**수정 후**:
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Supabase configuration
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

    # Secret key
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'

    # ... (나머지 설정 유지)
```

---

## 데이터 마이그레이션

### 옵션 1: 수동 마이그레이션 (소규모 데이터)
1. SQLite 데이터베이스에서 데이터 Export
2. Supabase Table Editor에서 수동 입력

### 옵션 2: Python 스크립트 마이그레이션 (권장)

**`migrate_data.py`** (새 파일):

```python
"""
SQLite에서 Supabase로 데이터 마이그레이션
"""
import sqlite3
from database import get_supabase_client
from datetime import datetime

def migrate_table(sqlite_table: str, supabase_table: str, column_mapping: dict = None):
    """
    SQLite 테이블 데이터를 Supabase로 마이그레이션

    Args:
        sqlite_table: SQLite 테이블 이름
        supabase_table: Supabase 테이블 이름
        column_mapping: 컬럼 이름 매핑 (SQLite -> Supabase)
    """
    supabase = get_supabase_client()

    # SQLite 연결
    conn = sqlite3.connect('student_council.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 데이터 조회
    cursor.execute(f"SELECT * FROM {sqlite_table}")
    rows = cursor.fetchall()

    print(f"마이그레이션 중: {sqlite_table} -> {supabase_table} ({len(rows)} rows)")

    # 데이터 변환 및 삽입
    for row in rows:
        data = dict(row)

        # 컬럼 이름 매핑 적용
        if column_mapping:
            data = {column_mapping.get(k, k): v for k, v in data.items()}

        # ID 제거 (Supabase에서 자동 생성)
        if 'id' in data:
            del data['id']

        # datetime 변환
        for key, value in data.items():
            if isinstance(value, str) and 'date' in key.lower():
                try:
                    data[key] = datetime.fromisoformat(value.replace('Z', '+00:00')).isoformat()
                except:
                    pass

        # Supabase에 삽입
        try:
            supabase.table(supabase_table).insert(data).execute()
        except Exception as e:
            print(f"Error inserting row: {e}")
            print(f"Data: {data}")

    conn.close()
    print(f"완료: {sqlite_table}")

def main():
    """메인 마이그레이션 함수"""
    print("=" * 60)
    print("SQLite -> Supabase 데이터 마이그레이션 시작")
    print("=" * 60)

    # 각 테이블 마이그레이션
    tables = [
        ('admin', 'admin'),
        ('schedule', 'schedule'),
        ('promise', 'promise'),
        ('promise_progress', 'promise_progress'),
        ('meeting_minutes', 'meeting_minutes'),
        ('regulation', 'regulation'),
        ('program', 'program'),
        ('organization', 'organization'),
        ('banner', 'banner'),
        ('archive', 'archive'),
        ('archive_image', 'archive_image'),
    ]

    for sqlite_table, supabase_table in tables:
        migrate_table(sqlite_table, supabase_table)

    print("=" * 60)
    print("마이그레이션 완료!")
    print("=" * 60)

if __name__ == "__main__":
    main()
```

**실행**:
```bash
python migrate_data.py
```

---

## 테스트 및 검증

### 1. 데이터 무결성 검증

```python
# verify_migration.py
from database import get_supabase_client

def verify_table(table_name: str, expected_count: int):
    supabase = get_supabase_client()
    response = supabase.table(table_name).select("*", count="exact").execute()
    actual_count = response.count

    print(f"{table_name}: {actual_count} / {expected_count}", end=" ")
    if actual_count == expected_count:
        print("✅")
    else:
        print("❌")

# 각 테이블 검증
verify_table("schedule", 10)  # 예상 개수 입력
verify_table("promise", 15)
# ... 나머지 테이블
```

### 2. 기능 테스트
- 모든 페이지 접속 확인
- CRUD 작업 테스트 (생성, 조회, 수정, 삭제)
- 관리자 로그인 테스트
- 파일 업로드 테스트

### 3. 성능 테스트
- 응답 시간 측정
- 동시 접속 테스트

---

## 배포 전략

### 단계적 배포 (Blue-Green Deployment)

1. **준비 단계**
   - Supabase 프로젝트 생성
   - 스키마 생성
   - 데이터 마이그레이션

2. **테스트 환경 배포**
   - 새 코드를 별도 서버/도메인에 배포
   - 충분한 테스트 진행

3. **프로덕션 배포**
   - 점검 시간 공지
   - 기존 데이터베이스 최종 백업
   - 새 코드 배포
   - 최종 데이터 동기화

4. **모니터링**
   - 에러 로그 모니터링
   - 사용자 피드백 수집

---

## 롤백 계획

문제 발생 시 신속한 롤백을 위한 준비:

### 1. SQLite 백업 유지
- 마이그레이션 전 `student_council.db` 백업
- 최소 1개월 보관

### 2. 코드 버전 관리
```bash
# 마이그레이션 전 브랜치 생성
git checkout -b backup/before-supabase-migration

# 마이그레이션 후 새 브랜치
git checkout -b feature/supabase-migration
```

### 3. 롤백 절차
1. 기존 코드로 복원: `git checkout backup/before-supabase-migration`
2. SQLite 데이터베이스 복원
3. 서버 재배포
4. 사용자 공지

---

## 추가 리소스

- **Supabase 공식 문서**: https://supabase.com/docs
- **Supabase Python Client**: https://github.com/supabase/supabase-py
- **PostgreSQL 문서**: https://www.postgresql.org/docs/

---

## 문의 및 지원

마이그레이션 과정에서 문제가 발생하면:
1. Supabase 대시보드의 Logs 확인
2. Python 에러 로그 확인
3. 개발팀 문의

---

**작성일**: 2025-12-19
**버전**: 1.0
**담당**: 제38대 총학생회 IT팀
