import re
with open('c:/Users/User/dev/tutorial/curriculum_manager/.streamlit/secrets.toml', 'r', encoding='utf-8') as f:
    text = f.read()
url = re.search(r'url\s*=\s*"([^"]+)"', text).group(1)
key = re.search(r'key\s*=\s*"([^"]+)"', text).group(1)
from supabase import create_client
supabase = create_client(url, key)

versions = supabase.table('curriculum_versions').select('id, target_grade').execute().data
for v in versions:
    scheds = supabase.table('curriculum_schedules').select('id').eq('version_id', v['id']).execute().data
    print(f"Target Grade {v['target_grade']}: {len(scheds)} schedules")
