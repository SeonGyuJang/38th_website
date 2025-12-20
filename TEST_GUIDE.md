# 시스템 작동 확인 가이드

## 현재 시스템 구조

모든 데이터는 **Supabase**에 저장되고, 홈페이지는 **실시간으로 Supabase에서 데이터를 읽어옵니다**.

### ✅ 데이터 흐름

1. **Seed 데이터 업로드**
   ```bash
   python seed_to_supabase.py
   ```
   - Supabase Database에 기본 데이터 저장
   - Supabase Storage에 기본 파일 업로드 (배너, 회칙 PDF)

2. **홈페이지 표시**
   - 모든 페이지가 Supabase에서 실시간으로 데이터 읽기
   - 파일들은 Supabase Storage URL로 로드

3. **관리자 추가/수정**
   - 관리자 패널에서 데이터 추가 → Supabase에 즉시 저장
   - 파일 업로드 → Supabase Storage에 즉시 저장
   - 홈페이지 새로고침 → 변경사항 즉시 반영

## 테스트 시나리오

### 1단계: 초기 설정

```bash
# 1. Supabase 대시보드에서 'uploads' 버킷 생성 (Public)
# https://app.supabase.com → Storage → Create bucket

# 2. 환경 변수 확인
cat .env
# SUPABASE_URL=...
# SUPABASE_KEY=...
# SUPABASE_SERVICE_ROLE_KEY=...

# 3. 기본 데이터 및 파일 업로드
python seed_to_supabase.py
```

**예상 출력:**
```
============================================================
고려대학교 38대 총학생회 - Supabase 데이터 마이그레이션
============================================================

Supabase Storage 버킷 확인 중...
✓ 'uploads' 버킷 확인 완료

기존 데이터 삭제 중...
  ✓ archive_images 삭제 완료
  ✓ archives 삭제 완료
  ...

일정 데이터 생성 중...
✓ 5개의 일정 생성 완료

공약 데이터 생성 중...
✓ 35개의 공약 생성 완료
✓ 8개의 공약 진행상황 생성 완료

회의록 데이터 생성 중...
✓ 5개의 회의록 생성 완료

회칙 데이터 생성 중...
  ✓ 업로드: regulations/regulation_sejong_main.pdf -> Storage
  ✓ 업로드: regulations/regulation_sejong_general_rules.pdf -> Storage
  ✓ 업로드: regulations/regulation_sejong_additional_rules.pdf -> Storage
  ✓ 업로드: regulations/regulation_science_tech.pdf -> Storage
  ✓ 업로드: regulations/regulation_global_biz.pdf -> Storage
  ✓ 업로드: regulations/regulation_culture_sports.pdf -> Storage
  ✓ 업로드: regulations/regulation_club_union.pdf -> Storage
✓ 11개의 회칙 생성 완료

프로그램 데이터 생성 중...
✓ 5개의 프로그램 생성 완료

조직도 데이터 생성 중...
✓ 41명의 조직도 멤버 생성 완료

배너 데이터 생성 중...
  ✓ 업로드: banners/banner_1.png -> Storage
  ✓ 업로드: banners/banner_2.png -> Storage
✓ 2개의 배너 생성 완료

============================================================
✓ 모든 데이터 마이그레이션 완료!
============================================================
```

### 2단계: 서버 실행 및 홈페이지 확인

```bash
python app.py
```

브라우저에서 http://localhost:1992 접속

**확인 사항:**

#### ✅ 메인 페이지 (/)
- [ ] 배너 2개가 캐러셀로 표시됨 (Supabase Storage에서 로드)
- [ ] 공약 이행률이 표시됨
- [ ] 다가오는 일정 2개 표시
- [ ] 최근 회의록 2개 표시

#### ✅ 공약 페이지 (/promises)
- [ ] 35개의 공약이 카테고리별로 표시됨
  - 학술/복지
  - 시설/환경 개선
  - 학생 참여/소통
  - 행사/프로그램
  - 편의/안전 시설
  - 기타
- [ ] 전체 진행률 표시
- [ ] 각 공약 클릭 시 상세 페이지 표시
- [ ] 진행 상황이 있는 공약은 업데이트 내역 표시

#### ✅ 회칙 페이지 (/regulations)
- [ ] 11개의 회칙이 카테고리별로 표시됨
  - 총학생회 (3개)
  - 단과대학 (6개)
  - 특별기구 (2개)
- [ ] PDF 파일 링크 클릭 시 Supabase Storage에서 파일 로드

#### ✅ 일정 페이지 (/schedule)
- [ ] 5개의 일정이 캘린더에 표시됨

#### ✅ 조직도 페이지 (/organization)
- [ ] 41명의 조직도 멤버 표시
  - 회장단
  - 각 위원회

#### ✅ 프로그램 페이지 (/programs)
- [ ] 5개의 프로그램 표시

### 3단계: 관리자 패널 테스트

```
http://localhost:1992/admin/login
아이디: admin
비밀비호: admin
```

#### ✅ 배너 추가 테스트
1. 관리자 → 배너 관리 → 배너 추가
2. 이미지 업로드 (예: test_banner.png)
3. 제목, 링크 입력
4. 활성화 체크
5. 저장

**확인:**
- [ ] Supabase 대시보드 → Storage → uploads/banners/ 에 파일 업로드됨
- [ ] Supabase 대시보드 → Table Editor → banners 테이블에 데이터 추가됨
- [ ] image_url이 Supabase Storage URL임 (https://xxx.supabase.co/storage/v1/object/public/uploads/banners/...)
- [ ] 메인 페이지 새로고침 → 새 배너가 즉시 표시됨

#### ✅ 회칙 추가 테스트
1. 관리자 → 회칙 관리 → 회칙 추가
2. PDF 파일 업로드 (예: test_regulation.pdf)
3. 카테고리, 제목, 내용 입력
4. 저장

**확인:**
- [ ] Supabase Storage → uploads/regulations/ 에 PDF 업로드됨
- [ ] Supabase → regulations 테이블에 데이터 추가됨
- [ ] 회칙 페이지 새로고침 → 새 회칙이 즉시 표시됨
- [ ] PDF 링크 클릭 → Supabase Storage에서 파일 로드

#### ✅ 데이터 삭제 테스트
1. 관리자 → 배너 관리
2. 방금 추가한 배너 삭제

**확인:**
- [ ] Supabase → banners 테이블에서 데이터 삭제됨
- [ ] Supabase Storage → uploads/banners/ 에서 파일도 삭제됨
- [ ] 메인 페이지 새로고침 → 배너가 사라짐

### 4단계: Heroku 배포 후 테스트

```bash
git push heroku main
```

Heroku 앱 URL 접속

**확인:**
- [ ] 모든 데이터가 표시됨 (Supabase에서 로드)
- [ ] 모든 이미지가 표시됨 (Supabase Storage에서 로드)
- [ ] Heroku dyno 재시작 후에도 데이터 유지됨
- [ ] 관리자 패널에서 추가한 데이터가 즉시 반영됨

## 코드 확인: 데이터가 Supabase에서 오는지 확인

### 공개 페이지 (읽기 전용)

```python
# app.py - 메인 페이지
@app.route('/')
def index():
    banners = db_helper.get_all_banners(is_active=True)  # ← Supabase에서 읽기
    promises_list = db_helper.get_all_promises()          # ← Supabase에서 읽기
    upcoming_schedules = db_helper.get_upcoming_schedules(limit=2)  # ← Supabase
    recent_minutes = db_helper.get_recent_minutes(limit=2)  # ← Supabase
    ...

# app.py - 회칙 페이지
@app.route('/regulations')
def regulations():
    regulations_list = db_helper.get_all_regulations()  # ← Supabase에서 읽기
    ...
```

### 관리자 패널 (읽기 + 쓰기)

```python
# app.py - 배너 추가
@app.route('/admin/banners/add', methods=['GET', 'POST'])
def admin_banner_add():
    if request.method == 'POST':
        file = request.files['image']
        saved_path = save_file(file, 'banners')  # ← Supabase Storage에 업로드

        data = {
            'title': request.form['title'],
            'image_url': saved_path,  # ← Supabase Storage URL
            ...
        }
        db_helper.create_banner(data)  # ← Supabase Database에 저장
        ...
```

## 문제 해결

### 배너나 이미지가 표시되지 않는 경우

1. **Supabase Storage 버킷 확인**
   ```
   Supabase 대시보드 → Storage → uploads 버킷이 Public인지 확인
   ```

2. **파일 URL 확인**
   ```
   Supabase → Table Editor → banners 테이블
   image_url이 https://로 시작하는 Supabase Storage URL인지 확인
   ```

3. **브라우저 개발자 도구 확인**
   ```
   F12 → Network 탭 → 이미지 요청 실패하는지 확인
   ```

### 데이터가 표시되지 않는 경우

1. **Supabase 연결 확인**
   ```bash
   python -c "from database import get_supabase_admin_client; print(get_supabase_admin_client().table('banners').select('*').execute())"
   ```

2. **환경 변수 확인**
   ```bash
   echo $SUPABASE_URL
   echo $SUPABASE_KEY
   ```

3. **seed_to_supabase.py 재실행**
   ```bash
   python seed_to_supabase.py
   ```

## 핵심 포인트

### ✅ 기존 seed data → 홈페이지에 표시
- `seed_to_supabase.py` 실행 → Supabase에 데이터 + 파일 업로드
- 홈페이지 모든 페이지가 `db_helper`를 통해 Supabase에서 데이터 읽기
- **실시간 반영**: Supabase 데이터 변경 → 홈페이지 새로고침 → 즉시 반영

### ✅ 관리자가 새롭게 추가한 데이터 → 즉시 반영 + 저장
- 관리자 패널에서 추가 → `db_helper.create_*()`로 Supabase에 저장
- 파일 업로드 → `save_file()`로 Supabase Storage에 업로드
- 홈페이지 새로고침 → Supabase에서 읽어와서 즉시 표시
- **영구 저장**: 서버 재시작해도 데이터 유지 (Supabase 클라우드에 저장됨)

### ✅ 삭제 시 파일도 함께 삭제
- 데이터베이스 레코드 삭제 → Storage 파일도 자동 삭제
- 예: 배너 삭제 → banners 테이블 + Storage 파일 모두 삭제

## 전체 흐름 요약

```
1. 초기 설정
   ↓
   seed_to_supabase.py 실행
   ↓
   Supabase Database: 데이터 저장
   Supabase Storage: 파일 업로드
   ↓
2. 홈페이지 접속
   ↓
   app.py의 각 페이지가 db_helper로 Supabase에서 데이터 읽기
   ↓
   템플릿에서 데이터 표시 (이미지는 Supabase Storage URL)
   ↓
3. 관리자가 데이터 추가
   ↓
   save_file() → Supabase Storage 업로드
   db_helper.create_*() → Supabase Database 저장
   ↓
4. 홈페이지 새로고침
   ↓
   변경된 데이터 즉시 반영
```

모든 것이 **Supabase 중심**으로 작동하므로, 서버 재시작이나 Heroku 배포와 관계없이 데이터가 안전하게 유지됩니다!
