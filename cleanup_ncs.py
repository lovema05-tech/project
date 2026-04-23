import re
with open('c:/Users/User/dev/tutorial/curriculum_manager/.streamlit/secrets.toml', 'r', encoding='utf-8') as f:
    text = f.read()
url = re.search(r'url\s*=\s*"([^"]+)"', text).group(1)
key = re.search(r'key\s*=\s*"([^"]+)"', text).group(1)
from supabase import create_client
supabase = create_client(url, key)

res = supabase.table('ncs_units').select('id, unit_name').execute()
to_delete = []
for r in res.data:
    clean_name = r['unit_name'].replace(" ", "")
    if clean_name == "내용영역합계":
        to_delete.append(r['id'])

if to_delete:
    for i in range(0, len(to_delete), 10):
        batch = to_delete[i:i+10]
        supabase.table('ncs_units').delete().in_('id', batch).execute()
    print(f"Successfully deleted {len(to_delete)} rows.")
else:
    print("No rows found to delete.")
