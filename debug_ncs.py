import re
import pandas as pd

with open('c:/Users/User/dev/tutorial/curriculum_manager/.streamlit/secrets.toml', 'r', encoding='utf-8') as f:
    text = f.read()
url = re.search(r'url\s*=\s*"([^"]+)"', text).group(1)
key = re.search(r'key\s*=\s*"([^"]+)"', text).group(1)
from supabase import create_client
supabase = create_client(url, key)

xls = pd.ExcelFile('c:/Users/User/dev/tutorial/2026학년도 신입생 교육과정 편제표_대양고.xlsx')
upload_year = 2026

for sheet_name in xls.sheet_names:
    if sheet_name.startswith("실무과목 능력단위("):
        print(f"Parsing sheet: {sheet_name}")
        dept_name_raw = sheet_name.replace("실무과목 능력단위(", "").replace(")", "")
        course_type = "도제" if "도제" in dept_name_raw else "과정평가형"
        clean_dept_name = dept_name_raw.replace("-도제반", "")
        
        dept_res = supabase.table("departments").select("id").eq("name", clean_dept_name).eq("course_type", course_type).execute()
        if not dept_res.data:
            print("Department not found")
            continue
        
        dept_id = dept_res.data[0]['id']
        ver_res = supabase.table("curriculum_versions").select("id").eq("department_id", dept_id).eq("year", upload_year).execute()
        if not ver_res.data:
            print("Version not found")
            continue
        version_id = ver_res.data[0]['id']
        
        df_ncs = pd.read_excel(xls, sheet_name=sheet_name, header=None)
        data_ncs = df_ncs.iloc[8:].copy()
        data_ncs[1] = data_ncs[1].ffill()
        
        count = 0
        for idx, row in data_ncs.iterrows():
            subject_name = str(row[1]).strip()
            unit_name = str(row[3]).strip()
            unit_code = str(row[4]).strip()
            
            if pd.isna(row[3]) or unit_name == 'nan' or unit_name == '내용영역(능력단위)':
                continue
            
            sub_res = supabase.table("subjects").select("id").eq("name", subject_name).execute()
            if not sub_res.data:
                print(f"Subject not found: {subject_name}")
                continue
            subject_id = sub_res.data[0]['id']
            
            sched_res = supabase.table("curriculum_schedules").select("id").eq("version_id", version_id).eq("subject_id", subject_id).execute()
            if not sched_res.data:
                print(f"Schedule not found for: {subject_name}")
                continue
            
            schedule_id = sched_res.data[0]['id']
            count += 1
            
        print(f"Sheet {sheet_name} found {count} valid units to insert.")
