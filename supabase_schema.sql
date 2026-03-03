-- ============================================
-- 고려대학교 38대 총학생회 웹사이트
-- Supabase 데이터베이스 스키마
-- ============================================

-- 1. Admin 테이블 (관리자)
CREATE TABLE IF NOT EXISTS admins (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(200) NOT NULL,
    name VARCHAR(100) NOT NULL,
    is_super_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Schedule 테이블 (일정)
CREATE TABLE IF NOT EXISTS schedules (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ,
    location VARCHAR(200),
    category VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Promise 테이블 (공약)
CREATE TABLE IF NOT EXISTS promises (
    id BIGSERIAL PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    detailed_description TEXT,
    progress_rate INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT '진행중',
    "order" INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. PromiseProgress 테이블 (공약 진행 상황)
CREATE TABLE IF NOT EXISTS promise_progress (
    id BIGSERIAL PRIMARY KEY,
    promise_id BIGINT NOT NULL REFERENCES promises(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    date TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. MeetingMinutes 테이블 (회의록)
CREATE TABLE IF NOT EXISTS meeting_minutes (
    id BIGSERIAL PRIMARY KEY,
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

-- 6. Regulation 테이블 (회칙)
CREATE TABLE IF NOT EXISTS regulations (
    id BIGSERIAL PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    pdf_filename VARCHAR(500),
    file_url VARCHAR(500),
    "order" INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Program 테이블 (교내 프로그램)
CREATE TABLE IF NOT EXISTS programs (
    id BIGSERIAL PRIMARY KEY,
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

-- 8. Organization 테이블 (조직도)
CREATE TABLE IF NOT EXISTS organizations (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    position VARCHAR(100) NOT NULL,
    department VARCHAR(100),
    major VARCHAR(100),
    student_id VARCHAR(20),
    phone VARCHAR(50),
    email VARCHAR(100),
    photo_url VARCHAR(500),
    "order" INTEGER DEFAULT 0,
    parent_id BIGINT REFERENCES organizations(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 9. Banner 테이블 (메인 페이지 배너)
CREATE TABLE IF NOT EXISTS banners (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    image_url VARCHAR(500) NOT NULL,
    link VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    is_event_banner BOOLEAN DEFAULT FALSE,
    "order" INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 10. Archive 테이블 (아카이브)
CREATE TABLE IF NOT EXISTS archives (
    id BIGSERIAL PRIMARY KEY,
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

-- 11. ArchiveImage 테이블 (아카이브 이미지)
CREATE TABLE IF NOT EXISTS archive_images (
    id BIGSERIAL PRIMARY KEY,
    archive_id BIGINT NOT NULL REFERENCES archives(id) ON DELETE CASCADE,
    image_url VARCHAR(500) NOT NULL,
    caption VARCHAR(500),
    "order" INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 12. MeetingRoomBooking 테이블 (회의실 대관)
CREATE TABLE IF NOT EXISTS meeting_room_bookings (
    id BIGSERIAL PRIMARY KEY,
    room_number INTEGER NOT NULL CHECK (room_number BETWEEN 1 AND 4),
    applicant_name VARCHAR(100) NOT NULL,
    applicant_email VARCHAR(200) NOT NULL,
    applicant_phone VARCHAR(50),
    organization VARCHAR(200),
    purpose TEXT NOT NULL,
    booking_date DATE NOT NULL,
    start_time VARCHAR(10) NOT NULL,
    end_time VARCHAR(10) NOT NULL,
    attendees INTEGER DEFAULT 1,
    status VARCHAR(20) DEFAULT 'pending',
    admin_note TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 13. HistoryLog 테이블 (관리자 작업 히스토리)
CREATE TABLE IF NOT EXISTS history_logs (
    id BIGSERIAL PRIMARY KEY,
    worker_name VARCHAR(100) NOT NULL,
    work_content TEXT NOT NULL,
    is_checked BOOLEAN DEFAULT FALSE,
    checked_by VARCHAR(100),
    checked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 인덱스 생성
-- ============================================

-- 일정 검색 최적화
CREATE INDEX IF NOT EXISTS idx_schedules_start_date ON schedules(start_date DESC);
CREATE INDEX IF NOT EXISTS idx_schedules_category ON schedules(category);

-- 공약 검색 최적화
CREATE INDEX IF NOT EXISTS idx_promises_category ON promises(category);
CREATE INDEX IF NOT EXISTS idx_promises_order ON promises("order");
CREATE INDEX IF NOT EXISTS idx_promise_progress_promise_id ON promise_progress(promise_id);

-- 회의록 검색 최적화
CREATE INDEX IF NOT EXISTS idx_meeting_minutes_date ON meeting_minutes(meeting_date DESC);

-- 회칙 검색 최적화
CREATE INDEX IF NOT EXISTS idx_regulations_category ON regulations(category);
CREATE INDEX IF NOT EXISTS idx_regulations_order ON regulations("order");

-- 프로그램 검색 최적화
CREATE INDEX IF NOT EXISTS idx_programs_active ON programs(is_active);
CREATE INDEX IF NOT EXISTS idx_programs_created ON programs(created_at DESC);

-- 조직도 검색 최적화
CREATE INDEX IF NOT EXISTS idx_organizations_position ON organizations(position);
CREATE INDEX IF NOT EXISTS idx_organizations_order ON organizations("order");

-- 배너 검색 최적화
CREATE INDEX IF NOT EXISTS idx_banners_active ON banners(is_active);
CREATE INDEX IF NOT EXISTS idx_banners_order ON banners("order");

-- 아카이브 검색 최적화
CREATE INDEX IF NOT EXISTS idx_archives_active ON archives(is_active);
CREATE INDEX IF NOT EXISTS idx_archives_event_date ON archives(event_date DESC);
CREATE INDEX IF NOT EXISTS idx_archive_images_archive_id ON archive_images(archive_id);

-- 히스토리 검색 최적화
CREATE INDEX IF NOT EXISTS idx_history_logs_created_at ON history_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_history_logs_checked ON history_logs(is_checked);

-- 회의실 대관 검색 최적화
CREATE INDEX IF NOT EXISTS idx_meeting_room_bookings_date ON meeting_room_bookings(booking_date DESC);
CREATE INDEX IF NOT EXISTS idx_meeting_room_bookings_room ON meeting_room_bookings(room_number);
CREATE INDEX IF NOT EXISTS idx_meeting_room_bookings_status ON meeting_room_bookings(status);

-- ============================================
-- Row Level Security (RLS) 정책
-- ============================================

-- RLS 활성화
ALTER TABLE admins ENABLE ROW LEVEL SECURITY;
ALTER TABLE schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE promises ENABLE ROW LEVEL SECURITY;
ALTER TABLE promise_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE meeting_minutes ENABLE ROW LEVEL SECURITY;
ALTER TABLE regulations ENABLE ROW LEVEL SECURITY;
ALTER TABLE programs ENABLE ROW LEVEL SECURITY;
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE banners ENABLE ROW LEVEL SECURITY;
ALTER TABLE archives ENABLE ROW LEVEL SECURITY;
ALTER TABLE archive_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE history_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE meeting_room_bookings ENABLE ROW LEVEL SECURITY;

-- 모든 테이블에 대한 공개 읽기 정책 (SELECT)
CREATE POLICY "Public read access" ON schedules FOR SELECT USING (true);
CREATE POLICY "Public read access" ON promises FOR SELECT USING (true);
CREATE POLICY "Public read access" ON promise_progress FOR SELECT USING (true);
CREATE POLICY "Public read access" ON meeting_minutes FOR SELECT USING (true);
CREATE POLICY "Public read access" ON regulations FOR SELECT USING (true);
CREATE POLICY "Public read access" ON programs FOR SELECT USING (true);
CREATE POLICY "Public read access" ON organizations FOR SELECT USING (true);
CREATE POLICY "Public read access" ON banners FOR SELECT USING (true);
CREATE POLICY "Public read access" ON archives FOR SELECT USING (true);
CREATE POLICY "Public read access" ON archive_images FOR SELECT USING (true);
CREATE POLICY "Public read access" ON history_logs FOR SELECT USING (true);

-- Admins 테이블은 service_role 키로만 접근 가능
CREATE POLICY "Admin full access" ON admins FOR ALL USING (auth.role() = 'service_role');

-- 관리자 인증 후 모든 작업 가능 (service_role 키 사용 시)
CREATE POLICY "Authenticated write access" ON schedules FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Authenticated write access" ON promises FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Authenticated write access" ON promise_progress FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Authenticated write access" ON meeting_minutes FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Authenticated write access" ON regulations FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Authenticated write access" ON programs FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Authenticated write access" ON organizations FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Authenticated write access" ON banners FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Authenticated write access" ON archives FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Authenticated write access" ON archive_images FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Public read access" ON meeting_room_bookings FOR SELECT USING (true);
CREATE POLICY "Authenticated write access" ON meeting_room_bookings FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Public insert access" ON meeting_room_bookings FOR INSERT WITH CHECK (true);

-- ============================================
-- 트리거: updated_at 자동 업데이트
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_schedules_updated_at BEFORE UPDATE ON schedules FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_promises_updated_at BEFORE UPDATE ON promises FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_meeting_minutes_updated_at BEFORE UPDATE ON meeting_minutes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_regulations_updated_at BEFORE UPDATE ON regulations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_programs_updated_at BEFORE UPDATE ON programs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_banners_updated_at BEFORE UPDATE ON banners FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_archives_updated_at BEFORE UPDATE ON archives FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_meeting_room_bookings_updated_at BEFORE UPDATE ON meeting_room_bookings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
