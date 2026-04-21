import streamlit as st
import pandas as pd
import time
import random
from supabase import create_client, Client

# 기본 설정 (페이지 구조)
st.set_page_config(page_title="🏫 수업 관리 시스템", page_icon="🏫", layout="wide")

# CSS를 활용한 디자인 통일 (Premium Aesthetics)
st.markdown("""
<style>
    .stApp {
        background-color: #f9f9f9;
        font-family: 'Inter', sans-serif;
    }
    .big-font {
        font-size:50px !important;
        font-weight: bold;
        color: #2c3e50;
        text-align: center;
    }
    .result-font {
        font-size:80px !important;
        font-weight: 800;
        color: #e74c3c;
        text-align: center;
        text-shadow: 2px 2px 5px rgba(0,0,0,0.2);
    }
    .group-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .group-title {
        color: #34495e;
        font-weight: 700;
        font-size: 24px;
        border-bottom: 2px solid #3498db;
        padding-bottom: 10px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def init_supabase() -> Client | None:
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception:
        return None

try:
    supabase = init_supabase()
except Exception:
    supabase = None

# 임시 메모리 폴백
if "local_df" not in st.session_state:
    st.session_state.local_df = pd.DataFrame()

def load_data():
    if supabase is not None:
        try:
            response = supabase.table("students").select("*").execute()
            if response.data:
                return pd.DataFrame(response.data)
        except Exception:
            pass
    return st.session_state.local_df

def save_data(df):
    if supabase is not None:
        try:
            # 기존 데이터 클리어 (테스트용)
            supabase.table("students").delete().neq("id", 0).execute()
            records = []
            for _, row in df.iterrows():
                # 인덱스, 칼럼명 통일 처리 ('grade' 등 영문 혹은 한글맵)
                records.append({
                    "grade": int(row.get('학년', 1)),
                    "student_num": int(row['학번']),
                    "name": str(row['이름']),
                    "gender": str(row['성별']),
                    "score": int(row['성적'])
                })
            supabase.table("students").insert(records).execute()
            return True
        except Exception as e:
            st.error(f"Supabase 저장 오류: {e}")
            return False
    else:
        st.session_state.local_df = df
        return True

# 통일된 칼럼명 가져오기 헬퍼 함수
def get_columns(df):
    if 'name' in df.columns:
        return 'name', 'gender', 'score'
    return '이름', '성별', '성적'

# ================= 메인 UI ================= #
st.markdown("<p class='big-font'>🏫 스마트 수업 관리 대시보드</p>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 데이터 관리 (Upload)", "🧑‍🤝‍🧑 모둠 구성 (Grouping)", "🎯 발표 추첨 (Pick)"])

with tab1:
    st.markdown("### 엑셀 명렬표 파일 업로드")
    
    if supabase is None:
        st.info("💡 **안내:** 현재 Supabase 시크릿 키가 등록되지 않아 브라우저 메모리에 임시 저장됩니다. (새로고침 시 초기화됨)\n\n"
                "1년 내내 영구 저장하려면 추후 Github `.streamlit/secrets.toml`에 `SUPABASE_URL`, `SUPABASE_KEY`를 추가하시면 자동 연동됩니다.")
    else:
        st.success("✅ Supabase 클라우드 데이터베이스 연동 완료")
        
    uploaded_file = st.file_uploader("학생 데이터 엑셀(.xlsx)을 업로드 해주세요.", type=['xlsx'])
    
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            st.write("📊 업로드된 데이터 미리보기:")
            st.dataframe(df.head())
            
            if st.button("서버에 저장 및 연동하기", type="primary"):
                if save_data(df):
                    st.success("데이터가 성공적으로 저장되었습니다!")
                    st.balloons()
        except Exception as e:
            st.error(f"엑셀을 읽는 중 문제가 발생했습니다: {e}")
            
    st.markdown("---")
    st.markdown("#### 저장된 전체 명렬표")
    current_df = load_data()
    if not current_df.empty:
        st.dataframe(current_df, use_container_width=True)
    else:
        st.write("아직 저장된 학생 데이터가 없습니다.")

with tab2:
    st.markdown("### 🧑‍🤝‍🧑 성별, 성적 균형 모둠 편성")
    
    current_df = load_data()
    if current_df.empty:
        st.warning("데이터 관리 탭에서 엑셀 서식을 먼저 업로드 해주세요.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            group_size = st.number_input("한 모둠당 기본 학생 수 (N명)", min_value=2, value=4, step=1)
            
        st.info(f"💡 전체 인원({len(current_df)}명)을 바탕으로 모둠 간 인원수 차이가 최대 1명이 되도록(예: 4명/5명 또는 3명/4명 조합) 가장 균형 있게 분배됩니다.")
        
        if st.button("모둠 자동 구성 시작", type="primary"):
            with st.spinner("최적의 균형을 계산하고 있습니다..."):
                time.sleep(1) # 부드러운 전환 효과용
                name_col, gender_col, score_col = get_columns(current_df)
                
                # 남여 분리 및 성적(내림차순) 정렬
                males = current_df[current_df[gender_col] == '남'].sort_values(by=score_col, ascending=False).to_dict('records')
                females = current_df[current_df[gender_col] == '여'].sort_values(by=score_col, ascending=False).to_dict('records')
                
                total_students = len(current_df)
                num_groups = max(1, round(total_students / group_size))
                
                groups = [[] for _ in range(num_groups)]
                
                # 전역 상태를 유지하면서 지그재그(Snake) 분배
                idx = 0
                direction = 1
                
                # 남학생 먼저, 그 다음 여학생을 이어서 분배 (상태 유지)
                for gender_group in [males, females]:
                    for student in gender_group:
                        groups[idx].append(student)
                        idx += direction
                        if idx >= num_groups:
                            direction = -1
                            idx = num_groups - 1
                        elif idx < 0:
                            direction = 1
                            idx = 0
                
                st.success(f"🎉 총 {num_groups}개의 모둠이 편성되었습니다!")
                
                # 결과 출력 (격자 구조)
                cols_per_row = 3
                for i in range(0, num_groups, cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j in range(cols_per_row):
                        if i + j < num_groups:
                            group = groups[i + j]
                            group_df = pd.DataFrame(group)
                            
                            with cols[j]:
                                st.markdown(f"<div class='group-card'>", unsafe_allow_html=True)
                                st.markdown(f"<div class='group-title'>✨ {i + j + 1}조 ({len(group)}명)</div>", unsafe_allow_html=True)
                                
                                if not group_df.empty:
                                    avg_score = group_df[score_col].mean()
                                    m_cnt = len(group_df[group_df[gender_col] == '남'])
                                    f_cnt = len(group_df[group_df[gender_col] == '여'])
                                    
                                    st.markdown(f"**평균 성적**: {avg_score:.1f}점<br>**성별**: 남 {m_cnt}명 / 여 {f_cnt}명", unsafe_allow_html=True)
                                    st.dataframe(group_df[[name_col, gender_col, score_col]], hide_index=True)
                                    
                                st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.markdown("### 🎯 무작위 발표 추첨 룰렛")
    
    current_df = load_data()
    if current_df.empty:
        st.warning("데이터 관리 탭에서 엑셀 서식을 먼저 업로드 해주세요.")
    else:
        name_col, _, _ = get_columns(current_df)
        num_col = 'student_num' if 'student_num' in current_df.columns else '학번'
        students = current_df.apply(lambda row: f"[{row[num_col]}] {row[name_col]}", axis=1).tolist()
        
        _, col_center, _ = st.columns([1, 2, 1])
        
        with col_center:
            if st.button("🎲 전체 발표 순서 추첨!", use_container_width=True, type="primary"):
                placeholder = st.empty()
                progress_bar = st.progress(0)
                
                # 애니메이션 루프: 리스트 전체를 빠르게 섞는 연출
                spins = 15
                for i in range(spins):
                    shuffled = random.sample(students, len(students))
                    html_list = "<div style='display: flex; flex-wrap: wrap; gap: 10px; justify-content: center;'>"
                    for rank, name in enumerate(shuffled, 1):
                        html_list += f"<div style='padding: 10px 15px; background-color: #3498db; color: white; border-radius: 8px; font-weight: bold;'>{rank}. {name}</div>"
                    html_list += "</div>"
                    
                    placeholder.markdown(html_list, unsafe_allow_html=True)
                    progress_bar.progress((i + 1) / spins)
                    time.sleep(0.05 + (i * 0.02)) # 갈수록 조금씩 느려짐
                    
                # 최종 결과 확정
                final_order = random.sample(students, len(students))
                html_list = "<div style='display: flex; flex-wrap: wrap; gap: 10px; justify-content: center;'>"
                for rank, name in enumerate(final_order, 1):
                    # 상위 3명은 금/은/동으로 약간 다르게 하이라이트 할 수도 있지만 통일성 위해 붉은색 배열
                    html_list += f"<div style='padding: 10px 15px; background-color: #e74c3c; color: white; border-radius: 8px; font-weight: bold; font-size: 1.1em; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>🎉 {rank}번. {name}</div>"
                html_list += "</div>"
                
                placeholder.markdown(html_list, unsafe_allow_html=True)
                progress_bar.empty()
                st.balloons()
