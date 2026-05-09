import streamlit as st
from database import supabase, get_announcements, get_schedules, get_applications
from datetime import datetime

# 페이지 설정 (모바일 최적화 및 밝은 테마)
st.set_page_config(page_title="브로시스 프리다이빙", page_icon="🌊", layout="centered", initial_sidebar_state="collapsed")

# 커스텀 CSS (프리다이빙 테마)
st.markdown("""
<style>
    .stApp {
        background-color: #f0f8ff; /* 아주 옅은 바다색 (AliceBlue) */
    }
    .main-header {
        color: #0077b6; /* Ocean Blue */
        text-align: center;
        font-weight: 800;
        margin-bottom: 30px;
    }
    .announce-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border-left: 5px solid #00b4d8;
    }
    .sched-card {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    /* 모바일을 위해 글자 크기 키우기 */
    p, li, .stMarkdown {
        font-size: 1.05rem !important;
    }
    h3 {
        color: #03045e;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-header'>🌊 브로시스 프리다이빙</h1>", unsafe_allow_html=True)
st.markdown("초보자도 쉽고 즐겁게 프리다이빙을 배울 수 있는 공간입니다. 아래에서 공지를 확인하고 교육을 예약하세요!")

st.divider()

# 1. 공지사항 섹션
st.markdown("### 📢 최근 공지사항")
announcements = get_announcements()
if not announcements:
    st.info("등록된 공지사항이 없습니다.")
else:
    for ann in announcements[:3]: # 최근 3개만 표시
        date_str = datetime.fromisoformat(ann['created_at']).strftime("%Y-%m-%d %H:%M")
        st.markdown(f"""
        <div class='announce-card'>
            <h4>{ann['title']}</h4>
            <p style='font-size:0.85em; color:gray;'>{date_str}</p>
            <p>{ann['content']}</p>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# 2. 교육 일정 및 예약 섹션
st.markdown("### 🗓️ 교육 일정 및 예약")
schedules = get_schedules()

if not schedules:
    st.info("현재 열려있는 교육 일정이 없습니다.")
else:
    # 일정별로 아코디언(Expander) 생성
    for sched in schedules:
        apps = get_applications(sched['id'])
        current_count = len(apps)
        max_count = sched['max_capacity']
        
        is_full = current_count >= max_count
        status_text = "🔴 마감" if is_full else f"🟢 예약 가능 ({current_count}/{max_count}명)"
        
        sched_title = f"{sched['schedule_date']} {sched['schedule_time'][:5]} | {sched['location']} | {status_text}"
        
        with st.expander(sched_title):
            # 신청자 현황 표시 (생년월일 숨김)
            st.markdown("#### 👥 현재 신청자 현황")
            if current_count == 0:
                st.write("아직 신청자가 없습니다. 첫 번째로 신청해보세요!")
            else:
                for a in apps:
                    consent = "✅ 동의" if a['liability_consent'] else "❌ 미동의"
                    equip = a['rental_equipment'] if a['rental_equipment'] else "없음"
                    st.markdown(f"- **{a['name']}**님 | 장비대여: {equip} | 면책동의: {consent}")
                    
            st.markdown("---")
            
            # 신청 폼
            if not is_full:
                st.markdown("#### 📝 예약 신청하기")
                with st.form(key=f"form_{sched['id']}"):
                    name = st.text_input("이름", placeholder="홍길동")
                    birthdate = st.text_input("생년월일", placeholder="YYYY-MM-DD (예: 1990-01-01)")
                    rental = st.text_input("대여 필요 장비", placeholder="예: 마스크, 오리발(260mm) / 없으면 생략")
                    
                    st.markdown("**면책 동의서**")
                    st.info("본인은 프리다이빙 교육 중 발생할 수 있는 위험성을 인지하며, 본인의 과실로 인한 사고에 대해 강사에게 책임을 묻지 않을 것에 동의합니다.")
                    consent = st.checkbox("위 면책 동의서 내용을 확인하였으며 동의합니다.")
                    
                    submit = st.form_submit_button("예약 신청하기", type="primary", use_container_width=True)
                    
                    if submit:
                        if not name or not birthdate:
                            st.error("이름과 생년월일을 모두 입력해주세요.")
                        elif not consent:
                            st.error("면책 동의에 체크해주셔야 예약이 가능합니다.")
                        else:
                            try:
                                supabase.table("fd_applications").insert({
                                    "schedule_id": sched['id'],
                                    "name": name,
                                    "birthdate": birthdate,
                                    "liability_consent": consent,
                                    "rental_equipment": rental
                                }).execute()
                                st.success(f"🎉 {name}님, 예약이 완료되었습니다!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"예약 중 오류가 발생했습니다: {e}")
            else:
                st.error("이 교육 일정은 마감되었습니다.")
