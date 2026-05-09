-- 1. curriculum_versions 테이블에 target_grade 컬럼 추가 (1, 2, 3학년 구분용)
-- 기본값은 0 (통합본)으로 설정하여 기존 데이터와 호환성 유지
ALTER TABLE curriculum_versions ADD COLUMN IF NOT EXISTS target_grade INT DEFAULT 0;

-- 2. 기존의 UNIQUE 제약 조건 제거 (department_id, year 조합 고유 제약)
ALTER TABLE curriculum_versions DROP CONSTRAINT IF EXISTS curriculum_versions_department_id_year_key;

-- 3. 새로운 UNIQUE 제약 조건 추가 (학과, 연도, 대상학년 조합이 고유하도록 변경)
ALTER TABLE curriculum_versions ADD CONSTRAINT curriculum_versions_unique_dept_year_grade UNIQUE (department_id, year, target_grade);
