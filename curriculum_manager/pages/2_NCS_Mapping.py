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
    
    # 엑셀에서 파싱된 각 능력단위의 이수학점 총합
    ncs_total_credits = (
        (ncs['grade_1_sem_1_credits'] or 0) + (ncs['grade_1_sem_2_credits'] or 0) +
        (ncs['grade_2_sem_1_credits'] or 0) + (ncs['grade_2_sem_2_credits'] or 0) +
        (ncs['grade_3_sem_1_credits'] or 0) + (ncs['grade_3_sem_2_credits'] or 0)
    )
    
    rows.append({
        "id": ncs['id'],
        "실무과목": subject_name,
        "능력단위 코드": ncs['unit_code'],
        "내용영역 (능력단위)": ncs['unit_name'],
        "수준": ncs['unit_level'],
        "훈련시간": ncs['training_hours'],
        "NCS 학점": ncs_total_credits
    })

df = pd.DataFrame(rows)

# 3. 과목별 학점 검증 로직
st.markdown("### 📊 실무과목별 NCS 매핑 검증")
st.caption("실무과목 내에 편성된 각 내용영역(능력단위) 학점의 총합이 편제표와 일치하는지 확인합니다.")

# 능력단위 코드 일관성 검사
code_to_subjects = {}
for row_idx, row in df.iterrows():
    code = row['능력단위 코드']
    subject = row['실무과목']
    if pd.isna(code) or not str(code).strip():
        continue
    if code not in code_to_subjects:
        code_to_subjects[code] = set()
    code_to_subjects[code].add(subject)

inconsistent_codes = {code: subs for code, subs in code_to_subjects.items() if len(subs) > 1}
if inconsistent_codes:
    st.warning("⚠️ **능력단위 코드 중복 주의:** 동일한 코드가 여러 실무과목에 중복 사용되었습니다.")
    for code, subs in inconsistent_codes.items():
        st.write(f"- 코드 `{code}`: {', '.join(subs)}")
    st.divider()

validation_passed = True
cols = st.columns(3)
col_idx = 0

for subject, target_credits in schedule_credit_map.items():
    subject_df = df[df["실무과목"] == subject]
    if subject_df.empty:
        continue
        
    current_total = subject_df["NCS 학점"].sum()
    unit_count = len(subject_df)
    
    with cols[col_idx % 3]:
        if current_total == target_credits:
            st.success(f"**{subject}** ({unit_count}개 단위)\n\n✅ {current_total} / {target_credits} 학점 (일치)")
        else:
            validation_passed = False
            st.error(f"**{subject}** ({unit_count}개 단위)\n\n⚠️ {current_total} / {target_credits} 학점 (불일치!)")
    col_idx += 1

st.divider()

# 4. Ag-Grid를 통한 데이터 조회
st.markdown("### 📋 NCS 실무과목/내용영역 매핑 현황")
st.info("실무과목을 클릭하여 내부의 내용영역(능력단위) 목록을 확인하세요.")

if not df.empty:
    gb = GridOptionsBuilder.from_dataframe(df.drop(columns=["id"]))

    # 그룹화 및 컬럼 설정 (숨김 해제하여 명시적으로 표시)
    gb.configure_column("실무과목", rowGroup=True, pinned='left', width=200)
    gb.configure_column("내용영역 (능력단위)", minWidth=350)
    gb.configure_column("능력단위 코드", width=150)
    gb.configure_column("NCS 학점", type=["numericColumn", "numberColumnFilter"], width=100)
    
    # 자동 그룹 컬럼 설정 (가장 왼쪽에 트리 형태로 표시)
    gb.configure_grid_options(
        autoGroupColumnDef={
            "headerName": "📂 실무과목 그룹",
            "minWidth": 250,
            "pinned": "left",
            "cellRendererParams": {"suppressCount": False}
        },
        groupDefaultExpanded=1
    )
    
    gridOptions = gb.build()

    AgGrid(
        df,
        gridOptions=gridOptions,
        fit_columns_on_grid_load=True,
        theme="streamlit",
        height=600
    )

if not validation_passed:
    st.warning("⚠️ 편제표 학점과 능력단위 배정 학점이 불일치하는 과목이 있습니다. 엑셀을 확인해 주세요.")
else:
    st.success("🎉 모든 실무과목의 NCS 매핑이 정상입니다!")
