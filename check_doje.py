import re
import pandas as pd

with open('c:/Users/User/dev/tutorial/curriculum_manager/.streamlit/secrets.toml', 'r', encoding='utf-8') as f:
    text = f.read()
url = re.search(r'url\s*=\s*"([^"]+)"', text).group(1)
key = re.search(r'key\s*=\s*"([^"]+)"', text).group(1)
from supabase import create_client
supabase = create_client(url, key)

dept_res = supabase.table('departments').select('id, name, course_type').eq('course_type', '도제').execute()
for d in dept_res.data:
    print("Doje Department:", d)
    
    ver_res = supabase.table('curriculum_versions').select('id, elective_credits').eq('department_id', d['id']).execute()
    for v in ver_res.data:
        sched_res = supabase.table('curriculum_schedules').select('*, subjects(name)').eq('version_id', v['id']).execute()
        sum_credits = 0
        for r in sched_res.data:
            if not r['is_elective']:
                c = (r['grade_1_sem_1'] or 0) + (r['grade_1_sem_2'] or 0) + (r['grade_2_sem_1'] or 0) + (r['grade_2_sem_2'] or 0) + (r['grade_3_sem_1'] or 0) + (r['grade_3_sem_2'] or 0)
                sum_credits += c
        print("Mandatory Credits for", d['name'], ":", sum_credits)
