import re
import pandas as pd

with open('c:/Users/User/dev/tutorial/curriculum_manager/.streamlit/secrets.toml', 'r', encoding='utf-8') as f:
    text = f.read()
url = re.search(r'url\s*=\s*"([^"]+)"', text).group(1)
key = re.search(r'key\s*=\s*"([^"]+)"', text).group(1)

from supabase import create_client
supabase = create_client(url, key)

res = supabase.table('curriculum_schedules').select('*, subjects(name)').eq('version_id', '8c43ca77-7645-4aa7-934d-205e019e112c').execute()
sum_credits = 0
for r in res.data:
    if not r['is_elective']:
        c = (r['grade_1_sem_1'] or 0) + (r['grade_1_sem_2'] or 0) + (r['grade_2_sem_1'] or 0) + (r['grade_2_sem_2'] or 0) + (r['grade_3_sem_1'] or 0) + (r['grade_3_sem_2'] or 0)
        sum_credits += c
        print(f"{r['subjects']['name']}: {c}")
print('Total mandatory credits:', sum_credits)
