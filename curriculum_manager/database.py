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
