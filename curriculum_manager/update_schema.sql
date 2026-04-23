-- 기준학점을 문자열(예: '2~4')로 저장할 수 있도록 타입 변경
ALTER TABLE subjects ALTER COLUMN base_credits TYPE VARCHAR(50);

-- 스케줄에 '필수/선택' 구분을 위한 컬럼 추가 (기본값: 필수(false))
ALTER TABLE curriculum_schedules ADD COLUMN is_elective BOOLEAN DEFAULT FALSE;

-- 교육과정 버전에 '선택과목 이수 인정 학점'을 저장할 컬럼 추가
ALTER TABLE curriculum_versions ADD COLUMN elective_credits INT DEFAULT 0;
