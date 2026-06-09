import streamlit as st

st.set_page_config(
    page_title="스마트 교육과정 관리 시스템",
    page_icon="🏫",
    layout="wide"
)

st.markdown("""
<style>
    .main-title {
        font-family: 'Inter', sans-serif;
        font-size: 3rem;
        font-weight: 800;
        color: #1e293b;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-title {
        text-align: center;
        font-size: 1.2rem;
        color: #475569;
        margin-bottom: 3rem;
    }
    .feature-card {
        background: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
        text-align: center;
        height: 100%;
        transition: transform 0.2s;
    }
    .feature-card:hover {
        transform: translateY(-5px);
    }
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">스마트 교육과정 관리 시스템 🏫</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">2022 개정 교육과정 기반 직업계고 맞춤형 편제표 작성 및 실시간 검증</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📝</div>
        <h3>스마트 편제표 입력</h3>
        <p>엑셀처럼 편리한 UI에서 직접 과목과 시수를 입력합니다. 오류 없이 직관적인 데이터 관리가 가능합니다.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🛡️</div>
        <h3>실시간 검증 시스템</h3>
        <p>192학점 기준 충족 여부, 학기 매핑, 필수 이수 학점 위반 등을 실시간으로 잡아내어 알려줍니다.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📋</div>
        <h3>공통과목 간편 복사</h3>
        <p>보통교과와 학과 공통 전문교과를 한 번만 세팅하면 다른 학과로 원클릭 복사가 가능합니다.</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

st.info("👈 왼쪽 사이드바에서 원하는 메뉴를 선택하여 시작하세요.")
