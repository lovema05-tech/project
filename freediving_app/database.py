import streamlit as st
from supabase import create_client

@st.cache_resource
def get_supabase():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = get_supabase()

def get_announcements():
    res = supabase.table("fd_announcements").select("*").order("created_at", desc=True).execute()
    return res.data

def get_schedules():
    res = supabase.table("fd_schedules").select("*").order("schedule_date").order("schedule_time").execute()
    return res.data

def get_applications(schedule_id=None):
    if schedule_id:
        res = supabase.table("fd_applications").select("*").eq("schedule_id", schedule_id).order("created_at").execute()
    else:
        res = supabase.table("fd_applications").select("*").order("created_at").execute()
    return res.data
