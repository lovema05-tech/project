-- 대양고등학교 교육과정 관리 시스템 Supabase DB Schema

-- 1. 학과 테이블 (Departments)
CREATE TABLE IF NOT EXISTS departments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL, -- e스포츠과, IT네트워크과 등
    course_type VARCHAR(50),   -- 과정평가형, 도제 등
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. 교육과정 버전 및 상태 테이블 (Curriculum Versions)
CREATE TABLE IF NOT EXISTS curriculum_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    department_id UUID REFERENCES departments(id) ON DELETE CASCADE,
    year INT NOT NULL,         -- 입학년도 (예: 2026)
    framework VARCHAR(50),     -- 교육과정 체제 (예: 2022 개정)
    status VARCHAR(20) DEFAULT 'Draft', -- 'Draft'(작성중), 'Submitted'(제출됨), 'Approved'(승인됨)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(department_id, year)
);

-- 3. 과목 마스터 테이블 (Subjects)
CREATE TABLE IF NOT EXISTS subjects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category VARCHAR(50),      -- 교과영역 (보통교과, 전문교과 등)
    subject_group VARCHAR(50), -- 교과군 (국어, 수학, 전문공통 등)
    name VARCHAR(100) NOT NULL, -- 과목명 (공통국어1 등)
    subject_type VARCHAR(50),  -- 공통, 일반선택, 진로선택, 실무과목 등
    base_credits VARCHAR(50),  -- 기본 학점
    operable_credits VARCHAR(50), -- 운영가능 학점 (예: 2~40)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. 학점/시수 편성표 (Curriculum Schedules)
CREATE TABLE IF NOT EXISTS curriculum_schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version_id UUID REFERENCES curriculum_versions(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
    
    grade_1_sem_1 INT DEFAULT 0, -- 1학년 1학기 운영학점
    grade_1_sem_2 INT DEFAULT 0, -- 1학년 2학기 운영학점
    grade_2_sem_1 INT DEFAULT 0, -- 2학년 1학기 운영학점
    grade_2_sem_2 INT DEFAULT 0, -- 2학년 2학기 운영학점
    grade_3_sem_1 INT DEFAULT 0, -- 3학년 1학기 운영학점
    grade_3_sem_2 INT DEFAULT 0, -- 3학년 2학기 운영학점
    
    total_credits INT GENERATED ALWAYS AS (
        grade_1_sem_1 + grade_1_sem_2 + grade_2_sem_1 + grade_2_sem_2 + grade_3_sem_1 + grade_3_sem_2
    ) STORED,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(version_id, subject_id)
);

-- 5. NCS 능력단위 매핑 테이블 (NCS Units)
CREATE TABLE IF NOT EXISTS ncs_units (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    schedule_id UUID REFERENCES curriculum_schedules(id) ON DELETE CASCADE,
    unit_name VARCHAR(200) NOT NULL, -- 능력단위명
    unit_code VARCHAR(50),           -- 능력단위코드
    unit_level VARCHAR(50),          -- 능력단위 수준
    training_hours INT,              -- 총 훈련시간 (NCS 기준)
    
    -- 과목에 대한 이론/실습 배분 (사용자 피드백 반영)
    theory_hours INT DEFAULT 0,
    practice_hours INT DEFAULT 0,
    
    -- 이수 학기/학년 매핑용 (학점 및 시간)
    grade_1_sem_1_credits INT DEFAULT 0,
    grade_1_sem_1_hours INT DEFAULT 0,
    grade_1_sem_2_credits INT DEFAULT 0,
    grade_1_sem_2_hours INT DEFAULT 0,
    grade_2_sem_1_credits INT DEFAULT 0,
    grade_2_sem_1_hours INT DEFAULT 0,
    grade_2_sem_2_credits INT DEFAULT 0,
    grade_2_sem_2_hours INT DEFAULT 0,
    grade_3_sem_1_credits INT DEFAULT 0,
    grade_3_sem_1_hours INT DEFAULT 0,
    grade_3_sem_2_credits INT DEFAULT 0,
    grade_3_sem_2_hours INT DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
