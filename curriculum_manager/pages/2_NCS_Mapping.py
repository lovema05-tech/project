import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode
from supabase import create_client

# Supabase 초기화
if "supabase" not in st.session_state:
    st.session_state.supabase = create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["key"]
    )
supabase = st.session_state.supabase

st.set_page_config(page_title="NCS 실무과목 매핑", page_icon="🔗", layout="wide")

st.title("🔗 NCS 실무과목 이론/실습 매핑")
st.markdown("편제표에 편성된 실무과목의 학점을 기준으로, NCS 능력단위별 **이론 학점**과 **실습 학점**을 배분합니다.")

# 1. 버전 선택
versions_res = supabase.table("curriculum_versions").select("id, year, departments(name, course_type)").execute()
if not versions_res.data:
    st.warning("등록된 교육과정 버전이 없습니다. 엑셀을 먼저 업로드해주세요.")
    st.stop()

version_options = {
    f"{v['year']}학년도 {v['departments']['name']} ({v['departments']['course_type']})": v['id']
    for v in versions_res.data if v['departments']
}

selected_ver_name = st.selectbox("📌 학과 및 연도 선택", list(version_options.keys()))
version_id = version_options[selected_ver_name]

st.divider()

# 2. 데이터 불러오기 (해당 버전의 실무과목 스케줄 + NCS 단위)
# 먼저 schedules와 subjects를 가져옴
sched_res = supabase.table("curriculum_schedules").select(
    "id, subject_id, total_credits, subjects(name, category, subject_group)"
).eq("version_id", version_id).execute()

# 실무과목(전문교과)만 필터링 (보통 실무과목은 NCS 단위가 매핑된 과목들임)
sched_ids = [s['id'] for s in sched_res.data]
if not sched_ids:
    st.info("해당 학과에 등록된 과목이 없습니다.")
    st.stop()

ncs_res = supabase.table("ncs_units").select("*").in_("schedule_id", sched_ids).execute()
ncs_data = ncs_res.data

if not ncs_data:
    st.info("해당 학과의 편제표에는 실무과목 능력단위가 없습니다. (엑셀에 '실무과목 능력단위' 시트가 없거나 아직 파싱되지 않았습니다.)")
    st.stop()

# 데이터 프레임 생성
rows = []
schedule_credit_map = {} # subject별 목표 학점 저장용

for ncs in ncs_data:
    sched_id = ncs['schedule_id']
    # 해당하는 schedule 찾기
    sched_info = next((s for s in sched_res.data if s['id'] == sched_id), None)
    if not sched_info:
        continue
        
    subject_name = sched_info['subjects']['name']
    total_credits = sched_info['total_credits']
    schedule_credit_map[subject_name] = total_credits
    
    # 총 이수 학점 (엑셀에서 파싱된 학기별 학점의 총합)
    ncs_total_credits = (
        (ncs['grade_1_sem_1_credits'] or 0) + (ncs['grade_1_sem_2_credits'] or 0) +
        (ncs['grade_2_sem_1_credits'] or 0) + (ncs['grade_2_sem_2_credits'] or 0) +
        (ncs['grade_3_sem_1_credits'] or 0) + (ncs['grade_3_sem_2_credits'] or 0)
    )
    
    rows.append({
        "id": ncs['id'],
        "과목명": subject_name,
        "능력단위명": ncs['unit_name'],
        "능력단위 수준": ncs['unit_level'],
        "NCS 훈련시간": ncs['training_hours'],
        "배정 학점 합계": ncs_total_credits, # 엑셀에서 파싱된 해당 능력단위의 이수학점 합계
        "이론 학점 (입력)": ncs['theory_hours'] or 0,
        "실습 학점 (입력)": ncs['practice_hours'] or 0,
    })

df = pd.DataFrame(rows)

# 3. 과목별 학점 검증 로직
st.markdown("### 📊 과목별 이론/실습 학점 동기화 검증")
st.caption("각 과목에 속한 능력단위들의 '이론 학점'과 '실습 학점'의 총합은, 편제표 상의 **'과목 총 학점'**과 정확히 일치해야 합니다.")

validation_passed = True
cols = st.columns(3)
col_idx = 0

for subject, target_credits in schedule_credit_map.items():
    subject_df = df[df["과목명"] == subject]
    if subject_df.empty:
        continue
        
    current_theory = subject_df["이론 학점 (입력)"].sum()
    current_practice = subject_df["실습 학점 (입력)"].sum()
    current_total = current_theory + current_practice
    
    with cols[col_idx % 3]:
        if current_total == target_credits:
            st.success(f"**{subject}**\n\n✅ {current_total} / {target_credits} 학점 (일치)")
        else:
            validation_passed = False
            st.error(f"**{subject}**\n\n⚠️ {current_total} / {target_credits} 학점 (불일치!)\n이론({current_theory}) + 실습({current_practice})")
    col_idx += 1

st.divider()

# 4. Ag-Grid를 통한 데이터 편집
st.markdown("### 📝 이론/실습 학점 분배하기")
st.info("아래 표에서 **'이론 학점 (입력)'** 및 **'실습 학점 (입력)'** 열을 더블 클릭하여 숫자를 수정하세요.")

gb = GridOptionsBuilder.from_dataframe(df.drop(columns=["id"]))

# 읽기 전용 컬럼 설정
gb.configure_column("과목명", editable=False, rowGroup=True, hide=True) # 과목명으로 그룹화
gb.configure_column("능력단위명", editable=False)
gb.configure_column("능력단위 수준", editable=False)
gb.configure_column("NCS 훈련시간", editable=False)
gb.configure_column("배정 학점 합계", editable=False)

# 편집 가능 컬럼 설정
gb.configure_column("이론 학점 (입력)", editable=True, type=["numericColumn", "numberColumnFilter"], 
                    cellStyle={'backgroundColor': '#e8f4f8', 'fontWeight': 'bold'})
gb.configure_column("실습 학점 (입력)", editable=True, type=["numericColumn", "numberColumnFilter"], 
                    cellStyle={'backgroundColor': '#f8f4e8', 'fontWeight': 'bold'})

gb.configure_grid_options(groupDefaultExpanded=1) # 기본으로 그룹 펼치기
gridOptions = gb.build()

grid_response = AgGrid(
    df,
    gridOptions=gridOptions,
    update_mode=GridUpdateMode.MODEL_CHANGED,
    data_return_mode=DataReturnMode.AS_INPUT,
    fit_columns_on_grid_load=True,
    theme="streamlit",
    height=500
)

# 5. 저장 로직
edited_df = grid_response['data']

col1, col2 = st.columns([1, 4])
with col1:
    if st.button("💾 변경사항 저장", type="primary", use_container_width=True):
        with st.spinner("저장 중..."):
            try:
                for idx, row in edited_df.iterrows():
                    ncs_id = df.iloc[idx]["id"] # 원본 df에서 id 추출
                    t_hours = int(row["이론 학점 (입력)"]) if pd.notna(row["이론 학점 (입력)"]) else 0
                    p_hours = int(row["실습 학점 (입력)"]) if pd.notna(row["실습 학점 (입력)"]) else 0
                    
                    supabase.table("ncs_units").update({
                        "theory_hours": t_hours,
                        "practice_hours": p_hours
                    }).eq("id", ncs_id).execute()
                    
                st.success("성공적으로 저장되었습니다!")
                st.rerun()
            except Exception as e:
                st.error(f"저장 중 오류가 발생했습니다: {e}")

if not validation_passed:
    st.warning("⚠️ 아직 편제표 학점과 동기화되지 않은 과목이 있습니다. 상단의 에러 박스를 확인하여 이론/실습 학점을 정확히 맞춰주세요.")
