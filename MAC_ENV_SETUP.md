# Mac 환경에서 .env 파일 생성 가이드

## 방법 1: 터미널에서 직접 생성

```bash
# 프로젝트 루트로 이동
cd /Users/jangseongyu/DynamicNotchKUS/38th_website

# .env.example을 복사하여 .env 파일 생성
cp .env.example .env

# nano 에디터로 .env 파일 편집
nano .env
```

## 방법 2: VS Code나 텍스트 에디터 사용

1. 프로젝트 폴더에서 `.env` 파일 생성
2. 아래 내용을 복사하여 붙여넣기
3. 실제 값으로 교체

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

## ⚠️ 중요: 실제 값으로 교체하세요!

Windows에서 사용했던 Supabase 값들을 그대로 사용하세요:

1. **SUPABASE_URL**: Supabase 프로젝트 URL
2. **SUPABASE_KEY**: anon (public) key
3. **SUPABASE_SERVICE_ROLE_KEY**: service_role key
4. **SECRET_KEY**: 랜덤 문자열 (또는 기존 값 사용)

## 빠른 설정 (터미널)

```bash
# 프로젝트 디렉토리로 이동
cd /Users/jangseongyu/DynamicNotchKUS/38th_website

# .env 파일 생성 (아래 명령어 한 번에 실행)
cat > .env << 'EOF'
SECRET_KEY=your-secret-key
FLASK_ENV=production
FLASK_DEBUG=False
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
PORT=1992
EOF

# .env 파일 권한 설정 (보안)
chmod 600 .env
```

그 후 실제 값으로 편집:
```bash
nano .env
```

## 완료 후 테스트

```bash
python -m flask init-db
```

성공하면:
```
Supabase를 사용하고 있습니다. supabase_schema.sql을 Supabase에 적용해주세요.
기본 관리자 계정 생성 완료 (admin / admin)
```
