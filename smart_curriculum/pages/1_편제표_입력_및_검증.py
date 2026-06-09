import streamlit as st
import pandas as pd
from database import supabase, get_departments, get_curriculum_version, get_curriculum_schedules, get_selectable_years

st.set_page_config(page_title="편제표 입력 및 검증", page_icon="📝", layout="wide")

st.title("📝 편제표 입력 및 자동 검증")

if not supabase:
    st.error("데이터베이스에 연결되지 않았습니다. `.streamlit/secrets.toml`을 확인해주세요.")
    st.stop()

departments = get_departments()
if not departments:
    st.warning("등록된 학과가 없습니다. 데이터베이스를 확인해주세요.")
    st.stop()

dept_names = [f"{d['name']} ({d['course_type']})" if d.get('course_type') else d['name'] for d in departments]

col_dept, col_year = st.columns(2)
with col_dept:
    selected_dept_name = st.selectbox("학과 선택", dept_names)
with col_year:
    selected_year = st.selectbox("기준 연도", get_selectable_years())

selected_dept = departments[dept_names.index(selected_dept_name)]
version = get_curriculum_version(selected_dept['id'], selected_year)

st.markdown(f"**{selected_year}학년도 입학생 기준** 편제표를 작성합니다. 입력과 동시에 192학점 이수 요건 등을 실시간으로 검증합니다.")


# --- 엑셀 업로드 통합 기능 ---
with st.expander("📥 엑셀 파일로 편제표 데이터 가져오기 (기존 데이터 초기화/덮어쓰기)", expanded=False):
    st.markdown(f"""
    **{selected_dept_name}**의 **{selected_year}학년도** 편제표와 실무과목 능력단위 데이터를 엑셀에서 파싱하여 초기화합니다.
    업로드 시 해당 학과/연도의 기존 편제표 데이터 및 NCS 능력단위 매핑은 모두 초기화됩니다.
    """)
    uploaded_file = st.file_uploader("편제표 엑셀 파일 선택 (.xlsx)", type=["xlsx"], key="excel_uploader")
    if uploaded_file is not None:
        if st.button("🚀 엑셀 데이터 파싱 및 적용"):
            with st.spinner("엑셀 데이터를 분석하고 데이터베이스를 구성하는 중..."):
                try:
                    # 1. 버전 확인 및 없을 경우 자동 생성
                    active_version = version
                    if not active_version:
                        new_version_res = supabase.table("curriculum_versions").insert({
                            "department_id": selected_dept['id'],
                            "year": selected_year,
                            "target_grade": 0,
                            "framework": "2022 개정",
                            "status": "Draft",
                            "elective_credits": 0
                        }).execute()
                        if not new_version_res.data:
                            raise Exception("교육과정 버전 생성에 실패했습니다.")
                        active_version = new_version_res.data[0]
                    
                    version_id = active_version['id']
                    
                    # 2. 엑셀 파일 파싱
                    xls = pd.ExcelFile(uploaded_file)
                    
                    # 시트 탐색
                    sheet_schedule = None
                    sheet_ncs = None
                    
                    for sheet_name in xls.sheet_names:
                        if sheet_name.startswith("교육과정편제표"):
                            dept_name_raw = sheet_name.replace("교육과정편제표 양식(", "").replace("교육과정편제표(", "").replace(")", "")
                            sheet_course_type = "도제" if "도제" in dept_name_raw else "과정평가형"
                            clean_dept_name = dept_name_raw.replace("-도제반", "").strip()
                            
                            if clean_dept_name == selected_dept['name'] and sheet_course_type == selected_dept['course_type']:
                                sheet_schedule = sheet_name
                        elif sheet_name.startswith("실무과목 능력단위"):
                            dept_name_raw = sheet_name.replace("실무과목 능력단위(", "").replace(")", "")
                            sheet_course_type = "도제" if "도제" in dept_name_raw else "과정평가형"
                            clean_dept_name = dept_name_raw.replace("-도제반", "").strip()
                            
                            if clean_dept_name == selected_dept['name'] and sheet_course_type == selected_dept['course_type']:
                                sheet_ncs = sheet_name
                                
                    if not sheet_schedule:
                        # 유연한 부분 일치 체크
                        for sheet_name in xls.sheet_names:
                            if sheet_name.startswith("교육과정편제표"):
                                dept_name_raw = sheet_name.replace("교육과정편제표 양식(", "").replace("교육과정편제표(", "").replace(")", "")
                                sheet_course_type = "도제" if "도제" in dept_name_raw else "과정평가형"
                                clean_dept_name = dept_name_raw.replace("-도제반", "").strip()
                                
                                if (clean_dept_name in selected_dept['name'] or selected_dept['name'] in clean_dept_name) and sheet_course_type == selected_dept['course_type']:
                                    sheet_schedule = sheet_name
                                    break
                                    
                    if not sheet_schedule:
                        raise Exception(f"엑셀 파일에서 '{selected_dept_name}'에 해당하는 편제표 시트를 찾을 수 없습니다. 시트 명칭을 확인해주세요.")
                    
                    # 기존 스케줄 삭제 (NCS 매핑도 Cascade로 자동 삭제됨)
                    supabase.table("curriculum_schedules").delete().eq("version_id", version_id).execute()
                    
                    # 편제표 데이터 파싱
                    df_sheet = pd.read_excel(xls, sheet_name=sheet_schedule, header=None)
                    
                    # 시작행 찾기
                    start_row = 8
                    for i in range(min(15, len(df_sheet))):
                        row_vals = [str(x).strip() for x in df_sheet.iloc[i].values if pd.notna(x)]
                        if any("과목명" in val for val in row_vals) or any("교과영역" in val for val in row_vals):
                            start_row = i + 1
                            next_row_vals = [str(x).strip() for x in df_sheet.iloc[i+1].values if pd.notna(x)]
                            if "1학기" in next_row_vals or "2학기" in next_row_vals:
                                start_row = i + 2
                            break
                            
                    data_df = df_sheet.iloc[start_row:].copy()
                    data_df[[1, 2]] = data_df[[1, 2]].ffill()
                    
                    schedules_inserted = 0
                    for idx, row in data_df.iterrows():
                        domain = str(row[1]).strip() if pd.notna(row[1]) else "nan"
                        group_cands = [str(row[j]).strip() for j in [3, 2] if j < len(row) and pd.notna(row[j]) and str(row[j]).strip() not in ["nan", "None"]]
                        group = group_cands[0] if group_cands else ""
                        
                        name_candidates = [str(row[i]).strip() for i in [6, 5, 4] if i < len(row) and pd.notna(row[i]) and str(row[i]).strip() != "nan"]
                        subject_name = name_candidates[0] if name_candidates else "nan"
                        
                        skip_keywords = ['소계', '총계', '택', '과목명', '학기별 이수학점', '자율', '동아리', '진로']
                        
                        if pd.notna(row[1]) and "학교 밖 교육과정" in str(row[1]):
                            break
                            
                        if domain == '창의적 체험활동' or subject_name == 'nan' or any(k in subject_name for k in skip_keywords):
                            continue
                            
                        try:
                            base_credits = str(row[7]).replace(".0", "").strip() if len(row) > 7 and pd.notna(row[7]) else "0"
                            operable_credits = str(row[8]).replace(".0", "").strip() if len(row) > 8 and pd.notna(row[8]) else ""
                            
                            if selected_year >= 2026:
                                sem_1_1 = int(float(row[10])) if len(row) > 10 and pd.notna(row[10]) else 0
                                sem_1_2 = int(float(row[11])) if len(row) > 11 and pd.notna(row[11]) else 0
                                sem_2_1 = int(float(row[12])) if len(row) > 12 and pd.notna(row[12]) else 0
                                sem_2_2 = int(float(row[13])) if len(row) > 13 and pd.notna(row[13]) else 0
                                sem_3_1 = int(float(row[14])) if len(row) > 14 and pd.notna(row[14]) else 0
                                sem_3_2 = int(float(row[15])) if len(row) > 15 and pd.notna(row[15]) else 0
                            else:
                                sem_1_1, sem_1_2 = 0, 0
                                sem_2_1 = int(float(row[10])) if len(row) > 10 and pd.notna(row[10]) and str(row[10]).strip() != "-" else 0
                                sem_2_2 = int(float(row[12])) if len(row) > 12 and pd.notna(row[12]) and str(row[12]).strip() != "-" else 0
                                sem_3_1 = int(float(row[14])) if len(row) > 14 and pd.notna(row[14]) and str(row[14]).strip() != "-" else 0
                                sem_3_2 = int(float(row[16])) if len(row) > 16 and pd.notna(row[16]) and str(row[16]).strip() != "-" else 0
                        except (ValueError, TypeError):
                            continue
                            
                        is_elective = False
                        for i in [4, 5]:
                            if i < len(row) and pd.notna(row[i]) and '택' in str(row[i]):
                                is_elective = True
                                break
                                
                        subject_res = supabase.table("subjects").select("id").eq("name", subject_name).execute()
                        if subject_res.data:
                            subject_id = subject_res.data[0]['id']
                            supabase.table("subjects").update({
                                "category": domain,
                                "subject_group": group,
                                "base_credits": base_credits,
                                "operable_credits": operable_credits
                            }).eq("id", subject_id).execute()
                        else:
                            new_sub = supabase.table("subjects").insert({
                                "category": domain,
                                "subject_group": group,
                                "name": subject_name,
                                "base_credits": base_credits,
                                "operable_credits": operable_credits
                            }).execute()
                            if not new_sub.data:
                                continue
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
                        
                        supabase.table("curriculum_schedules").insert(sched_data).execute()
                        schedules_inserted += 1
                        
                    # NCS 능력단위 파싱 및 매핑
                    ncs_inserted = 0
                    if sheet_ncs:
                        df_ncs = pd.read_excel(xls, sheet_name=sheet_ncs, header=None)
                        data_ncs = df_ncs.iloc[8:].copy()
                        data_ncs[1] = data_ncs[1].ffill()
                        
                        for idx, row in data_ncs.iterrows():
                            subject_name = str(row[1]).strip()
                            unit_name = str(row[3]).strip()
                            unit_code = str(row[4]).strip()
                            
                            clean_unit_name = unit_name.replace(" ", "")
                            if pd.isna(row[3]) or unit_name == 'nan' or clean_unit_name == '내용영역(능력단위)' or clean_unit_name == '내용영역합계':
                                continue
                                
                            training_hours = int(row[5]) if pd.notna(row[5]) and str(row[5]).isdigit() else 0
                            unit_level = str(row[6]) if pd.notna(row[6]) else ""
                            
                            sub_res = supabase.table("subjects").select("id").eq("name", subject_name).execute()
                            if not sub_res.data:
                                match_name = subject_name.replace("컨텐츠", "콘텐츠")
                                sub_res = supabase.table("subjects").select("id").eq("name", match_name).execute()
                                
                            if not sub_res.data:
                                continue
                            subject_id = sub_res.data[0]['id']
                            
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
                            
                            supabase.table("ncs_units").insert(ncs_data).execute()
                            ncs_inserted += 1
                            
                    st.success(f"🎉 엑셀 파싱 완료! (편제표 과목 {schedules_inserted}개, NCS 능력단위 {ncs_inserted}개 반영)")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"엑셀 처리 중 오류 발생: {e}")

if not version:
    st.warning(f"{selected_dept_name}의 {selected_year}학년도 버전이 생성되지 않았습니다.")
    st.info("💡 처음이라면 버전 생성 버튼을 눌러 시작하세요.")
    if st.button("신규 버전 생성"):
        new_version = supabase.table("curriculum_versions").insert({
            "department_id": selected_dept['id'],
            "year": selected_year,
            "framework": "2022 개정",
            "status": "Draft",
            "elective_credits": 0
        }).execute()
        st.success("버전이 생성되었습니다!")
        st.rerun()
    st.stop()

st.divider()

# 데이터 로드
schedules = get_curriculum_schedules(version['id'])

general_data = []
special_data = []
creative_saved_credits = 0

for s in schedules:
    sub = s['subjects']
    row_data = {
        "id": s['id'],
        "subject_id": sub['id'],
        "교과군": sub['subject_group'] or "",
        "과목명": sub['name'],
        "필수/선택": "선택" if s.get('is_elective') else "필수",
        "운영 학점": s.get('total_credits', 0),
        "1-1": s['grade_1_sem_1'] or 0,
        "1-2": s['grade_1_sem_2'] or 0,
        "2-1": s['grade_2_sem_1'] or 0,
        "2-2": s['grade_2_sem_2'] or 0,
        "3-1": s['grade_3_sem_1'] or 0,
        "3-2": s['grade_3_sem_2'] or 0,
    }
    
    # 과거 데이터 오류(보통교과로 잘못 저장된 전문과목)를 보정하여 올바른 표로 분류합니다.
    is_special = sub['category'] == "전문교과" or sub['subject_group'] in ["전문공통", "전공일반", "NCS", "전문교과 공통"]
    is_creative = sub['category'] == "창의적 체험활동" or sub['subject_group'] in ["자율활동", "동아리활동", "진로활동"]
    
    # 예전의 '전문교과 공통' 이름을 최신 이름인 '전문공통'으로 통일
    if row_data["교과군"] == "전문교과 공통":
        row_data["교과군"] = "전문공통"
        
    if is_special:
        special_data.append(row_data)
    elif is_creative:
        creative_saved_credits = row_data["운영 학점"]
    else:
        general_data.append(row_data)

columns = ["id", "subject_id", "교과군", "과목명", "필수/선택", "운영 학점", "1-1", "1-2", "2-1", "2-2", "3-1", "3-2"]
df_gen = pd.DataFrame(general_data, columns=columns)
df_spec = pd.DataFrame(special_data, columns=columns)

# 기존 DB에 남아있을 수 있는 공백 및 예전 이름 보정
df_gen["교과군"] = df_gen["교과군"].astype(str).str.strip()
df_spec["교과군"] = df_spec["교과군"].astype(str).str.strip()

group_mapping = {
    "사회": "사회(역사/도덕포함)",
    "역사": "사회(역사/도덕포함)",
    "도덕": "사회(역사/도덕포함)",
    "기술·가정": "기술·가정/제2외국어/한문/교양",
    "기술 가정": "기술·가정/제2외국어/한문/교양",
    "제2외국어": "기술·가정/제2외국어/한문/교양",
    "한문": "기술·가정/제2외국어/한문/교양",
    "교양": "기술·가정/제2외국어/한문/교양",
    "None": None,
    "nan": None,
    "": None
}
df_gen["교과군"] = df_gen["교과군"].replace(group_mapping)
df_spec["교과군"] = df_spec["교과군"].replace({"None": None, "nan": None, "": None})

# 정렬 시 ㄱㄴㄷ 순이 아니라 교육과정 편제표의 공식 순서대로 정렬되도록 Categorical 데이터 타입으로 변환합니다.
gen_order = ["국어", "수학", "영어", "한국사", "사회(역사/도덕포함)", "과학", "체육", "예술", "기술·가정/제2외국어/한문/교양"]
spec_order = ["전문공통", "전공일반", "NCS"]

df_gen["교과군"] = pd.Categorical(df_gen["교과군"], categories=gen_order, ordered=True)
df_spec["교과군"] = pd.Categorical(df_spec["교과군"], categories=spec_order, ordered=True)

# 빈 행은 수동으로 추가하지 않고 st.data_editor의 num_rows="dynamic" 기능에 맡깁니다.
# 이렇게 해야 제목줄을 클릭했을 때 빈칸이 위로 올라오는 문제 없이 ㄱㄴㄷ 순 정렬이 깔끔하게 됩니다.
if df_gen.empty:
    df_gen = pd.DataFrame(columns=columns)

if df_spec.empty:
    df_spec = pd.DataFrame(columns=columns)

st.info(
    "💡 **[사용 방법]**\n"
    "- 보통교과와 전문교과 표가 분리되어 있습니다. 알맞은 표에 과목을 입력하세요.\n"
    "- **교과군**을 클릭하면 해당 영역에 맞는 목록(국영수 또는 전문/NCS)만 나타납니다.\n"
    "- 행을 삭제하려면 왼쪽 회색 숫자(인덱스) 선택 후 `Delete`를 누르세요."
)

st.subheader("📘 보통교과 편제표")
edited_gen = st.data_editor(
    df_gen,
    column_config={
        "id": None, "subject_id": None,
        "교과군": st.column_config.SelectboxColumn(
            "교과군", 
            options=["국어", "수학", "영어", "한국사", "사회(역사/도덕포함)", "과학", "체육", "예술", "기술·가정/제2외국어/한문/교양"], 
            required=True
        ),
        "필수/선택": st.column_config.SelectboxColumn("필수/선택", options=["필수", "선택"], required=True),
        "과목명": st.column_config.TextColumn("과목명", required=True),
        "운영 학점": st.column_config.NumberColumn("운영 학점", disabled=True),
    },
    num_rows="dynamic", use_container_width=True, key="gen_editor"
)

st.subheader("📙 전문교과 편제표")
edited_spec = st.data_editor(
    df_spec,
    column_config={
        "id": None, "subject_id": None,
        "교과군": st.column_config.SelectboxColumn(
            "교과군", 
            options=["전문공통", "전공일반", "NCS"], 
            required=True
        ),
        "필수/선택": st.column_config.SelectboxColumn("필수/선택", options=["필수", "선택"], required=True),
        "과목명": st.column_config.TextColumn("과목명", required=True),
        "운영 학점": st.column_config.NumberColumn("운영 학점", disabled=True),
    },
    num_rows="dynamic", use_container_width=True, key="spec_editor"
)

st.divider()

# --- 창의적 체험활동 자동 적용 ---
st.subheader("📗 창의적 체험활동")
st.markdown("복잡하게 학기별로 나누어 적을 필요 없이 **총 이수시간(또는 총 학점)**만 적으면 전 학기에 자동 분배되어 저장됩니다.")

col_c1, col_c2 = st.columns(2)
with col_c1:
    default_hours = creative_saved_credits * 16 if creative_saved_credits else 288
    creative_hours_input = st.number_input("창의적 체험활동 총 이수시간 (시간)", value=int(default_hours), step=16)
with col_c2:
    creative_credits = creative_hours_input // 16
    st.metric("자동 변환 학점 (16시간=1학점)", f"{creative_credits} 학점")

st.divider()

# --- 자동 검증 시스템 ---
st.markdown("### 🛡️ 실시간 교육과정 검증")

# 데이터를 하나로 합쳐서 총 학점 계산
edited_gen["교과영역"] = "보통교과"
edited_spec["교과영역"] = "전문교과"
edited_df = pd.concat([edited_gen, edited_spec], ignore_index=True)

# 1. 192학점 검증
mandatory_df = edited_df[edited_df["필수/선택"] == "필수"]
mandatory_credits = 0
for col in ["1-1", "1-2", "2-1", "2-2", "3-1", "3-2"]:
    mandatory_credits += pd.to_numeric(mandatory_df[col], errors='coerce').fillna(0).sum()

elective_credits_input = st.number_input("선택과목 이수 인정 학점 (직접 입력)", min_value=0, max_value=192, value=version.get('elective_credits', 0), step=1)

final_total_credits = mandatory_credits + elective_credits_input + creative_credits

col1, col2, col3, col4 = st.columns(4)
col1.metric("필수과목 총점", f"{mandatory_credits} 학점")
col2.metric("선택과목 인정", f"{elective_credits_input} 학점")
col3.metric("창의적 체험활동", f"{creative_credits} 학점")
col4.metric("최종 이수 학점", f"{final_total_credits} 학점", 
            delta="충족" if final_total_credits == 192 else f"{final_total_credits - 192} 부족/초과",
            delta_color="normal" if final_total_credits == 192 else "inverse")

if final_total_credits == 192:
    st.success("✅ **[총 이수학점]** 192학점 기준을 완벽하게 충족했습니다!")
else:
    st.error(f"❌ **[총 이수학점]** 기준(192학점)에 맞지 않습니다. (현재 {final_total_credits}학점)")

# 2. 필수 교과 검증 로직 예시
korean_df = mandatory_df[mandatory_df["교과군"] == "국어"]
korean_credits = korean_df[["1-1", "1-2", "2-1", "2-2", "3-1", "3-2"]].apply(pd.to_numeric, errors='coerce').fillna(0).sum().sum()

if korean_credits < 8:
    st.warning(f"⚠️ **[필수단위 위반]** 국어 교과는 최소 8학점 이상 이수해야 합니다. (현재 편성: {korean_credits}학점)")
else:
    st.success(f"✅ **[필수단위 충족]** 국어 교과 최소 8학점 이수 기준 충족 (현재 편성: {korean_credits}학점)")

st.divider()

if st.button("💾 편제표 저장하기", type="primary"):
    with st.spinner("저장 중..."):
        # 기존 스케줄 삭제
        existing_ids = set(s['id'] for s in schedules)
        kept_ids = set(edited_df['id'].dropna())
        deleted_ids = existing_ids - kept_ids
        for d_id in deleted_ids:
            supabase.table("curriculum_schedules").delete().eq("id", d_id).execute()
            
        # Categorical 속성 때문에 빈 문자열("")로 채우면 에러가 나므로 object 타입으로 변환 후 채웁니다.
        edited_df["교과군"] = edited_df["교과군"].astype(object)
        save_df = edited_df.fillna({"과목명": "", "교과군": "", "1-1": 0, "1-2": 0, "2-1": 0, "2-2": 0, "3-1": 0, "3-2": 0})
        
        for index, row in save_df.iterrows():
            if not str(row["과목명"]).strip() or not str(row["교과군"]).strip():
                continue
                
            is_elective_val = True if row["필수/선택"] == "선택" else False
            
            # 과목 조회/생성 및 업데이트
            subject_res = supabase.table("subjects").select("id").eq("name", row["과목명"]).execute()
            if subject_res.data:
                subject_id = subject_res.data[0]["id"]
                # 기존 과목이라도 교과영역이나 교과군이 변경되었을 수 있으므로 업데이트합니다.
                supabase.table("subjects").update({
                    "category": row["교과영역"],
                    "subject_group": row["교과군"]
                }).eq("id", subject_id).execute()
            else:
                new_sub = supabase.table("subjects").insert({
                    "category": row["교과영역"],
                    "subject_group": row["교과군"],
                    "name": row["과목명"],
                    "base_credits": "0" # Default base credits
                }).execute()
                subject_id = new_sub.data[0]["id"]
                
            sched_data = {
                "version_id": version['id'],
                "subject_id": subject_id,
                "is_elective": is_elective_val,
                "grade_1_sem_1": int(row["1-1"]),
                "grade_1_sem_2": int(row["1-2"]),
                "grade_2_sem_1": int(row["2-1"]),
                "grade_2_sem_2": int(row["2-2"]),
                "grade_3_sem_1": int(row["3-1"]),
                "grade_3_sem_2": int(row["3-2"])
            }
            
            if pd.notna(row.get("id")) and row.get("id"):
                supabase.table("curriculum_schedules").update(sched_data).eq("id", row["id"]).execute()
            else:
                supabase.table("curriculum_schedules").insert(sched_data).execute()
                
        supabase.table("curriculum_versions").update({"elective_credits": elective_credits_input}).eq("id", version['id']).execute()
        
        # 창의적 체험활동 자동 저장 (학기당 균등 분배)
        subject_res = supabase.table("subjects").select("id").eq("name", "창의적 체험활동").execute()
        if subject_res.data:
            c_subject_id = subject_res.data[0]["id"]
        else:
            new_sub = supabase.table("subjects").insert({
                "category": "창의적 체험활동",
                "subject_group": "창의적 체험활동",
                "name": "창의적 체험활동",
                "base_credits": str(creative_credits)
            }).execute()
            c_subject_id = new_sub.data[0]["id"]
            
        base_sem_credit = creative_credits // 6
        remainder = creative_credits % 6
        
        # 남는 학점은 3학년 2학기부터 역순으로 추가 (일반적인 분배 방식)
        dist = [base_sem_credit] * 6
        for i in range(remainder):
            dist[5-i] += 1
            
        c_sched_data = {
            "version_id": version['id'],
            "subject_id": c_subject_id,
            "is_elective": False,
            "grade_1_sem_1": dist[0],
            "grade_1_sem_2": dist[1],
            "grade_2_sem_1": dist[2],
            "grade_2_sem_2": dist[3],
            "grade_3_sem_1": dist[4],
            "grade_3_sem_2": dist[5]
        }
        supabase.table("curriculum_schedules").insert(c_sched_data).execute()
        
    st.success("✅ 저장되었습니다!")
    st.rerun()
