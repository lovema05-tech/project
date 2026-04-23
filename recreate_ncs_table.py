import re
with open('c:/Users/User/dev/tutorial/curriculum_manager/.streamlit/secrets.toml', 'r', encoding='utf-8') as f:
    text = f.read()
url = re.search(r'url\s*=\s*"([^"]+)"', text).group(1)
key = re.search(r'key\s*=\s*"([^"]+)"', text).group(1)
from supabase import create_client
supabase = create_client(url, key)

sql = """
DROP TABLE IF EXISTS ncs_units;
CREATE TABLE ncs_units (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    schedule_id UUID REFERENCES curriculum_schedules(id) ON DELETE CASCADE,
    unit_name VARCHAR(200) NOT NULL,
    unit_code VARCHAR(50),
    unit_level VARCHAR(50),
    training_hours INT,
    theory_hours INT DEFAULT 0,
    practice_hours INT DEFAULT 0,
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
"""
# Supabase Python client does not support raw SQL execution directly.
# Let's tell the user to run this SQL in their Supabase SQL editor.
