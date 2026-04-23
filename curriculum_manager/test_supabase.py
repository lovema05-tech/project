import os
import json
import requests
import pandas as pd

SUPABASE_URL = "https://wtgjztwbwxzeqtupmwqv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0Z2p6dHdid3h6ZXF0dXBtd3F2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY4OTM4MjQsImV4cCI6MjA5MjQ2OTgyNH0.HYPB12UOFQKOSfzTACdtRWZQkd77awCliiAt5NcPEPg"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

# Test if departments table exists
url = f"{SUPABASE_URL}/rest/v1/departments?select=*"
response = requests.get(url, headers=headers)

if response.status_code == 200:
    print("SUCCESS: Tables exist. We can proceed with seeding.")
else:
    print(f"ERROR: Cannot query tables. Status: {response.status_code}, Response: {response.text}")
    print("The user might not have run schema.sql yet.")
