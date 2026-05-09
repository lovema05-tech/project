import re
with open('c:/Users/User/dev/tutorial/curriculum_manager/.streamlit/secrets.toml', 'r', encoding='utf-8') as f:
    text = f.read()
url = re.search(r'url\s*=\s*"([^"]+)"', text).group(1)
key = re.search(r'key\s*=\s*"([^"]+)"', text).group(1)
with open('c:/Users/User/dev/tutorial/freediving-web/.env.local', 'w', encoding='utf-8') as f:
    f.write(f'VITE_SUPABASE_URL={url}\nVITE_SUPABASE_ANON_KEY={key}\n')
print('Created .env.local')
