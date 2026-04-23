import re
with open('c:/Users/User/dev/tutorial/curriculum_manager/.streamlit/secrets.toml', 'r', encoding='utf-8') as f:
    text = f.read()
url = re.search(r'url\s*=\s*"([^"]+)"', text).group(1)
key = re.search(r'key\s*=\s*"([^"]+)"', text).group(1)
from supabase import create_client
supabase = create_client(url, key)

res = supabase.table('ncs_units').select('id, unit_name').execute()
unique_names = list(set([r['unit_name'] for r in res.data]))
for name in unique_names:
    if '내용' in name or '영역' in name or '합계' in name:
        print(f"FOUND: '{name}' (length: {len(name)})")
