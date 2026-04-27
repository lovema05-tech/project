import streamlit as st
import pandas as pd
from supabase import create_client
import io

# Supabase 초기화
if "supabase" not in st.session_state:
    st.session_state.supabase = create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["key"]
    )
supabase = st.session_state.supabase

st.set_page_config(page_title="학년별 교육과정 조회", page_icon="📅", layout="wide")

st.title("📅 학과별/학년별 교육과정 조회")
st.markdown("전체 학년(1~3학년)의 교육과정 편성 현황을 한눈에 확인하고 엑셀로 다운로드할 수 있습니다.")

# 1. 버전 선택
versions_res = supabase.table("curriculum_versions").select("*, departments(name, course_type)").execute()
if not versions_res.data:
    st.warning("등록된 교육과정 데이터가 없습니다.")
    st.stop()

version_options = {
    f"{v['year']}학년도 {v['departments']['name']} ({v['departments']['course_type']})": v
    for v in versions_res.data if v['departments']
}

selected_ver_name = st.selectbox("📌 조회할 학과 및 연도 선택", list(version_options.keys()))
version = version_options[selected_ver_name]

# 2. 데이터 불러오기
schedules_res = supabase.table("curriculum_schedules").select("*, subjects(*)").eq("version_id", version['id']).execute()

if not schedules_res.data:
    st.info("해당 학과에 등록된 과목이 없습니다.")
    st.stop()

# 데이터 가공
view_data = []
for s in schedules_res.data:
    sub = s['subjects']
    view_data.append({
        "필수/선택": "선택" if s.get('is_elective') else "필수",
        "교과영역": sub['category'] or "",
        "교과군": sub['subject_group'] or "",
        "과목명": sub['name'],
        "기본 학점": sub.get('base_credits', ""),
        "운영 학점": (s['grade_1_sem_1'] or 0) + (s['grade_1_sem_2'] or 0) + 
                     (s['grade_2_sem_1'] or 0) + (s['grade_2_sem_2'] or 0) + 
                     (s['grade_3_sem_1'] or 0) + (s['grade_3_sem_2'] or 0),
        "1-1": s['grade_1_sem_1'] or 0,
        "1-2": s['grade_1_sem_2'] or 0,
        "2-1": s['grade_2_sem_1'] or 0,
        "2-2": s['grade_2_sem_2'] or 0,
        "3-1": s['grade_3_sem_1'] or 0,
        "3-2": s['grade_3_sem_2'] or 0,
    })

df = pd.DataFrame(view_data)

# 요약 정보 표시
total_mandatory = df[df["필수/선택"] == "필수"]["운영 학점"].sum()
elective_credits = version.get('elective_credits', 0)
creative_credits = 18
final_total = total_mandatory + elective_credits + creative_credits

col1, col2, col3, col4 = st.columns(4)
col1.metric("총 이수학점", f"{final_total} / 192")
col2.metric("필수교과 합계", f"{total_mandatory} 학점")
col3.metric("선택교과 인정", f"{elective_credits} 학점")
col4.metric("창의적 체험활동", f"{creative_credits} 학점")

st.divider()

# 3. 데이터 테이블 표시
st.subheader("📋 상세 교육과정 편성표")
# 교과영역/교과군별로 정렬
df = df.sort_values(by=["필수/선택", "교과영역", "교과군"])
st.dataframe(df, use_container_width=True, height=600)

# 4. 엑셀 다운로드
st.markdown("### 📥 엑셀 파일로 저장")
output = io.BytesIO()
with pd.ExcelWriter(output, engine='openpyxl') as writer:
    df.to_excel(writer, index=False, sheet_name='교육과정편제표')
excel_data = output.getvalue()

st.download_button(
    label="💾 엑셀 다운로드 (.xlsx)",
    data=excel_data,
    file_name=f"{selected_ver_name}_교육과정.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
