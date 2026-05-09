import streamlit as st
import pandas as pd
import math
from supabase import create_client, Client

# Streamlit 페이지 설정
st.set_page_config(page_title="엑셀 업로드", page_icon="📁", layout="wide")

st.markdown("# 📁 초기 데이터 엑셀 업로드")
st.write("대양고 교육과정 편제표 엑셀 파일을 업로드하면 데이터베이스가 자동으로 세팅됩니다.")

# Supabase 클라이언트 초기화
@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = get_supabase()

uploaded_file = st.file_uploader("엑셀 파일 선택", type=["xlsx", "xls"])

if uploaded_file is not None:
    # 옵션을 먼저 보여줍니다 (파일을 미리 읽지 않음)
    upload_year = st.selectbox("업로드할 엑셀의 입학년도(코호트)를 선택하세요", [2026, 2025, 2024])
    
    if st.button(f"{upload_year}학년도 데이터베이스에 엑셀 데이터 전체 밀어넣기"):
        st.info("엑셀 파일을 분석 중입니다. 파일 크기에 따라 10~20초 정도 소요될 수 있습니다...")
        
        try:
            with st.spinner("데이터를 처리하고 Supabase에 저장하는 중... 이 작업은 약 1~2분 정도 소요될 수 있습니다."):
                # 무거운 엑셀 읽기 작업을 버튼 클릭 후로 이동
                xls = pd.ExcelFile(uploaded_file)
                
                # 학과 정보 하드코딩
                departments = [
                    {"name": "e스포츠과", "course_type": "과정평가형"},
                    {"name": "IT네트워크과", "course_type": "과정평가형"},
                    {"name": "전기전자과", "course_type": "과정평가형"},
                    {"name": "전기전자과", "course_type": "도제"}
                ]

                # 1. 학과 저장 및 버전 생성
                for dept in departments:
                    existing_dept = supabase.table("departments").select("id").eq("name", dept["name"]).eq("course_type", dept["course_type"]).execute()
                    if existing_dept.data:
                        dept_id = existing_dept.data[0]['id']
                    else:
                        res = supabase.table("departments").insert(dept).execute()
                        dept_id = res.data[0]['id']
                    
                    existing_ver = supabase.table("curriculum_versions").select("id").eq("department_id", dept_id).eq("year", upload_year).execute()
                    if not existing_ver.data:
                        supabase.table("curriculum_versions").insert({
                            "department_id": dept_id,
                            "year": upload_year,
                            "target_grade": 0,
                            "framework": "2022 개정",
                            "status": "Draft"
                        }).execute()
                
                st.success("✅ 학과 기초 데이터 확인 완료. 세부 과목 파싱을 시작합니다...")
                    
                # 2. 각 학과별 편제표 시트 파싱
                found_any_sheet = False
                for sheet_name in xls.sheet_names:
                    # 시트 이름이 '교육과정편제표'로 시작하면 모두 허용 (양식 이라는 단어가 없어도 됨)
                    if sheet_name.startswith("교육과정편제표"):
                        found_any_sheet = True
                        dept_name_raw = sheet_name.replace("교육과정편제표 양식(", "").replace("교육과정편제표(", "").replace(")", "")
                        
                        course_type = "도제" if "도제" in dept_name_raw else "과정평가형"
                        clean_dept_name = dept_name_raw.replace("-도제반", "")
                        
                        dept_res = supabase.table("departments").select("id").eq("name", clean_dept_name).eq("course_type", course_type).execute()
                        if not dept_res.data:
                            continue
                        
                        dept_id = dept_res.data[0]['id']
                        ver_res = supabase.table("curriculum_versions").select("id").eq("department_id", dept_id).eq("year", upload_year).execute()
                        version_id = ver_res.data[0]['id']
                        
                        # 기존 스케줄 완전 초기화 (중복 방지 및 깔끔한 재업로드 보장)
                        supabase.table("curriculum_schedules").delete().eq("version_id", version_id).execute()
                        
                        df_sheet = pd.read_excel(xls, sheet_name=sheet_name, header=None)
                        
                        # 데이터 시작행 동적 탐색 (과목명, 교과영역 등이 있는 행의 다음 행부터)
                        start_row = 8
                        for i in range(min(15, len(df_sheet))):
                            row_vals = [str(x).strip() for x in df_sheet.iloc[i].values if pd.notna(x)]
                            if any("과목명" in val for val in row_vals) or any("교과영역" in val for val in row_vals):
                                start_row = i + 1
                                # 만약 바로 다음 줄이 '공통', '일반선택' 등 헤더의 연속이라면 한 줄 더 내림
                                next_row_vals = [str(x).strip() for x in df_sheet.iloc[i+1].values if pd.notna(x)]
                                if "1학기" in next_row_vals or "2학기" in next_row_vals:
                                    start_row = i + 2
                                break
                        
                        data_df = df_sheet.iloc[start_row:].copy()
                        data_df[[1, 2]] = data_df[[1, 2]].fillna(method='ffill')
                        
                        for idx, row in data_df.iterrows():
                            domain = str(row[1]).strip() if pd.notna(row[1]) else "nan"
                            group_cands = [str(row[j]).strip() for j in [3, 2] if j < len(row) and pd.notna(row[j]) and str(row[j]).strip() not in ["nan", "None"]]
                            group = group_cands[0] if group_cands else ""
                            
                            # 병합 셀 때문에 과목명이 G(6), F(5), E(4) 중 어디에 있을지 모르므로 오른쪽부터 탐색
                            name_candidates = [str(row[i]).strip() for i in [6, 5, 4] if i < len(row) and pd.notna(row[i]) and str(row[i]).strip() != "nan"]
                            subject_name = name_candidates[0] if name_candidates else "nan"
                            
                            skip_keywords = ['소계', '총계', '택', '과목명', '학기별 이수학점', '자율', '동아리', '진로']
                            
                            # 하단의 학교 밖 교육과정 상세 내역은 이미 위에서 합산된 과목들이므로 파싱 중단
                            if pd.notna(row[1]) and "학교 밖 교육과정" in str(row[1]):
                                break
                                
                            if domain == '창의적 체험활동' or subject_name == 'nan' or any(k in subject_name for k in skip_keywords):
                                if domain == '창의적 체험활동' or '총계' in subject_name:
                                    break
                                # 불필요한 행 건너뜀
                                continue
                            
                            try:
                                # 기본학점(7) 및 운영가능학점(8) 추출
                                base_credits = str(row[7]).replace(".0", "").strip() if len(row) > 7 and pd.notna(row[7]) else "0"
                                operable_credits = str(row[8]).replace(".0", "").strip() if len(row) > 8 and pd.notna(row[8]) else ""
                                
                                # 연도별로 양식이 다를 경우 학점 컬럼 인덱스 분기 처리
                                if upload_year == 2026:
                                    sem_1_1 = int(float(row[10])) if len(row) > 10 and pd.notna(row[10]) else 0
                                    sem_1_2 = int(float(row[11])) if len(row) > 11 and pd.notna(row[11]) else 0
                                    sem_2_1 = int(float(row[12])) if len(row) > 12 and pd.notna(row[12]) else 0
                                    sem_2_2 = int(float(row[13])) if len(row) > 13 and pd.notna(row[13]) else 0
                                    sem_3_1 = int(float(row[14])) if len(row) > 14 and pd.notna(row[14]) else 0
                                    sem_3_2 = int(float(row[15])) if len(row) > 15 and pd.notna(row[15]) else 0
                                else:
                                    # 2025, 2024 학년도 양식: 2학년/3학년만 표시되며 컬럼이 한 칸씩 띄워져 있음 (10, 12, 14, 16)
                                    sem_1_1, sem_1_2 = 0, 0
                                    sem_2_1 = int(float(row[10])) if len(row) > 10 and pd.notna(row[10]) and str(row[10]).strip() != "-" else 0
                                    sem_2_2 = int(float(row[12])) if len(row) > 12 and pd.notna(row[12]) and str(row[12]).strip() != "-" else 0
                                    sem_3_1 = int(float(row[14])) if len(row) > 14 and pd.notna(row[14]) and str(row[14]).strip() != "-" else 0
                                    sem_3_2 = int(float(row[16])) if len(row) > 16 and pd.notna(row[16]) and str(row[16]).strip() != "-" else 0
                            except ValueError:
                                continue
                            
                            # 선택과목 자동 식별 로직 ('택'이라는 단어가 E(4), F(5) 등에 있으면 선택과목으로 지정)
                            is_elective = False
                            for i in [4, 5]:
                                if i < len(row) and pd.notna(row[i]) and '택' in str(row[i]):
                                    is_elective = True
                                    break
                            
                            subject_res = supabase.table("subjects").select("id").eq("name", subject_name).execute()
                            if subject_res.data:
                                subject_id = subject_res.data[0]['id']
                                # 기본학점 및 운영가능학점 업데이트
                                supabase.table("subjects").update({
                                    "base_credits": base_credits,
                                    "operable_credits": operable_credits
                                }).eq("id", subject_id).execute()
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
                            
                            # 중복 과목 삽입 방지 로직
                            exist_sched = supabase.table("curriculum_schedules").select("id").eq("version_id", version_id).eq("subject_id", subject_id).execute()
                            if not exist_sched.data:
                                supabase.table("curriculum_schedules").insert(sched_data).execute()
                
                st.success("✅ 교과 편제표 파싱이 완료되었습니다. 이제 실무과목 능력단위 매핑 데이터를 파싱합니다...")
                
                # 2. 실무과목 능력단위 파싱
                for sheet_name in xls.sheet_names:
                    if sheet_name.startswith("실무과목 능력단위("):
                        dept_name_raw = sheet_name.replace("실무과목 능력단위(", "").replace(")", "")
                        course_type = "도제" if "도제" in dept_name_raw else "과정평가형"
                        clean_dept_name = dept_name_raw.replace("-도제반", "")
                        
                        dept_res = supabase.table("departments").select("id").eq("name", clean_dept_name).eq("course_type", course_type).execute()
                        if not dept_res.data:
                            continue
                        
                        dept_id = dept_res.data[0]['id']
                        ver_res = supabase.table("curriculum_versions").select("id").eq("department_id", dept_id).eq("year", upload_year).execute()
                        if not ver_res.data:
                            continue
                        version_id = ver_res.data[0]['id']
                        
                        df_ncs = pd.read_excel(xls, sheet_name=sheet_name, header=None)
                        data_ncs = df_ncs.iloc[8:].copy()
                        # 과목명(열 인덱스 1)은 병합 셀이므로 ffill로 채움
                        data_ncs[1] = data_ncs[1].ffill()
                        
                        for idx, row in data_ncs.iterrows():
                            subject_name = str(row[1]).strip()
                            unit_name = str(row[3]).strip()
                            unit_code = str(row[4]).strip()
                            
                            # 공백 제거 후 비교 (내용 영역 합계 등 띄어쓰기 대응)
                            clean_unit_name = unit_name.replace(" ", "")
                            if pd.isna(row[3]) or unit_name == 'nan' or clean_unit_name == '내용영역(능력단위)' or clean_unit_name == '내용영역합계':
                                continue
                            
                            training_hours = int(row[5]) if pd.notna(row[5]) and str(row[5]).isdigit() else 0
                            unit_level = str(row[6]) if pd.notna(row[6]) else ""
                            
                            # 1. 과목명으로 subject_id 조회 (컨텐츠/콘텐츠 오타 대응)
                            sub_res = supabase.table("subjects").select("id").eq("name", subject_name).execute()
                            if not sub_res.data:
                                match_name = subject_name.replace("컨텐츠", "콘텐츠")
                                sub_res = supabase.table("subjects").select("id").eq("name", match_name).execute()
                            
                            if not sub_res.data:
                                continue
                            subject_id = sub_res.data[0]['id']
                            
                            # 2. version_id와 subject_id로 schedule_id 조회
                            sched_res = supabase.table("curriculum_schedules").select("id").eq("version_id", version_id).eq("subject_id", subject_id).execute()
                            if not sched_res.data:
                                continue
                            schedule_id = sched_res.data[0]['id']
                            
                            def get_int(val):
                                return int(val) if pd.notna(val) and str(val).isdigit() else 0
                            
                            grade_1_sem_1_credits = get_int(row[7])
                            grade_1_sem_1_hours = get_int(row[8])
                            grade_1_sem_2_credits = get_int(row[9])
                            grade_1_sem_2_hours = get_int(row[10])
                            grade_2_sem_1_credits = get_int(row[11])
                            grade_2_sem_1_hours = get_int(row[12])
                            grade_2_sem_2_credits = get_int(row[13])
                            grade_2_sem_2_hours = get_int(row[14])
                            grade_3_sem_1_credits = get_int(row[15])
                            grade_3_sem_1_hours = get_int(row[16])
                            grade_3_sem_2_credits = get_int(row[17])
                            grade_3_sem_2_hours = get_int(row[18])
                            
                            exist_ncs = supabase.table("ncs_units").select("id").eq("schedule_id", schedule_id).eq("unit_code", unit_code).execute()
                            
                            ncs_data = {
                                "schedule_id": schedule_id,
                                "unit_name": unit_name,
                                "unit_code": unit_code,
                                "unit_level": unit_level,
                                "training_hours": training_hours,
                                "grade_1_sem_1_credits": grade_1_sem_1_credits,
                                "grade_1_sem_1_hours": grade_1_sem_1_hours,
                                "grade_1_sem_2_credits": grade_1_sem_2_credits,
                                "grade_1_sem_2_hours": grade_1_sem_2_hours,
                                "grade_2_sem_1_credits": grade_2_sem_1_credits,
                                "grade_2_sem_1_hours": grade_2_sem_1_hours,
                                "grade_2_sem_2_credits": grade_2_sem_2_credits,
                                "grade_2_sem_2_hours": grade_2_sem_2_hours,
                                "grade_3_sem_1_credits": grade_3_sem_1_credits,
                                "grade_3_sem_1_hours": grade_3_sem_1_hours,
                                "grade_3_sem_2_credits": grade_3_sem_2_credits,
                                "grade_3_sem_2_hours": grade_3_sem_2_hours
                            }
                            
                            if exist_ncs.data:
                                supabase.table("ncs_units").update(ncs_data).eq("id", exist_ncs.data[0]['id']).execute()
                            else:
                                supabase.table("ncs_units").insert(ncs_data).execute()
                
                st.success("🎉 모든 학과의 과목, 편제표, 그리고 **실무과목 능력단위 매핑 데이터**가 자동으로 파싱되어 DB에 저장되었습니다! 이제 왼쪽 메뉴에서 확인해보세요.")
                
        except Exception as e:
            st.error(f"엑셀 처리 중 오류 발생: {e}")

