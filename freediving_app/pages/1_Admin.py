import streamlit as st
import pandas as pd
from database import supabase, get_announcements, get_schedules, get_applications
from datetime import datetime

st.set_page_config(page_title="관리자 - 브로시스 프리다이빙", page_icon="🔐", layout="wide")

# 관리자 인증
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False

if not st.session_state.admin_logged_in:
    st.title("🔐 관리자 로그인")
    pwd = st.text_input("관리자 비밀번호를 입력하세요", type="password")
    if st.button("로그인"):
        # secrets.toml 에 저장된 관리자 비밀번호 확인
        if pwd == st.secrets.get("admin", {}).get("password", "admin1234"):
            st.session_state.admin_logged_in = True
            st.rerun()
        else:
            st.error("비밀번호가 일치하지 않습니다.")
    st.stop()

# --- 로그인 성공 시 아래 화면 ---
st.title("⚙️ 브로시스 프리다이빙 관리자 대시보드")
st.markdown("[👉 사용자 웹앱(메인화면)으로 바로가기](/)", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📢 공지사항 관리", "🗓️ 교육 일정 관리", "👥 예약자 현황 (상세)"])

# ----------------- 탭 1: 공지사항 관리 -----------------
with tab1:
    st.subheader("새 공지사항 작성")
    with st.form("announce_form", clear_on_submit=True):
        a_title = st.text_input("공지 제목")
        a_content = st.text_area("공지 내용")
        
        # 알림 기능 가설정
        st.info("💡 카카오톡/문자 자동 알림 발송은 외부 API(예: CoolSMS, 카카오비즈보드) 연동이 필요합니다. 현재는 가상의 발송 로직만 실행됩니다.")
        send_alert = st.checkbox("등록 시 수강생들에게 알림(SMS/카톡) 발송하기", value=True)
        
        a_submit = st.form_submit_button("공지 등록하기", type="primary")
        
        if a_submit:
            if not a_title or not a_content:
                st.error("제목과 내용을 모두 입력해주세요.")
            else:
                supabase.table("fd_announcements").insert({"title": a_title, "content": a_content}).execute()
                st.success("✅ 공지가 등록되었습니다!")
                if send_alert:
                    st.toast("📲 (가상) 카카오톡 알림이 발송되었습니다!")
                # 상태 갱신을 위해 rerun
                st.rerun()
                
    st.divider()
    st.subheader("등록된 공지사항 목록")
    anns = get_announcements()
    if anns:
        for ann in anns:
            st.write(f"**[{ann['created_at'][:10]}] {ann['title']}**")
            st.write(f"{ann['content']}")
            if st.button("삭제", key=f"del_ann_{ann['id']}"):
                supabase.table("fd_announcements").delete().eq("id", ann['id']).execute()
                st.rerun()
            st.markdown("---")

# ----------------- 탭 2: 교육 일정 관리 -----------------
with tab2:
    st.subheader("새 교육 일정 등록")
    with st.form("sched_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            s_date = st.date_input("교육 날짜")
        with col2:
            s_time = st.time_input("교육 시간")
            
        s_location = st.text_input("교육 장소", placeholder="예: 올림픽 수영장 다이빙풀")
        s_cap = st.number_input("최대 인원", min_value=1, max_value=20, value=4)
        
        s_submit = st.form_submit_button("일정 등록하기", type="primary")
        
        if s_submit:
            if not s_location:
                st.error("교육 장소를 입력해주세요.")
            else:
                supabase.table("fd_schedules").insert({
                    "schedule_date": str(s_date),
                    "schedule_time": str(s_time),
                    "location": s_location,
                    "max_capacity": s_cap
                }).execute()
                st.success("✅ 일정이 등록되었습니다!")
                st.rerun()

    st.divider()
    st.subheader("등록된 교육 일정 목록")
    scheds = get_schedules()
    if scheds:
        for s in scheds:
            st.write(f"📅 **{s['schedule_date']} {s['schedule_time'][:5]}** | 📍 {s['location']} | 최대 {s['max_capacity']}명")
            if st.button("삭제", key=f"del_sch_{s['id']}"):
                supabase.table("fd_schedules").delete().eq("id", s['id']).execute()
                st.rerun()
            st.markdown("---")

# ----------------- 탭 3: 예약자 현황 (상세) -----------------
with tab3:
    st.subheader("날짜별 교육 예약 현황")
    scheds = get_schedules()
    if not scheds:
        st.info("등록된 교육 일정이 없습니다.")
    else:
        for s in scheds:
            apps = get_applications(s['id'])
            
            with st.expander(f"📅 {s['schedule_date']} {s['schedule_time'][:5]} - {s['location']} (현재 {len(apps)}/{s['max_capacity']}명)", expanded=True):
                if not apps:
                    st.write("아직 신청자가 없습니다.")
                else:
                    # 관리자용이므로 생년월일을 포함하여 모두 보여줌
                    df_data = []
                    for a in apps:
                        df_data.append({
                            "신청일시": a['created_at'][:16].replace('T', ' '),
                            "이름": a['name'],
                            "생년월일": a['birthdate'],
                            "면책동의": "✅ 동의" if a['liability_consent'] else "❌ 미동의",
                            "대여장비": a['rental_equipment'] if a['rental_equipment'] else "없음"
                        })
                    df = pd.DataFrame(df_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
