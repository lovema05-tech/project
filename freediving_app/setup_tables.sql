-- 브로시스 프리다이빙 예약 웹앱 데이터베이스 스키마

-- 1. 공지사항 테이블
CREATE TABLE IF NOT EXISTS fd_announcements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. 교육 일정 테이블
CREATE TABLE IF NOT EXISTS fd_schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    schedule_date DATE NOT NULL,
    schedule_time TIME NOT NULL,
    location TEXT NOT NULL,
    max_capacity INTEGER NOT NULL DEFAULT 4,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. 신청 내역 테이블
CREATE TABLE IF NOT EXISTS fd_applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    schedule_id UUID REFERENCES fd_schedules(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    birthdate TEXT NOT NULL,
    liability_consent BOOLEAN NOT NULL DEFAULT FALSE,
    rental_equipment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- RLS 정책 설정 (간편한 데모용으로 모든 접근 허용, 운영 환경에서는 제한 필요)
ALTER TABLE fd_announcements ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow anonymous read fd_announcements" ON fd_announcements FOR SELECT USING (true);
CREATE POLICY "Allow anonymous insert fd_announcements" ON fd_announcements FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow anonymous update fd_announcements" ON fd_announcements FOR UPDATE USING (true);
CREATE POLICY "Allow anonymous delete fd_announcements" ON fd_announcements FOR DELETE USING (true);

ALTER TABLE fd_schedules ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow anonymous read fd_schedules" ON fd_schedules FOR SELECT USING (true);
CREATE POLICY "Allow anonymous insert fd_schedules" ON fd_schedules FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow anonymous update fd_schedules" ON fd_schedules FOR UPDATE USING (true);
CREATE POLICY "Allow anonymous delete fd_schedules" ON fd_schedules FOR DELETE USING (true);

ALTER TABLE fd_applications ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow anonymous read fd_applications" ON fd_applications FOR SELECT USING (true);
CREATE POLICY "Allow anonymous insert fd_applications" ON fd_applications FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow anonymous update fd_applications" ON fd_applications FOR UPDATE USING (true);
CREATE POLICY "Allow anonymous delete fd_applications" ON fd_applications FOR DELETE USING (true);
