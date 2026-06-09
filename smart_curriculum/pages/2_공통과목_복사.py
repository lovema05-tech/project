import streamlit as st
import pandas as pd
from database import supabase, get_departments, get_curriculum_version, get_curriculum_schedules, get_selectable_years

st.set_page_config(page_title="공통과목 일괄 복사", page_icon="📋", layout="wide")

st.title("📋 학과 간 공통과목 일괄 복사")
st.markdown("한 학과에 입력해둔 **'보통교과'** 및 **'전문공통'** 과목들을 다른 학과로 한 번에 복사할 수 있습니다.")

if not supabase:
    st.error("데이터베이스에 연결되지 않았습니다.")
    st.stop()

departments = get_departments()
dept_names = [f"{d['name']} ({d['course_type']})" if d.get('course_type') else d['name'] for d in departments]

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("1. 원본 학과 선택 (어디서 복사할까요?)")
    source_dept_name = st.selectbox("원본 학과", dept_names, key="source_dept")
    source_year = st.selectbox("기준 연도", get_selectable_years(), key="source_year")


# 원본 학과 객체 가져오기
source_dept = departments[dept_names.index(source_dept_name)]

with col2:
    st.subheader("2. 복사 대상 학과 선택")
    st.markdown("과목을 복사하여 넣을 대상 학과들을 모두 선택하세요.")
    
    other_depts = [d for d in departments if d['id'] != source_dept['id']]
    selected_targets = []
    
    if not other_depts:
        st.info("선택할 수 있는 다른 학과가 없습니다.")
    else:
        for d in other_depts:
            d_display = f"{d['name']} ({d['course_type']})" if d.get('course_type') else d['name']
            if st.checkbox(d_display, value=True, key=f"target_dept_{d['id']}"):
                selected_targets.append(d)

with col3:
    st.subheader("3. 복사 조건")
    copy_general = st.checkbox("보통교과 복사하기", value=True)
    copy_special_common = st.checkbox("전문교과(공통) 복사하기", value=True)

if not selected_targets:
    st.warning("복사 대상 학과를 최소 하나 이상 선택해야 합니다.")
    st.stop()

# 소스 데이터 가져오기
source_version = get_curriculum_version(source_dept['id'], source_year)

if not source_version:
    st.error(f"원본 학과에 {source_year}학년도 편제표 데이터가 없습니다. 먼저 작성해주세요.")
    st.stop()

source_schedules = get_curriculum_schedules(source_version['id'])

# 복사할 데이터 필터링
copy_candidates = []
for s in source_schedules:
    sub = s['subjects']
    is_general = sub.get('category') == "보통교과"
    is_special_common = sub.get('subject_group') == "전문공통"
    
    if (copy_general and is_general) or (copy_special_common and is_special_common):
        copy_candidates.append(s)

st.divider()

st.markdown(f"### 📦 복사 예정 과목 목록 (총 {len(copy_candidates)}개 과목)")

if not copy_candidates:
    st.info("조건에 일치하는 복사할 과목이 없습니다.")
else:
    df_preview = pd.DataFrame([{
        "교과영역": s['subjects']['category'],
        "교과군": s['subjects']['subject_group'],
        "과목명": s['subjects']['name'],
        "기본 학점": s['subjects']['base_credits'],
        "1-1": s['grade_1_sem_1'] or 0, "1-2": s['grade_1_sem_2'] or 0,
        "2-1": s['grade_2_sem_1'] or 0, "2-2": s['grade_2_sem_2'] or 0,
        "3-1": s['grade_3_sem_1'] or 0, "3-2": s['grade_3_sem_2'] or 0,
    } for s in copy_candidates])
    
    st.dataframe(df_preview, use_container_width=True)
    
    target_names_str = ", ".join([f"'{d['name']} ({d['course_type']})'" if d.get('course_type') else f"'{d['name']}'" for d in selected_targets])
    st.warning(f"⚠️ **주의:** 복사하기를 누르면 **{target_names_str}**의 기존 편성표에 위 과목들이 추가됩니다. (이미 존재하는 동일 과목은 중복 등록을 방지하기 위해 자동으로 제외됩니다.)")
    
    if st.button("🚀 위 과목들을 선택한 학과들로 복사하기", type="primary"):
        with st.spinner("복사 중입니다..."):
            copied_count = 0
            for target_dept in selected_targets:
                # 대상 버전 확인 및 생성
                target_version = get_curriculum_version(target_dept['id'], source_year)
                if not target_version:
                    new_v = supabase.table("curriculum_versions").insert({
                        "department_id": target_dept['id'],
                        "year": source_year,
                        "target_grade": 0,
                        "framework": "2022 개정",
                        "status": "Draft",
                        "elective_credits": 0
                    }).execute()
                    target_version = new_v.data[0]
                
                # 대상 학과의 기존 schedule 목록 조회 (중복 방지용)
                exist_scheds_res = supabase.table("curriculum_schedules").select("subject_id").eq("version_id", target_version['id']).execute()
                exist_subject_ids = set(item['subject_id'] for item in exist_scheds_res.data) if exist_scheds_res.data else set()
                
                for s in copy_candidates:
                    # 중복 과목은 제외하고 복사
                    if s['subject_id'] in exist_subject_ids:
                        continue
                        
                    sched_data = {
                        "version_id": target_version['id'],
                        "subject_id": s['subject_id'],
                        "is_elective": s['is_elective'],
                        "grade_1_sem_1": s['grade_1_sem_1'],
                        "grade_1_sem_2": s['grade_1_sem_2'],
                        "grade_2_sem_1": s['grade_2_sem_1'],
                        "grade_2_sem_2": s['grade_2_sem_2'],
                        "grade_3_sem_1": s['grade_3_sem_1'],
                        "grade_3_sem_2": s['grade_3_sem_2']
                    }
                    supabase.table("curriculum_schedules").insert(sched_data).execute()
                copied_count += 1
                
        st.success(f"🎉 성공적으로 {copied_count}개 대상 학과에 복사가 완료되었습니다! 편제표 입력 메뉴에서 확인하세요.")
