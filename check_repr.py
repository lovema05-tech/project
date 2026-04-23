import re
with open('c:/Users/User/dev/tutorial/curriculum_manager/.streamlit/secrets.toml', 'r', encoding='utf-8') as f:
    text = f.read()
url = re.search(r'url\s*=\s*"([^"]+)"', text).group(1)
key = re.search(r'key\s*=\s*"([^"]+)"', text).group(1)
from supabase import create_client
supabase = create_client(url, key)

res = supabase.table('ncs_units').select('id, unit_name').execute()
for r in res.data:
    name = r['unit_name']
    if '내' in name or '영' in name or '합' in name or '계' in name:
        print(f"ID: {r['id']} | NAME: {repr(name)}")
