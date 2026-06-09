import streamlit as st
import pandas as pd
from database import supabase, get_departments, get_curriculum_version, get_curriculum_schedules, get_selectable_years

st.set_page_config(page_title="NCS 매칭 및 검증", page_icon="🧩", layout="wide")

st.title("🧩 NCS 능력단위 매핑 및 검증")
st.markdown("전문교과 실무과목과 NCS 능력단위가 올바르게 매핑되었는지, 코드가 일치하는지, 편성 학기가 맞는지 검증합니다.")

if not supabase:
    st.error("데이터베이스에 연결되지 않았습니다.")
    st.stop()

departments = get_departments()
dept_names = [f"{d['name']} ({d['course_type']})" if d.get('course_type') else d['name'] for d in departments]

col_dept, col_year = st.columns(2)
with col_dept:
    selected_dept_name = st.selectbox("학과 선택", dept_names)
with col_year:
    selected_year = st.selectbox("기준 연도", get_selectable_years())


selected_dept = departments[dept_names.index(selected_dept_name)]
version = get_curriculum_version(selected_dept['id'], selected_year)

if not version:
    st.warning("해당 학년도의 편제표 버전이 없습니다. 먼저 편제표를 작성해주세요.")
    st.stop()

# 전문교과 스케줄 가져오기
schedules = get_curriculum_schedules(version['id'])
special_schedules = [s for s in schedules if s['subjects']['category'] == "전문교과"]

if not special_schedules:
    st.info("편성된 전문교과가 없습니다.")
    st.stop()

st.subheader("1. 과목별 NCS 능력단위 매핑")

# 현재 선택된 과목
subject_options = {s['id']: s['subjects']['name'] for s in special_schedules}
selected_sched_id = st.selectbox("전문교과 선택", options=list(subject_options.keys()), format_func=lambda x: subject_options[x])

# 선택된 과목의 스케줄 정보
selected_sched = next(s for s in special_schedules if s['id'] == selected_sched_id)
subject_name = selected_sched['subjects']['name']
subject_semesters = []
for sem in ["1_sem_1", "1_sem_2", "2_sem_1", "2_sem_2", "3_sem_1", "3_sem_2"]:
    if selected_sched.get(f"grade_{sem}"):
        subject_semesters.append(sem.replace("_sem_", "-"))

st.write(f"**[{subject_name}]** 편성 학기: {', '.join(subject_semesters) if subject_semesters else '편성안됨'}")

# NCS 데이터 가져오기
ncs_res = supabase.table("ncs_units").select("*").eq("schedule_id", selected_sched_id).execute()
ncs_data = ncs_res.data

df_ncs = pd.DataFrame(ncs_data)
if df_ncs.empty:
    df_ncs = pd.DataFrame(columns=["id", "unit_name", "unit_code", "training_hours", "grade_1_sem_1_hours", "grade_1_sem_2_hours", "grade_2_sem_1_hours", "grade_2_sem_2_hours", "grade_3_sem_1_hours", "grade_3_sem_2_hours"])

st.markdown("##### 📌 NCS 능력단위 추가/수정 (직접 입력 가능)")
# Streamlit data_editor for easy inline editing
edited_ncs = st.data_editor(
    df_ncs,
    column_config={
        "id": None, # hide
        "unit_name": st.column_config.TextColumn("능력단위명", required=True),
        "unit_code": st.column_config.TextColumn("NCS 코드", required=True),
        "training_hours": st.column_config.NumberColumn("총 훈련시간", min_value=0),
        "grade_1_sem_1_hours": "1-1 시간", "grade_1_sem_2_hours": "1-2 시간",
        "grade_2_sem_1_hours": "2-1 시간", "grade_2_sem_2_hours": "2-2 시간",
        "grade_3_sem_1_hours": "3-1 시간", "grade_3_sem_2_hours": "3-2 시간"
    },
    num_rows="dynamic",
    use_container_width=True
)

if st.button("💾 NCS 능력단위 저장"):
    # Save logic (simplified for brevity)
    for index, row in edited_ncs.iterrows():
        if pd.isna(row.get('unit_name')) or not str(row.get('unit_name')).strip():
            continue
            
        data = {
            "schedule_id": selected_sched_id,
            "unit_name": row['unit_name'],
            "unit_code": row['unit_code'],
            "training_hours": int(row.get('training_hours', 0) or 0),
            "grade_1_sem_1_hours": int(row.get('grade_1_sem_1_hours', 0) or 0),
            "grade_1_sem_2_hours": int(row.get('grade_1_sem_2_hours', 0) or 0),
            "grade_2_sem_1_hours": int(row.get('grade_2_sem_1_hours', 0) or 0),
            "grade_2_sem_2_hours": int(row.get('grade_2_sem_2_hours', 0) or 0),
            "grade_3_sem_1_hours": int(row.get('grade_3_sem_1_hours', 0) or 0),
            "grade_3_sem_2_hours": int(row.get('grade_3_sem_2_hours', 0) or 0),
        }
        if pd.notna(row.get('id')):
            supabase.table("ncs_units").update(data).eq("id", row['id']).execute()
        else:
            supabase.table("ncs_units").insert(data).execute()
    st.success("저장되었습니다!")
    st.rerun()

st.divider()

st.subheader("2. 🔍 학과 전체 NCS 자동 검증")

if st.button("전체 검증 실행", type="primary"):
    with st.spinner("검증 중..."):
        all_ncs_res = supabase.table("ncs_units").select("*, curriculum_schedules(id, subjects(name), grade_1_sem_1, grade_1_sem_2, grade_2_sem_1, grade_2_sem_2, grade_3_sem_1, grade_3_sem_2)").execute()
        # Filter only for this version
        valid_sched_ids = [s['id'] for s in special_schedules]
        dept_ncs = [n for n in all_ncs_res.data if n['schedule_id'] in valid_sched_ids]
        
        errors = []
        code_name_map = {}
        
        for n in dept_ncs:
            code = n['unit_code']
            name = n['unit_name']
            
            # Rule 1: 코드/명칭 불일치 검증
            if code in code_name_map and code_name_map[code] != name:
                errors.append(f"⚠️ [명칭 불일치] 코드 '{code}'가 '{code_name_map[code]}'와 '{name}' 두 가지 명칭으로 사용되고 있습니다.")
            else:
                code_name_map[code] = name
                
            # Rule 2: 학기 매핑 검증
            sched = n['curriculum_schedules']
            sub_name = sched['subjects']['name']
            for sem in ["1_sem_1", "1_sem_2", "2_sem_1", "2_sem_2", "3_sem_1", "3_sem_2"]:
                subj_credit = sched.get(f"grade_{sem}") or 0
                ncs_hours = n.get(f"grade_{sem}_hours") or 0
                
                if ncs_hours > 0 and subj_credit == 0:
                    errors.append(f"❌ [학기 불일치] '{sub_name}' 과목은 {sem.replace('_sem_', '-')} 학기에 편성되지 않았는데, 해당 학기에 NCS 시간({name})이 배정되어 있습니다.")
        
        if not errors:
            st.success("🎉 완벽합니다! NCS 코드 불일치나 학기 매핑 오류가 발견되지 않았습니다.")
        else:
            st.error(f"총 {len(errors)}개의 오류가 발견되었습니다.")
            for e in set(errors): # Remove duplicates
                st.write(e)
