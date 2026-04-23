import streamlit as st
from database import supabase, get_departments, get_curriculum_version
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

st.set_page_config(page_title="대양고 교육과정 관리 시스템", page_icon="🏫", layout="wide")

# CSS 스타일링
st.markdown("""
<style>
    .stApp { background-color: #f8fafc; font-family: 'Inter', sans-serif; }
    .main-header { font-size: 32px; font-weight: 800; color: #1e293b; margin-bottom: 20px; }
    .status-badge-draft { background-color: #e2e8f0; color: #475569; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
    .status-badge-submitted { background-color: #fef08a; color: #854d0e; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
    .status-badge-approved { background-color: #bbf7d0; color: #166534; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">대양고등학교 교육과정 관리 시스템 🏫</div>', unsafe_allow_html=True)

if not supabase:
    st.error("데이터베이스에 연결되지 않았습니다. `.streamlit/secrets.toml`을 확인해주세요.")
    st.stop()

# 데이터 로드
departments = get_departments()
dept_names = [f"{d['name']} ({d['course_type']})" if d.get('course_type') else d['name'] for d in departments]

st.sidebar.title("🔐 사용자 권한")
user_role = st.sidebar.radio("접속 모드:", ["교과담당 부장 (데이터 입력)", "교육과정 담당자 (검토 및 승인)"])

if "부장" in user_role:
    st.subheader("📝 교육과정 편제표 입력 및 제출 (부장용)")
    if not dept_names:
        st.warning("등록된 학과가 없습니다. 왼쪽 '엑셀 업로드' 메뉴에서 초기 데이터를 세팅해주세요.")
        st.stop()
        
    # 학과 및 입학년도 선택
    col_dept, col_year = st.columns(2)
    with col_dept:
        selected_dept_name = st.selectbox("학과 선택", dept_names)
    with col_year:
        selected_year = st.selectbox("입학년도 (적용 학년)", [2026, 2025, 2024])
        
    selected_dept = departments[dept_names.index(selected_dept_name)]
    
    # 선택된 입학년도 버전 정보 가져오기
    version = get_curriculum_version(selected_dept['id'], selected_year)
    
    if version:
        status_color = "status-badge-draft" if version['status'] == 'Draft' else "status-badge-submitted" if version['status'] == 'Submitted' else "status-badge-approved"
        st.markdown(f"**현재 상태:** <span class='{status_color}'>{version['status']}</span>", unsafe_allow_html=True)
        
        if version['status'] == 'Approved':
            st.success("이미 승인 완료된 교육과정입니다. 수정할 수 없습니다.")
        else:
            # DB에서 기존 과목 및 스케줄 가져오기
            schedules_res = supabase.table("curriculum_schedules").select("*, subjects(*)").eq("version_id", version['id']).execute()
            
            table_data = []
            for s in schedules_res.data:
                sub = s['subjects']
                table_data.append({
                    "id": s['id'],
                    "subject_id": sub['id'],
                    "필수/선택": "선택" if s.get('is_elective') else "필수",
                    "교과영역": sub['category'] or "",
                    "교과군": sub['subject_group'] or "",
                    "과목명": sub['name'],
                    "기본 학점": str(sub.get('base_credits', '')) if pd.notna(sub.get('base_credits')) else "0",
                    "운영가능 학점": sub.get('operable_credits', ""),
                    "운영 학점": s.get('total_credits', 0),
                    "1-1": s['grade_1_sem_1'] or 0,
                    "1-2": s['grade_1_sem_2'] or 0,
                    "2-1": s['grade_2_sem_1'] or 0,
                    "2-2": s['grade_2_sem_2'] or 0,
                    "3-1": s['grade_3_sem_1'] or 0,
                    "3-2": s['grade_3_sem_2'] or 0,
                })
                
            df = pd.DataFrame(table_data)
            if df.empty:
                df = pd.DataFrame(columns=["id", "subject_id", "필수/선택", "교과영역", "교과군", "과목명", "기본 학점", "운영가능 학점", "운영 학점", "1-1", "1-2", "2-1", "2-2", "3-1", "3-2"])
            
            # 항상 빈 행 5개를 추가로 제공
            empty_rows = []
            for _ in range(5):
                empty_rows.append([None, None, "필수", "보통교과", "", "", "0", "", 0, 0, 0, 0, 0, 0, 0])
            df = pd.concat([df, pd.DataFrame(empty_rows, columns=df.columns)], ignore_index=True)
            
            # 교과군 목록 가져오기 (DB에 저장된 고유 값들 + 기본값)
            groups_res = supabase.table("subjects").select("subject_group").execute()
            unique_groups = list(set(item['subject_group'] for item in groups_res.data if item['subject_group'])) if groups_res.data else []
            default_groups = ["국어", "수학", "영어", "한국사", "사회(역사/도덕포함)", "과학", "체육", "예술", "기술·가정/제2외국어/한문/교양", "전문공통", "전공일반", "전공실무", "문화·예술·디자인·방송", "정보·통신", "전기·전자"]
            for dg in default_groups:
                if dg not in unique_groups:
                    unique_groups.append(dg)
            
            # Ag-Grid 옵션 설정
            gb = GridOptionsBuilder.from_dataframe(df)
            gb.configure_default_column(editable=True, resizable=True, sortable=True)
            gb.configure_column("id", hide=True)
            gb.configure_column("subject_id", hide=True)
            
            # 컬럼 너비 및 속성 설정
            gb.configure_column("필수/선택", width=100, cellEditor='agSelectCellEditor', cellEditorParams={'values': ["필수", "선택"]})
            gb.configure_column("교과영역", width=120)
            gb.configure_column("교과군", width=150, cellEditor='agSelectCellEditor', cellEditorParams={'values': unique_groups})
            gb.configure_column("과목명", width=200)
            gb.configure_column("기본 학점", width=100)
            gb.configure_column("운영가능 학점", width=120)
            gb.configure_column("운영 학점", width=100, editable=False)
            
            # 학기별 컬럼 설정
            sem_cols = ["1-1", "1-2", "2-1", "2-2", "3-1", "3-2"]
            for col in sem_cols:
                gb.configure_column(col, width=80, type=["numericColumn", "numberColumnFilter"])
            
            gridOptions = gb.build()
            
            st.info("💡 엑셀처럼 탭(Tab)키나 방향키로 이동하며 자유롭게 수정하세요. 표 아래쪽의 빈칸에 새 과목을 입력할 수 있습니다.")
            grid_response = AgGrid(
                df,
                gridOptions=gridOptions,
                data_return_mode=DataReturnMode.AS_INPUT,
                update_mode=GridUpdateMode.MODEL_CHANGED,
                fit_columns_on_grid_load=True,
                theme='streamlit',
                height=500
            )
            edited_df = pd.DataFrame(grid_response['data'])
            
            st.divider()
            st.markdown("### 🧮 총 이수학점 검증")
            
            # 총 이수학점 계산 로직 (필수과목만 자동 합산)
            mandatory_df = edited_df[edited_df["필수/선택"] == "필수"]
            mandatory_credits = mandatory_df[["1-1", "1-2", "2-1", "2-2", "3-1", "3-2"]].sum().sum() if not mandatory_df.empty else 0
            
            # 선택과목 인정 학점 수동 입력
            col_calc1, col_calc2, col_calc3 = st.columns(3)
            with col_calc1:
                st.metric("필수과목 총 이수학점 (자동 합계)", f"{mandatory_credits} 학점")
            with col_calc2:
                elective_credits_input = st.number_input("선택과목 이수 인정 학점 (직접 입력)", min_value=0, max_value=192, value=version.get('elective_credits', 0), step=1)
            with col_calc3:
                # 창의적 체험활동은 버전에 필드가 없으므로, 편의상 기본값 18로 두고 elective_credits과 분리하거나, UI에서만 더해줍니다.
                # (192학점 = 교과(필수+선택) 174학점 + 창의적체험활동 18학점)
                creative_credits_input = st.number_input("창의적 체험활동 학점", min_value=0, max_value=192, value=18, step=1)
            
            final_total_credits = mandatory_credits + elective_credits_input + creative_credits_input
            
            if final_total_credits == 192:
                st.success(f"🎉 완벽합니다! 최종 이수학점이 192학점으로 딱 맞습니다. (필수 {mandatory_credits} + 선택 {elective_credits_input} + 창체 {creative_credits_input})")
            else:
                st.warning(f"⚠️ 현재 최종 이수학점은 **{final_total_credits}학점** 입니다. 192학점을 맞춰주세요.")
            
            st.divider()
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("💾 변경사항 임시 저장", icon="💾"):
                    with st.spinner("데이터베이스에 저장 중..."):
                        # 삭제된 행 처리
                        existing_ids = set(df['id'].dropna())
                        kept_ids = set(edited_df['id'].dropna())
                        deleted_ids = existing_ids - kept_ids
                        for d_id in deleted_ids:
                            supabase.table("curriculum_schedules").delete().eq("id", d_id).execute()
                            
                        # NaN 값을 기본값으로 처리
                        save_df = edited_df.fillna({"과목명": "", "교과영역": "", "교과군": "", "기준학점": "0", "1-1": 0, "1-2": 0, "2-1": 0, "2-2": 0, "3-1": 0, "3-2": 0})
                        
                        for index, row in save_df.iterrows():
                            if not str(row["과목명"]).strip():
                                continue
                            
                            is_elective_val = True if row["필수/선택"] == "선택" else False
                            
                            # 과목 조회 또는 생성
                            subject_res = supabase.table("subjects").select("id").eq("name", row["과목명"]).execute()
                            if subject_res.data:
                                subject_id = subject_res.data[0]["id"]
                                supabase.table("subjects").update({"base_credits": str(row["기준학점"])}).eq("id", subject_id).execute()
                            else:
                                new_sub = supabase.table("subjects").insert({
                                    "category": row["교과영역"],
                                    "subject_group": row["교과군"],
                                    "name": row["과목명"],
                                    "base_credits": str(row["기준학점"])
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
                                
                        # 버전의 선택과목 인정학점 저장
                        supabase.table("curriculum_versions").update({"elective_credits": elective_credits_input}).eq("id", version['id']).execute()
                                
                    st.success("✅ 성공적으로 저장되었습니다!")
                    st.rerun()
            
            with col_btn2:
                if st.button("🚀 담당자에게 제출하기", type="primary"):
                    if final_total_credits != 192:
                        st.error(f"총 이수학점이 192학점이 아닙니다! (현재 {final_total_credits}학점) 확인 후 제출해주세요.")
                    else:
                        supabase.table("curriculum_versions").update({"status": "Submitted", "elective_credits": elective_credits_input}).eq("id", version['id']).execute()
                        st.success("제출이 완료되었습니다!")
                        st.rerun()
    else:
        st.error(f"해당 학과의 {selected_year}학년도 입학생 교육과정 버전이 생성되지 않았습니다.")

elif "담당자" in user_role:
    st.subheader("✅ 교육과정 편제표 검토 및 승인 (담당자용)")
    
    selected_year = st.selectbox("검토할 입학년도 (적용 학년)", [2026, 2025, 2024])
    
    # 선택된 입학년도의 모든 학과 버전 로드
    versions_res = supabase.table("curriculum_versions").select("*, departments(name, course_type)").eq("year", selected_year).execute()
    all_versions = versions_res.data
    
    submitted_count = len([v for v in all_versions if v['status'] == 'Submitted'])
    
    col1, col2 = st.columns(2)
    col1.metric("총 학과 수", len(departments))
    col2.metric("결재 대기 중(Submitted)", submitted_count)
    
    st.divider()
    st.markdown("### 📋 각 학과별 진행 현황")
    
    if not all_versions:
        st.info("해당 연도의 교육과정 데이터가 없습니다.")
        
    for v in all_versions:
        dept_info = v['departments']
        dept_display = f"{dept_info['name']} ({dept_info['course_type']})" if dept_info.get('course_type') else dept_info['name']
        
        # 필수과목 학점 합계 + 선택과목 인정학점 = 최종 총 학점
        schedules_res = supabase.table("curriculum_schedules").select("*").eq("version_id", v['id']).eq("is_elective", False).execute()
        
        mandatory_credits = 0
        if schedules_res.data:
            for s in schedules_res.data:
                mandatory_credits += (s['grade_1_sem_1'] or 0) + (s['grade_1_sem_2'] or 0) + \
                                     (s['grade_2_sem_1'] or 0) + (s['grade_2_sem_2'] or 0) + \
                                     (s['grade_3_sem_1'] or 0) + (s['grade_3_sem_2'] or 0)
        
        elective_credits = v.get('elective_credits', 0)
        final_total_credits = mandatory_credits + elective_credits + 18
        
        status_emoji = "✅" if final_total_credits == 192 else "⚠️"
        
        with st.expander(f"{dept_display} - 상태: {v['status']} | {status_emoji} 총 학점: {final_total_credits}"):
            st.write(f"작성 상태: **{v['status']}**")
            st.markdown(f"**현재 편성된 총 이수학점:** {final_total_credits} 학점 (필수 {mandatory_credits} + 선택 {elective_credits} + 창체 18)")
            
            if final_total_credits != 192:
                st.error("총 이수학점이 192학점에 부합하지 않습니다. 부서에 수정을 요청하세요.")
            else:
                st.success("총 이수학점(192학점) 기준을 정확히 충족했습니다.")
            
            if v['status'] == 'Submitted':
                if final_total_credits == 192:
                    if st.button(f"{dept_display} 최종 승인", key=f"btn_{v['id']}", type="primary"):
                        supabase.table("curriculum_versions").update({"status": "Approved"}).eq("id", v['id']).execute()
                        st.success("승인 완료!")
                        st.rerun()
                else:
                    st.button(f"{dept_display} 최종 승인 (학점 오류로 불가)", key=f"btn_{v['id']}", disabled=True)

