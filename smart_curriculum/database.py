import streamlit as st
from supabase import create_client, Client

@st.cache_resource
def init_connection() -> Client:
    """Initialize and return Supabase client using secrets"""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

# Initialize global client
try:
    supabase = init_connection()
except Exception as e:
    st.error(f"Supabase 연결 오류: {e}")
    supabase = None

def get_departments():
    """학과 목록을 가져옵니다."""
    response = supabase.table("departments").select("*").execute()
    return response.data

def get_curriculum_version(dept_id, year):
    """특정 학과/연도의 교육과정 버전 정보를 가져옵니다."""
    response = supabase.table("curriculum_versions") \
        .select("*") \
        .eq("department_id", dept_id) \
        .eq("year", year) \
        .execute()
    return response.data[0] if response.data else None

def get_curriculum_schedules(version_id):
    """특정 버전의 편성표와 과목 정보를 가져옵니다."""
    response = supabase.table("curriculum_schedules") \
        .select("*, subjects(*)") \
        .eq("version_id", version_id) \
        .execute()
    return response.data

def get_common_subjects():
    """모든 학과에서 참조할 수 있는 보통교과(공통) 또는 학교 공통 과목을 가져옵니다. 
       (여기서는 예시로 가장 먼저 등록된 학과의 보통교과를 가져오거나 별도의 템플릿 로직 구성 가능)"""
    pass

def get_selectable_years():
    """DB에 저장된 모든 교육과정 연도와 현재 연도 기준 미래 1년 범위를 합산하여 선택 가능한 연도 목록을 반환합니다."""
    import datetime
    years = set()
    
    # 1. DB에 이미 존재하는 연도들 조회 (과거에 이미 저장된 교육과정 연도는 계속 유지되도록 보장)
    try:
        response = supabase.table("curriculum_versions").select("year").execute()
        if response.data:
            for item in response.data:
                if item.get('year'):
                    years.add(int(item['year']))
    except Exception as e:
        # DB 조회 실패 시 무시하고 진행
        pass
        
    # 2. 현재 연도 기준 범위 추가 (기본 2024년부터 현재 연도 + 1년까지)
    current_year = datetime.date.today().year
    for y in range(2024, current_year + 2):
        years.add(y)
        
    # 3. 내림차순 정렬하여 반환
    return sorted(list(years), reverse=True)

