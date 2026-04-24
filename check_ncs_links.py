import re
import pandas as pd
with open('c:/Users/User/dev/tutorial/curriculum_manager/.streamlit/secrets.toml', 'r', encoding='utf-8') as f:
    text = f.read()
url = re.search(r'url\s*=\s*"([^"]+)"', text).group(1)
key = re.search(r'key\s*=\s*"([^"]+)"', text).group(1)
from supabase import create_client
supabase = create_client(url, key)

res = supabase.table('ncs_units').select('id, schedule_id, unit_name').execute()
print(f"Total NCS units: {len(res.data)}")
null_sched = [r for r in res.data if r['schedule_id'] is None]
print(f"Units with NULL schedule_id: {len(null_sched)}")
if res.data:
    print("Sample row:", res.data[0])
