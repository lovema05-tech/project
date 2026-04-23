import re
with open('c:/Users/User/dev/tutorial/curriculum_manager/.streamlit/secrets.toml', 'r', encoding='utf-8') as f:
    text = f.read()
url = re.search(r'url\s*=\s*"([^"]+)"', text).group(1)
key = re.search(r'key\s*=\s*"([^"]+)"', text).group(1)
from supabase import create_client
supabase = create_client(url, key)
res = supabase.table('curriculum_schedules').select('*, subjects(name)').eq('version_id', '8c43ca77-7645-4aa7-934d-205e019e112c').execute()
for r in res.data:
    if r['subjects']['name'] in ['게임콘텐츠제작', '전자제품생산', '스마트문화앱콘텐츠제작']:
        print(f"{r['subjects']['name']}: {r['is_elective']}")
