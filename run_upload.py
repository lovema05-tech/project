import re
import pandas as pd

with open('c:/Users/User/dev/tutorial/curriculum_manager/.streamlit/secrets.toml', 'r', encoding='utf-8') as f:
    text = f.read()
url = re.search(r'url\s*=\s*"([^"]+)"', text).group(1)
key = re.search(r'key\s*=\s*"([^"]+)"', text).group(1)
from supabase import create_client
supabase = create_client(url, key)

upload_year = 2026
xls = pd.ExcelFile('c:/Users/User/dev/tutorial/2026학년도 신입생 교육과정 편제표_대양고.xlsx')

try:
    for sheet_name in xls.sheet_names:
        if sheet_name.startswith("교육과정편제표 양식"):
            dept_name_raw = sheet_name.replace("교육과정편제표 양식(", "").replace(")", "")
            course_type = "도제" if "도제" in dept_name_raw else "과정평가형"
            clean_dept_name = dept_name_raw.replace("-도제반", "")
            
            dept_res = supabase.table("departments").select("id").eq("name", clean_dept_name).eq("course_type", course_type).execute()
            if not dept_res.data:
                continue
            
            dept_id = dept_res.data[0]['id']
            ver_res = supabase.table("curriculum_versions").select("id").eq("department_id", dept_id).eq("year", upload_year).execute()
            version_id = ver_res.data[0]['id']
            
            supabase.table("curriculum_schedules").delete().eq("version_id", version_id).execute()
            print(f"Deleted schedules for {sheet_name}")
            
            df_sheet = pd.read_excel(xls, sheet_name=sheet_name, header=None)
            data_df = df_sheet.iloc[8:].copy()
            data_df[[1, 2]] = data_df[[1, 2]].fillna(method='ffill')
            
            for idx, row in data_df.iterrows():
                domain = str(row[1]).strip()
                group = str(row[2]).strip()
                
                name_candidates = [str(row[i]).strip() for i in [6, 5, 4] if i < len(row) and pd.notna(row[i]) and str(row[i]).strip() != "nan"]
                subject_name = name_candidates[0] if name_candidates else "nan"
                
                skip_keywords = ['소계', '총계', '택', '과목명', '학기별 이수학점', '자율', '동아리', '진로']
                
                # 하단의 학교 밖 교육과정 상세 내역은 파싱 중단
                if pd.notna(row[1]) and "학교 밖 교육과정" in str(row[1]):
                    break
                    
                if domain == '창의적 체험활동' or subject_name == 'nan' or any(k in subject_name for k in skip_keywords):
                    if domain == '창의적 체험활동' or '총계' in subject_name:
                        break
                    continue
                
                try:
                    base_credits = str(row[7]).replace(".0", "") if len(row) > 7 and pd.notna(row[7]) else "0"
                    sem_1_1 = int(row[10]) if len(row) > 10 and pd.notna(row[10]) else 0
                    sem_1_2 = int(row[11]) if len(row) > 11 and pd.notna(row[11]) else 0
                    sem_2_1 = int(row[12]) if len(row) > 12 and pd.notna(row[12]) else 0
                    sem_2_2 = int(row[13]) if len(row) > 13 and pd.notna(row[13]) else 0
                    sem_3_1 = int(row[14]) if len(row) > 14 and pd.notna(row[14]) else 0
                    sem_3_2 = int(row[15]) if len(row) > 15 and pd.notna(row[15]) else 0
                except ValueError:
                    continue
                
                is_elective = False
                for i in [4, 5]:
                    if i < len(row) and pd.notna(row[i]) and '택' in str(row[i]):
                        is_elective = True
                        break
                
                subject_res = supabase.table("subjects").select("id").eq("name", subject_name).execute()
                if subject_res.data:
                    subject_id = subject_res.data[0]['id']
                    supabase.table("subjects").update({"base_credits": base_credits}).eq("id", subject_id).execute()
                else:
                    new_sub = supabase.table("subjects").insert({
                        "category": domain,
                        "subject_group": group,
                        "name": subject_name,
                        "base_credits": base_credits
                    }).execute()
                    subject_id = new_sub.data[0]['id']
                    
                sched_data = {
                    "version_id": version_id,
                    "subject_id": subject_id,
                    "is_elective": is_elective,
                    "grade_1_sem_1": sem_1_1,
                    "grade_1_sem_2": sem_1_2,
                    "grade_2_sem_1": sem_2_1,
                    "grade_2_sem_2": sem_2_2,
                    "grade_3_sem_1": sem_3_1,
                    "grade_3_sem_2": sem_3_2
                }
                
                exist_sched = supabase.table("curriculum_schedules").select("id").eq("version_id", version_id).eq("subject_id", subject_id).execute()
                if not exist_sched.data:
                    supabase.table("curriculum_schedules").insert(sched_data).execute()
    print("Upload completed successfully!")
except Exception as e:
    print(f"Error during upload: {e}")
