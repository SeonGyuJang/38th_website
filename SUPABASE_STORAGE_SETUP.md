# Supabase Storage 설정 가이드

## 개요

Heroku의 임시(ephemeral) 파일 시스템 문제를 해결하기 위해 Supabase Storage를 통합했습니다. 이제 모든 파일(PDF, 이미지 등)이 클라우드에 저장되어 서버 재시작 후에도 유지됩니다.

## 1단계: Supabase Storage 버킷 생성

### Supabase 대시보드에서 설정:

1. **Supabase 프로젝트 접속**
   - https://app.supabase.com 에 로그인
   - 프로젝트 선택

2. **Storage 버킷 생성**
   - 왼쪽 메뉴에서 `Storage` 클릭
   - `Create a new bucket` 버튼 클릭
   - 버킷 설정:
     - **Name**: `uploads`
     - **Public bucket**: ✅ 체크 (중요!)
     - **File size limit**: 기본값 사용
   - `Create bucket` 클릭

3. **버킷 정책 확인**
   - 생성된 `uploads` 버킷 클릭
   - `Policies` 탭 확인
   - Public 버킷이므로 별도 정책 설정 불필요

## 2단계: 로컬 파일 마이그레이션 (옵션)

현재 로컬 PC에 있는 파일들을 Supabase Storage로 업로드하려면:

### 마이그레이션 스크립트 실행:

```bash
python migrate_files_to_storage.py
```

### 스크립트가 수행하는 작업:

1. **버킷 존재 확인**
   - `uploads` 버킷이 있는지 확인
   - 없으면 수동 생성 안내

2. **파일 업로드**
   - `static/uploads/` 폴더의 모든 파일을 Supabase Storage로 업로드
   - 하위 폴더 구조 유지:
     - `banners/` - 배너 이미지
     - `regulations/` - 회칙 PDF 파일
     - `archives/` - 아카이브 이미지
     - `programs/` - 프로그램 이미지
     - `profiles/` - 조직도 멤버 사진
     - `minutes/` - 회의록 파일

3. **데이터베이스 URL 업데이트**
   - 기존 로컬 파일 경로를 Supabase Storage URL로 변경
   - 예: `/static/uploads/banners/image.png` → `https://xxx.supabase.co/storage/v1/object/public/uploads/banners/image.png`

### 수동 파일 업로드 (대안):

마이그레이션 스크립트 대신 Supabase 대시보드에서 직접 파일을 업로드할 수 있습니다:

1. Storage > `uploads` 버킷 선택
2. 폴더 생성 (banners, regulations, archives 등)
3. 각 폴더에 파일 드래그 앤 드롭
4. 데이터베이스의 URL을 수동으로 업데이트

## 3단계: 관리자 패널 파일 업로드 동작 확인

### 자동으로 Supabase Storage 사용:

이제 관리자 패널에서 파일을 업로드하면 자동으로 Supabase Storage에 저장됩니다:

- ✅ **배너 관리**: 배너 이미지 → `uploads/banners/`
- ✅ **회칙 관리**: PDF 파일 → `uploads/regulations/`
- ✅ **프로그램 관리**: 프로그램 이미지 → `uploads/programs/`
- ✅ **조직도 관리**: 멤버 사진 → `uploads/profiles/`
- ✅ **아카이브 관리**: 아카이브 이미지 → `uploads/archives/`
- ✅ **회의록 관리**: 회의록 파일 → `uploads/minutes/`

### 파일 삭제 기능:

데이터베이스에서 레코드를 삭제하면 Supabase Storage의 파일도 자동으로 삭제됩니다:

- 회칙 삭제 → PDF 파일도 삭제
- 배너 삭제 → 이미지 파일도 삭제
- 아카이브 삭제 → 연결된 모든 이미지 일괄 삭제
- 프로그램 삭제 → 이미지 파일도 삭제
- 조직도 멤버 삭제 → 사진 파일도 삭제
- 회의록 삭제 → 파일도 삭제

## 4단계: Heroku 배포

변경사항을 Heroku에 배포:

```bash
git push heroku main
```

또는 GitHub 연동이 되어있다면 자동 배포됩니다.

## 주요 변경사항

### 새로 추가된 파일:

1. **`storage_helper.py`**
   - Supabase Storage 업로드/삭제/마이그레이션 기능
   - 타임스탬프 기반 고유 파일명 생성
   - 공개 URL 자동 생성

2. **`migrate_files_to_storage.py`**
   - 로컬 파일을 Supabase Storage로 일괄 마이그레이션
   - 데이터베이스 URL 자동 업데이트
   - 버킷 존재 확인

### 수정된 파일:

1. **`app.py`**
   - `save_file()`: 로컬 저장 → Supabase Storage 업로드
   - `delete_file()`: Supabase Storage 파일 삭제 함수 추가

2. **`supabase_helpers.py`**
   - 모든 `delete_*()` 함수에 파일 삭제 로직 추가
   - 데이터베이스 레코드 삭제 시 Storage 파일도 함께 삭제

## 파일 저장 구조

```
Supabase Storage (uploads 버킷)
├── banners/          # 배너 이미지
├── regulations/      # 회칙 PDF 파일
├── archives/         # 아카이브 이미지
├── programs/         # 프로그램 이미지
├── profiles/         # 조직도 멤버 사진
└── minutes/          # 회의록 파일
```

## 파일명 규칙

업로드되는 파일명 형식:
```
{타임스탬프}_{원본파일명}
예: 20251220_143022_banner.png
```

이를 통해 파일명 충돌을 방지합니다.

## 문제 해결

### 버킷이 없다는 오류가 발생하는 경우:

```
⚠ 'uploads' 버킷이 없습니다.
```

**해결**: Supabase 대시보드에서 `uploads` 버킷을 생성하세요 (1단계 참조)

### 파일 업로드 오류:

```
파일 업로드 오류: ...
```

**체크리스트**:
1. Supabase 프로젝트 URL과 API 키가 `.env`에 정확히 설정되었는지 확인
2. `uploads` 버킷이 Public으로 설정되었는지 확인
3. 파일 확장자가 허용된 확장자인지 확인 (`config.py`의 `ALLOWED_EXTENSIONS`)

### 마이그레이션 후 이미지가 보이지 않는 경우:

**체크리스트**:
1. 데이터베이스의 URL이 Supabase Storage URL로 업데이트되었는지 확인
2. 브라우저 캐시 삭제 후 새로고침
3. Supabase Storage에서 파일이 실제로 업로드되었는지 확인

## 장점

### Before (로컬 파일 시스템):
- ❌ Heroku 재시작 시 파일 삭제됨
- ❌ 여러 dyno 간 파일 공유 불가
- ❌ 백업 어려움

### After (Supabase Storage):
- ✅ 영구 저장 (클라우드)
- ✅ 모든 서버 인스턴스에서 동일한 파일 접근
- ✅ Supabase 자동 백업
- ✅ CDN을 통한 빠른 파일 전송
- ✅ 확장성 우수

## 참고 자료

- [Supabase Storage 문서](https://supabase.com/docs/guides/storage)
- [Heroku Ephemeral Filesystem](https://devcenter.heroku.com/articles/dynos#ephemeral-filesystem)
