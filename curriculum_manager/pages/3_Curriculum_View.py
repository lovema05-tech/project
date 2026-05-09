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

st.set_page_config(page_title="교육과정 종합 조회", page_icon="📅", layout="wide")

st.title("📅 교육과정 종합 조회 (학과별/학년별)")
st.markdown("학과별로 전체 교육과정을 보거나, 특정 학년의 모든 학과 교육과정을 모아서 볼 수 있습니다.")

# 1. 데이터 불러오기 (버전 및 학과 정보)
versions_res = supabase.table("curriculum_versions").select("*, departments(name, course_type)").execute()
if not versions_res.data:
    st.warning("등록된 교육과정 데이터가 없습니다.")
    st.stop()

# 입학년도 목록 추출
years = sorted(list(set([v['year'] for v in versions_res.data])), reverse=True)
selected_year = st.sidebar.selectbox("📌 입학년도 선택", years)

# 선택된 연도의 버전들 필터링
filtered_versions = [v for v in versions_res.data if v['year'] == selected_year]

# 탭 생성
tab1, tab2 = st.tabs(["🏢 학과별 조회", "👥 학년별 조회"])

# -------------------------------------------------------------------------
# Tab 1: 학과별 조회 (기존 기능 유지 및 개선)
# -------------------------------------------------------------------------
with tab1:
    st.subheader("🏢 학과별 교육과정 (3개년)")
    
    dept_options = {
        f"{v['departments']['name']} ({v['departments']['course_type']})": v
        for v in filtered_versions if v['departments']
    }
    
    if not dept_options:
        st.info("해당 연도에 등록된 학과가 없습니다.")
    else:
        selected_dept = st.selectbox("조회할 학과 선택", list(dept_options.keys()))
        version = dept_options[selected_dept]
        
        # 데이터 불러오기
        schedules_res = supabase.table("curriculum_schedules").select("*, subjects(*)").eq("version_id", version['id']).execute()
        
        if not schedules_res.data:
            st.info("해당 학과에 등록된 과목이 없습니다.")
        else:
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
            
            # 요약 정보
            total_mandatory = df[df["필수/선택"] == "필수"]["운영 학점"].sum()
            elective_credits = version.get('elective_credits', 0)
            creative_credits = 18
            final_total = total_mandatory + elective_credits + creative_credits
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("총 이수학점", f"{final_total} / 192")
            col_idx = 0 # Dummy for grid
            
            # 테이블 정렬 및 표시
            df = df.sort_values(by=["필수/선택", "교과영역", "교과군"])
            st.dataframe(df, use_container_width=True, height=500)
            
            # 엑셀 다운로드
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='학과별_교육과정')
            excel_data = output.getvalue()
            
            st.download_button(
                label=f"📥 {selected_dept} 엑셀 다운로드",
                data=excel_data,
                file_name=f"{selected_year}_{selected_dept}_교육과정.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_dept"
            )

# -------------------------------------------------------------------------
# Tab 2: 학년별 조회 (신규 기능)
# -------------------------------------------------------------------------
with tab2:
    st.subheader("👥 학년별 모든 학과 교육과정 모아보기")
    
    selected_grade = st.radio("조회할 학년 선택", ["1학년", "2학년", "3학년"], horizontal=True)
    
    grade_data = []
    for v in filtered_versions:
        dept_name = v['departments']['name']
        course_type = v['departments']['course_type']
        dept_display = f"{dept_name} ({course_type})" if course_type else dept_name
        
        schedules = supabase.table("curriculum_schedules").select("*, subjects(*)").eq("version_id", v['id']).execute()
        
        for s in schedules.data:
            sub = s['subjects']
            
            # 선택된 학년에 따른 학기별 학점 추출
            if selected_grade == "1학년":
                sem1 = s['grade_1_sem_1'] or 0
                sem2 = s['grade_1_sem_2'] or 0
            elif selected_grade == "2학년":
                sem1 = s['grade_2_sem_1'] or 0
                sem2 = s['grade_2_sem_2'] or 0
            else:
                sem1 = s['grade_3_sem_1'] or 0
                sem2 = s['grade_3_sem_2'] or 0
                
            # 해당 학년에 이수하는 과목만 포함
            if sem1 > 0 or sem2 > 0:
                grade_data.append({
                    "학과": dept_display,
                    "필수/선택": "선택" if s.get('is_elective') else "필수",
                    "교과영역": sub['category'] or "",
                    "교과군": sub['subject_group'] or "",
                    "과목명": sub['name'],
                    "1학기 학점": sem1,
                    "2학기 학점": sem2,
                    "학년 총학점": sem1 + sem2
                })
                
    if not grade_data:
        st.info(f"선택된 {selected_year}학년도 {selected_grade}에 편성된 과목이 없습니다.")
    else:
        grade_df = pd.DataFrame(grade_data)
        
        # 학과, 필수/선택, 교과영역 순으로 정렬
        grade_df = grade_df.sort_values(by=["학과", "필수/선택", "교과영역"])
        
        st.dataframe(grade_df, use_container_width=True, height=600)
        
        # 학년별 엑셀 다운로드
        output_grade = io.BytesIO()
        with pd.ExcelWriter(output_grade, engine='openpyxl') as writer:
            grade_df.to_excel(writer, index=False, sheet_name=f'{selected_grade}_교육과정')
        excel_data_grade = output_grade.getvalue()
        
        st.download_button(
            label=f"📥 {selected_year}학년도 {selected_grade} 전체 엑셀 다운로드",
            data=excel_data_grade,
            file_name=f"{selected_year}_{selected_grade}_전체_교육과정.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_grade"
        )
