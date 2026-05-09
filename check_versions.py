import re
with open('c:/Users/User/dev/tutorial/curriculum_manager/.streamlit/secrets.toml', 'r', encoding='utf-8') as f:
    text = f.read()
url = re.search(r'url\s*=\s*"([^"]+)"', text).group(1)
key = re.search(r'key\s*=\s*"([^"]+)"', text).group(1)
from supabase import create_client
supabase = create_client(url, key)

versions = supabase.table('curriculum_versions').select('id, department_id, year, target_grade').execute().data
for v in versions:
    dept = supabase.table('departments').select('name').eq('id', v['department_id']).execute().data[0]['name']
    scheds = supabase.table('curriculum_schedules').select('id').eq('version_id', v['id']).execute().data
    print(f"Dept: {dept}, Year: {v['year']}, Grade: {v['target_grade']}, Scheds: {len(scheds)}")
