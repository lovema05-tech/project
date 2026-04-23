import re
import pandas as pd

with open('c:/Users/User/dev/tutorial/curriculum_manager/.streamlit/secrets.toml', 'r', encoding='utf-8') as f:
    text = f.read()
url = re.search(r'url\s*=\s*"([^"]+)"', text).group(1)
key = re.search(r'key\s*=\s*"([^"]+)"', text).group(1)
from supabase import create_client
supabase = create_client(url, key)

res = supabase.table('subjects').select('*').eq('id', '02d7c745-9f61-424c-b5d3-ecf764c6f74b').execute()
print(res.data)
