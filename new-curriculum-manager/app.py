import streamlit as st
import pandas as pd
import datetime
import io
import uuid
from database import (
    init_db, get_courses, get_student, enroll_student, 
    cancel_enrollment, get_enrollments_by_course, get_student_enrollment,
    is_admin, add_student, add_admin, get_email_logs, calculate_attendance_score, 
    get_student_sort_key, update_course_capacity, get_unenrolled_students,
    verify_login, update_password, get_all_students
)
from email_sender import send_cancellation_email

# Initialize database on startup
init_db()

# Streamlit Page Config
st.set_page_config(
    page_title="대양고등학교 학점제 수강신청 시스템",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Vanilla CSS - Premium Light Mode)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Noto+Sans+KR:wght@300;400;700;900&display=swap');
    
    .stApp {
        background: #f8fafc;
        font-family: 'Outfit', 'Noto Sans KR', sans-serif;
        color: #1e293b;
    }
    
    /* Header styling */
    .title-container {
        padding: 2.5rem;
        background: #ffffff;
        border-radius: 24px;
        border: 1px solid #e2e8f0;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04);
    }
    
    .main-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(90deg, #1e40af, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .sub-title {
        color: #64748b;
        font-size: 1.1rem;
        font-weight: 400;
    }
    
    /* Custom Card Design */
    .course-card {
        background: #ffffff;
        border-radius: 20px;
        border: 1px solid #e2e8f0;
        padding: 1.8rem;
        margin-bottom: 1.5rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 20px rgba(15, 23, 42, 0.02);
    }
    
    .course-card:hover {
        transform: translateY(-5px);
        border-color: #c084fc;
        box-shadow: 0 12px 30px rgba(99, 102, 241, 0.08);
    }
    
    .course-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.5rem;
    }
    
    .instructor-tag {
        display: inline-block;
        background: #e0e7ff;
        color: #4338ca;
        padding: 4px 12px;
        border-radius: 8px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    
    .capacity-label {
        display: flex;
        justify-content: space-between;
        font-size: 0.95rem;
        color: #475569;
        margin-bottom: 0.4rem;
    }
    
    .capacity-bar-container {
        background: #e2e8f0;
        border-radius: 8px;
        height: 10px;
        overflow: hidden;
        margin-bottom: 1.2rem;
    }
    
    .capacity-bar-fill {
        height: 100%;
        border-radius: 8px;
        transition: width 0.5s ease-in-out;
    }
    
    .bar-normal { background: linear-gradient(90deg, #2563eb, #60a5fa); }
    .bar-warning { background: linear-gradient(90deg, #ca8a04, #facc15); }
    .bar-full { background: linear-gradient(90deg, #db2777, #f43f5e); }
    
    /* Profiles and statuses */
    .profile-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(15, 23, 42, 0.02);
    }
    
    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 10px;
        font-size: 0.8rem;
        font-weight: 700;
    }
    
    .status-safe { background-color: #dcfce7; color: #15803d; }
    .status-warning { background-color: #fef9c3; color: #854d0e; }
    .status-danger { background-color: #fee2e2; color: #b91c1c; }
    .status-info { background-color: #dbeafe; color: #1d4ed8; }
    
</style>
""", unsafe_allow_html=True)

# Application Header
st.markdown("""
<div class="title-container">
    <div class="main-title">대양고등학교 학점제 수강신청 시스템 🏫</div>
    <div class="sub-title">성실한 출결 관리가 약속하는 공정한 교과 선택의 기회</div>
</div>
""", unsafe_allow_html=True)

# --- Authentication & Login Panel ---
if "user_email" not in st.session_state:
    st.session_state.user_email = None
    st.session_state.user_role = None
if "force_password_change" not in st.session_state:
    st.session_state.force_password_change = False

if st.session_state.user_email is None:
    st.subheader("🔑 수강신청 로그인")
    st.info("💡 대양고등학교 학교 계정(@daeyang.hs.kr)과 비밀번호로 로그인해 주세요.")
    
    col_login1, col_login2 = st.columns([3, 2])
    
    with col_login1:
        with st.form("login_form", clear_on_submit=False):
            login_email = st.text_input("학교 구글 이메일 (@daeyang.hs.kr)", placeholder="dy26학번@daeyang.hs.kr")
            login_password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
            submit_login = st.form_submit_button("로그인 👤", type="primary", use_container_width=True)
            
            if submit_login:
                if not login_email.endswith("@daeyang.hs.kr"):
                    st.error("❌ 대양고등학교 학교 도메인(@daeyang.hs.kr) 계정만 로그인 가능합니다.")
                elif not login_password:
                    st.error("❌ 비밀번호를 입력해 주세요.")
                else:
                    role, result = verify_login(login_email, login_password)
                    if role:
                        st.session_state.user_email = login_email
                        st.session_state.user_role = role
                        if login_password == "dy6400580":
                            st.session_state.force_password_change = True
                        else:
                            st.session_state.force_password_change = False
                        st.toast(f"{login_email} 로그인 성공!", icon="✅")
                        st.rerun()
                    else:
                        st.error(f"❌ 로그인 실패: {result}")
                    
    with col_login2:
        st.markdown("""
        <div style="background: #f1f5f9; padding: 1.5rem; border-radius: 16px; border: 1px solid #e2e8f0; color: #475569;">
            <h4 style="margin-top:0; color: #1e293b;">📋 모의 테스트 계정 안내</h4>
            <p style="font-size:0.9rem; margin-bottom: 0.5rem;">개발 테스트용 임시 계정 정보입니다.</p>
            <ul style="font-size:0.85rem; padding-left: 1.2rem; margin-bottom:0.8rem;">
                <li><strong>초기 비밀번호:</strong> <code style="color: #6d28d9; font-weight:bold;">dy6400580</code></li>
                <li><strong>관리자:</strong> <code>parkminah@daeyang.hs.kr</code></li>
                <li><strong>출결만점 학생:</strong> <code>student1@daeyang.hs.kr</code></li>
                <li><strong>지각 1회 학생:</strong> <code>student2@daeyang.hs.kr</code></li>
                <li><strong>결석 1회 학생:</strong> <code>student3@daeyang.hs.kr</code></li>
            </ul>
            <p style="font-size:0.8rem; color:#64748b; margin-bottom:0;">※ 로그인 후 사이드바 메뉴를 통해 언제든지 비밀번호를 수정할 수 있습니다.</p>
        </div>
        """, unsafe_allow_html=True)
        
    st.stop()

# Logout Handler
if st.sidebar.button("🔓 로그아웃"):
    st.session_state.user_email = None
    st.session_state.user_role = None
    st.session_state.force_password_change = False
    st.rerun()

# Welcome message in sidebar
st.sidebar.markdown(f"**접속 계정:**  \n`{st.session_state.user_email}`")
st.sidebar.markdown(f"**사용자 권한:**  \n`{st.session_state.user_role.upper()}`")

# Change Password UI in Sidebar
with st.sidebar.expander("🔑 비밀번호 변경"):
    with st.form("sidebar_pwd_change_form", clear_on_submit=False):
        current_pwd = st.text_input("현재 비밀번호", type="password", key="change_pwd_curr")
        new_pwd = st.text_input("새 비밀번호", type="password", key="change_pwd_new")
        confirm_pwd = st.text_input("새 비밀번호 확인", type="password", key="change_pwd_conf")
        submit_sidebar = st.form_submit_button("변경 적용 💾", use_container_width=True)
        
        if submit_sidebar:
            if not current_pwd or not new_pwd or not confirm_pwd:
                st.error("모든 입력란을 채워주세요.")
            elif new_pwd != confirm_pwd:
                st.error("새 비밀번호가 일치하지 않습니다.")
            else:
                role, res = verify_login(st.session_state.user_email, current_pwd)
                if role:
                    if update_password(st.session_state.user_email, st.session_state.user_role, new_pwd):
                        st.success("비밀번호 변경 완료!")
                        st.toast("비밀번호 변경 성공", icon="🔑")
                    else:
                        st.error("데이터베이스 수정 중 오류가 발생했습니다.")
                else:
                    st.error("현재 비밀번호가 다릅니다.")

st.sidebar.divider()

# --- Force Password Change View ---
if st.session_state.get("force_password_change", False):
    st.subheader("🔒 보안을 위한 비밀번호 변경 안내")
    st.warning("⚠️ 현재 초기 비밀번호(dy6400580)를 사용 중이십니다. 첫 로그인 시에는 안전한 개인 비밀번호로 반드시 변경하셔야 서비스를 이용하실 수 있습니다.")
    
    col_force1, col_force2 = st.columns([3, 2])
    with col_force1:
        with st.form("force_pwd_change_form", clear_on_submit=False):
            new_pwd_force = st.text_input("새 비밀번호 입력", type="password", key="force_pwd_new")
            confirm_pwd_force = st.text_input("새 비밀번호 확인", type="password", key="force_pwd_conf")
            submit_force = st.form_submit_button("비밀번호 변경 완료 및 로그인 💾", type="primary", use_container_width=True)
            
            if submit_force:
                if not new_pwd_force or not confirm_pwd_force:
                    st.error("새 비밀번호를 모두 입력해 주세요.")
                elif new_pwd_force == "dy6400580":
                    st.error("초기 비밀번호인 'dy6400580'은 사용할 수 없습니다. 다른 비밀번호를 지정해 주세요.")
                elif new_pwd_force != confirm_pwd_force:
                    st.error("입력하신 새 비밀번호가 일치하지 않습니다.")
                else:
                    if update_password(st.session_state.user_email, st.session_state.user_role, new_pwd_force):
                        st.session_state.force_password_change = False
                        st.success("비밀번호가 안전하게 변경되었습니다! 이제 서비스를 이용하실 수 있습니다.")
                        st.toast("비밀번호 변경 및 로그인 완료", icon="✅")
                        st.rerun()
                    else:
                        st.error("데이터베이스 수정 중 오류가 발생했습니다. 다시 시도해 주세요.")
                    
    with col_force2:
        st.info("""
        💡 **비밀번호 작성 가이드**
        * 비밀번호는 다른 사람이 쉽게 유추할 수 없는 안전한 문자 조합을 권장합니다.
        * 변경 후에는 다음 로그인 시 변경한 비밀번호를 사용해 주세요.
        """)
    st.stop() # Block further execution to force password change!

# --- STUDENT PORTAL ---
if st.session_state.user_role == "student":
    student_data = get_student(st.session_state.user_email)
    
    if not student_data:
        st.error("학생 정보가 조회되지 않습니다. 로그아웃 후 다시 시도해 주세요.")
        st.stop()
        
    # Student Info Display
    st.subheader("🧑‍🎓 학생 프로필 및 출결 상황")
    
    penalty_score = calculate_attendance_score(student_data)
    
    col_info1, col_info2, col_info3, col_info4 = st.columns(4)
    with col_info1:
        st.metric("이름 / 학적", f"{student_data['name']} ({student_data['grade']}학년 {student_data['class']}반 {student_data['number']}번)")
    with col_info2:
        st.metric("최종 출결 점수", f"{penalty_score} 점", help="미인정 결석 -5점, 미인정 지각 -3점")
    with col_info3:
        st.metric("미인정 출결 현황", f"결석 {student_data['unexcused_absences']}회 / 지각 {student_data['unexcused_tardiness']}회")
    with col_info4:
        st.metric("질병 출결 현황", f"결석 {student_data['sick_absences']}회 / 지각 {student_data['sick_tardiness']}회 / 조퇴 {student_data['sick_early_leaves']}회")
        
    st.divider()
    
    # Get Current Enrollment
    current_enrollment = get_student_enrollment(st.session_state.user_email)
    
    st.subheader("📚 개설 과목 신청 현황")
    
    if current_enrollment:
        st.success(f"🎉 현재 **'{current_enrollment['course_name']}'** 과목 수강신청이 성공적으로 접수되어 있습니다.")
        if st.button("❌ 수강신청 철회 (취소)"):
            if cancel_enrollment(st.session_state.user_email, current_enrollment['course_id']):
                st.toast("수강신청이 철회되었습니다.", icon="🗑️")
                st.rerun()
            else:
                st.error("취소 처리 중 오류가 발생했습니다.")
    else:
        st.info("⚠️ 현재 신청된 수강 과목이 없습니다. 아래 개설 과목 목록에서 신청해 주세요.")
        
    st.divider()
    
    # 4 Core Elective Courses List
    st.subheader("🏫 개설 과목 리스트")
    st.caption("과목 목록은 [e스포츠 코스, IT네트워크 코스, 전자코스, 전기코스] 순으로 고정되어 표시됩니다.")
    
    courses = get_courses()
    
    # Fix the order as requested: e스포츠 코스, IT네트워크 코스, 전자코스, 전기코스
    fixed_order = ["e스포츠 코스", "IT네트워크 코스", "전자코스", "전기코스"]
    ordered_courses = []
    for course_name in fixed_order:
        c = next((item for item in courses if item['name'] == course_name), None)
        if c:
            ordered_courses.append(c)
            
    # Display Course Cards
    for course in ordered_courses:
        enrolled_students = get_enrollments_by_course(course['id'])
        current_num = len(enrolled_students)
        capacity = course['capacity']
        
        fill_percentage = min(100, int((current_num / capacity) * 100))
        
        bar_class = "bar-normal"
        status_text = "수강신청 가능 (여유)"
        status_badge_class = "status-safe"
        
        if current_num >= capacity:
            bar_class = "bar-full"
            status_text = "정원 초과 (출결 점수 경쟁 필요)"
            status_badge_class = "status-danger"
        elif current_num >= capacity - 1:
            bar_class = "bar-warning"
            status_text = "마감 임박"
            status_badge_class = "status-warning"
            
        warning_message = ""
        is_my_enrolled = current_enrollment and current_enrollment['course_id'] == course['id']
        
        if not is_my_enrolled and current_num >= capacity:
            candidate_list = enrolled_students + [student_data]
            candidate_list.sort(key=get_student_sort_key)
            worst = candidate_list[-1]
            
            if worst['student_email'] == st.session_state.user_email:
                warning_message = "⚠️ 현재 본인의 출결 점수로는 신청 즉시 탈락(밀어내기 실패)되는 위험 권역입니다."
                status_badge_class = "status-danger"
                status_text = "밀어내기 실패 예상"
            else:
                warning_message = "💡 현재 출결 점수 기준, 신청 시 최하위 우선순위 학생을 밀어내고 수강신청을 완료할 수 있습니다."
                status_badge_class = "status-info"
                status_text = "밀어내기 가능 권역"
                
        # Card Layout (Vanilla CSS - Light theme compliant)
        st.markdown(f"""
        <div class="course-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div class="course-title">{course['name']}</div>
                <span class="status-badge {status_badge_class}">{status_text}</span>
            </div>
            <p style="color: #475569; font-size: 0.95rem; margin-top: 1rem; margin-bottom: 1.2rem;">{course['description']}</p>
            <div class="capacity-label">
                <span>신청 현황</span>
                <span><strong>{current_num}</strong> / {capacity} 명</span>
            </div>
            <div class="capacity-bar-container">
                <div class="capacity-bar-fill {bar_class}" style="width: {fill_percentage}%;"></div>
            </div>
            <p style="color: #e11d48; font-size: 0.9rem; font-weight: bold;">{warning_message}</p>
        </div>
        """, unsafe_allow_html=True)
        
        col_btn, _ = st.columns([1, 4])
        with col_btn:
            if is_my_enrolled:
                st.button("신청 완료됨", key=f"btn_done_{course['id']}", disabled=True)
            else:
                if current_enrollment is not None:
                    btn_text = "🔄 수강 과목 변경"
                    btn_type = "secondary"
                else:
                    btn_text = "📝 수강신청"
                    btn_type = "primary"
                    
                if st.button(btn_text, key=f"btn_req_{course['id']}", type=btn_type):
                    result = enroll_student(st.session_state.user_email, course['id'])
                    if result['success']:
                        st.success(result['message'])
                        if "kicked_student" in result:
                            ks = result['kicked_student']
                            st.warning(f"📣 [밀어내기 발생] {ks['name']} 학생이 정원 초과로 인해 수강 취소 처리되었습니다.")
                            with st.spinner("해당 학생에게 취소 통보 이메일을 전송하는 중..."):
                                success, msg = send_cancellation_email(ks['email'], ks['name'], ks['course_name'], str(uuid.uuid4()))
                                if success:
                                    st.success(f"📧 이메일 통보 완료: {ks['email']}")
                                else:
                                    st.error(f"📧 이메일 발송 오류: {msg}")
                        st.rerun()
                    else:
                        st.error(result['message'])
                        
    # Live Leaderboard (경쟁 순위 시각화)
    st.divider()
    st.subheader("📊 과목별 실시간 우선순위 경쟁 순위 현황")
    st.caption("각 과목에 수강신청을 완료한 학생들의 출결 우선순위 명단입니다. 하단에 위치할수록 마감 시 밀려날 위험이 큽니다. (※ **⭐** 표시는 로그인한 **본인**의 위치를 나타냅니다.)")
    
    col_lead1, col_lead2 = st.columns(2)
    
    for idx, course in enumerate(ordered_courses):
        target_col = col_lead1 if idx % 2 == 0 else col_lead2
        with target_col:
            st.markdown(f"#### 🏷️ {course['name']} (정원: {course['capacity']}명)")
            enrolled = get_enrollments_by_course(course['id'])
            
            if not enrolled:
                st.info("현재 수강신청한 학생이 없습니다.")
            else:
                enrolled.sort(key=get_student_sort_key)
                
                lead_table = []
                for rank, s in enumerate(enrolled, 1):
                    is_me = "⭐️" if s['student_email'] == st.session_state.user_email else ""
                    score = calculate_attendance_score(s)
                    
                    status_zone = "안전"
                    if rank > course['capacity']:
                        status_zone = "대기/밀려남"
                    elif rank >= course['capacity'] - 1:
                        status_zone = "위험"
                        
                    lead_table.append({
                        "순위": rank,
                        "구분": is_me,
                        "출결점수": score,
                        "미인정(결/지)": f"{s['unexcused_absences']}/{s['unexcused_tardiness']}",
                        "질병(결/지/조)": f"{s['sick_absences']}/{s['sick_tardiness']}/{s['sick_early_leaves']}",
                        "신청상태": status_zone
                    })
                    
                st.table(pd.DataFrame(lead_table))

# --- ADMIN PORTAL ---
elif st.session_state.user_role == "admin":
    st.subheader("🛡️ 관리자 대시보드")
    
    admin_tab1, admin_tab2, admin_tab3, admin_tab4 = st.tabs([
        "🏫 과목 및 정원 설정", 
        "📋 과목별 수강 현황", 
        "👥 학생 및 관리자 추가/관리",
        "📧 취소 알림 이메일 로그"
    ])
    
    # Tab 1: Course Capacity Settings
    with admin_tab1:
        st.markdown("### ⚙️ 과목별 정원(제한 인원) 수정")
        courses = get_courses()
        for c in courses:
            col_c1, col_c2, col_c3 = st.columns([2, 1, 1])
            with col_c1:
                st.write(f"**과목명:** {c['name']}")
            with col_c2:
                new_cap = st.number_input(f"제한 인원 ({c['name']})", min_value=1, max_value=100, value=c['capacity'], key=f"cap_{c['id']}")
            with col_c3:
                if st.button("저장 💾", key=f"save_cap_{c['id']}", type="primary"):
                    update_course_capacity(c['id'], new_cap)
                    st.toast(f"'{c['name']}' 정원이 {new_cap}명으로 변경되었습니다.", icon="✅")
                    st.rerun()
                    
    # Tab 2: Enrolled Students List & Unenrolled Students List
    with admin_tab2:
        st.markdown("### 📋 개설 과목별 수강생 명단 및 미신청자 조회")
        courses = get_courses()
        
        options = [c['name'] for c in courses] + ["⚠️ [미신청] 수강신청 미완료 학생 목록"]
        selected_option = st.selectbox("조회 대상을 선택하세요", options)
        
        if selected_option == "⚠️ [미신청] 수강신청 미완료 학생 목록":
            unenrolled_list = get_unenrolled_students()
            st.write(f"**미신청 학생 수:** {len(unenrolled_list)}명")
            
            if not unenrolled_list:
                st.success("🎉 모든 학생이 수강신청을 완료하였습니다!")
            else:
                rows = []
                for s in unenrolled_list:
                    score = calculate_attendance_score(s)
                    rows.append({
                        "학생 이름": s['name'],
                        "이메일 주소": s['email'],
                        "학년": s['grade'],
                        "반": s['class'],
                        "번호": s['number'],
                        "출결 점수": score,
                        "미인정 결석": s['unexcused_absences'],
                        "미인정 지각": s['unexcused_tardiness'],
                        "질병 결석": s['sick_absences'],
                        "질병 지각": s['sick_tardiness'],
                        "질병 조퇴": s['sick_early_leaves']
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True)
        else:
            selected_course = next(item for item in courses if item['name'] == selected_option)
            enrolled_list = get_enrollments_by_course(selected_course['id'])
            
            st.write(f"**과목명:** {selected_course['name']} | **제한 인원:** {selected_course['capacity']}명 | **현재 신청 인원:** {len(enrolled_list)}명")
            
            if not enrolled_list:
                st.info("현재 수강신청을 완료한 학생이 없습니다.")
            else:
                enrolled_list.sort(key=get_student_sort_key)
                
                rows = []
                for rank, s in enumerate(enrolled_list, 1):
                    score = calculate_attendance_score(s)
                    rows.append({
                        "우선순위 순위": rank,
                        "학생 이름": s['student_name'],
                        "이메일 주소": s['student_email'],
                        "학년": s['grade'],
                        "반": s['class'],
                        "번호": s['number'],
                        "출결 점수": score,
                        "미인정 결석": s['unexcused_absences'],
                        "미인정 지각": s['unexcused_tardiness'],
                        "질병 결석": s['sick_absences'],
                        "질병 지각": s['sick_tardiness'],
                        "질병 조퇴": s['sick_early_leaves'],
                        "신청 시간": s['created_at']
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True)
            
    # Tab 3: Student & Admin Management (New Tab)
    with admin_tab3:
        st.markdown("### 👥 학생 및 관리자 추가/관리")
        
        sub_tab_student, sub_tab_admin = st.tabs(["🧑‍🎓 학생 관리", "🛡️ 관리자 관리"])
        
        # Student Management
        with sub_tab_student:
            st.markdown("#### 1. 개별 학생 수동 추가")
            
            col_s_add1, col_s_add2, col_s_add3 = st.columns(3)
            with col_s_add1:
                s_email = st.text_input("학생 이메일 (@daeyang.hs.kr)", key="s_add_email")
                s_name = st.text_input("학생 이름", key="s_add_name")
            with col_s_add2:
                s_grade = st.number_input("학년", min_value=1, max_value=3, value=1, key="s_add_grade")
                s_class = st.number_input("반", min_value=1, max_value=20, value=1, key="s_add_class")
                s_number = st.number_input("번호", min_value=1, max_value=50, value=1, key="s_add_number")
            with col_s_add3:
                s_un_abs = st.number_input("미인정 결석 횟수", min_value=0, value=0, key="s_add_un_abs")
                s_un_tard = st.number_input("미인정 지각 횟수", min_value=0, value=0, key="s_add_un_tard")
                s_sk_abs = st.number_input("병결석 횟수", min_value=0, value=0, key="s_add_sk_abs")
                s_sk_tard = st.number_input("병지각 횟수", min_value=0, value=0, key="s_add_sk_tard")
                s_sk_early = st.number_input("병조퇴 횟수", min_value=0, value=0, key="s_add_sk_early")
                
            if st.button("학생 등록 👤", type="primary", key="s_add_submit"):
                if not s_email.endswith("@daeyang.hs.kr"):
                    st.error("❌ 이메일은 반드시 @daeyang.hs.kr 도메인이어야 합니다.")
                elif not s_name.strip():
                    st.error("❌ 학생 이름을 입력해 주세요.")
                else:
                    att_record = {
                        "unexcused_absences": s_un_abs,
                        "unexcused_tardiness": s_un_tard,
                        "sick_absences": s_sk_abs,
                        "sick_tardiness": s_sk_tard,
                        "sick_early_leaves": s_sk_early
                    }
                    if add_student(s_email, s_name, s_grade, s_class, s_number, att_record):
                        st.success(f"🎉 {s_name} 학생이 성공적으로 등록되었습니다.")
                        st.rerun()
                    else:
                        st.error("등록 중 데이터베이스 오류가 발생했습니다.")
                        
            st.divider()
            st.markdown("#### 2. 학생 엑셀 일괄 업로드")
            
            # Download Student Template
            mock_s_df = pd.DataFrame([
                {
                    "이메일": "student_test@daeyang.hs.kr",
                    "이름": "홍길동",
                    "학년": 1,
                    "반": 1,
                    "번호": 10,
                    "미인정결석": 0,
                    "미인정지각": 1,
                    "병결석": 0,
                    "병지각": 0,
                    "병조퇴": 0
                }
            ])
            s_output = io.BytesIO()
            with pd.ExcelWriter(s_output, engine='openpyxl') as writer:
                mock_s_df.to_excel(writer, index=False, sheet_name='학생일괄등록')
            s_template_data = s_output.getvalue()
            
            st.download_button(
                label="📥 학생 일괄 등록용 엑셀 양식 다운로드",
                data=s_template_data,
                file_name="대양고_학생_일괄등록_양식.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_s_template"
            )
            
            s_uploaded_file = st.file_uploader("학생 등록 엑셀 파일 선택", type=["xlsx"], key="s_excel_upload")
            if s_uploaded_file is not None:
                try:
                    df_s_upload = pd.read_excel(s_uploaded_file)
                    st.dataframe(df_s_upload.head(5))
                    if st.button("업로드 실행 🚀", key="s_excel_submit"):
                        success_count = 0
                        required_cols = ["이메일", "이름", "학년", "반", "번호", "미인정결석", "미인정지각", "병결석", "병지각", "병조퇴"]
                        
                        missing_cols = [c for c in required_cols if c not in df_s_upload.columns]
                        if missing_cols:
                            st.error(f"❌ 엑셀 파일에 필수 열이 누락되었습니다: {missing_cols}")
                        else:
                            for idx, row in df_s_upload.iterrows():
                                email = str(row["이메일"]).strip()
                                name = str(row["이름"]).strip()
                                grade = int(row["학년"])
                                class_num = int(row["반"])
                                number = int(row["번호"])
                                
                                att_dict = {
                                    "unexcused_absences": int(row["미인정결석"]),
                                    "unexcused_tardiness": int(row["미인정지각"]),
                                    "sick_absences": int(row["병결석"]),
                                    "sick_tardiness": int(row["병지각"]),
                                    "sick_early_leaves": int(row["병조퇴"])
                                }
                                if add_student(email, name, grade, class_num, number, att_dict):
                                    success_count += 1
                            st.success(f"🎉 총 {success_count}명의 학생 등록이 완료되었습니다.")
                            st.rerun()
                except Exception as e:
                    st.error(f"에러: {e}")
            
            st.divider()
            st.markdown("#### 3. 학생 비밀번호 초기화")
            st.caption("비밀번호를 분실한 학생의 비밀번호를 시스템 초기 비밀번호인 **'dy6400580'**으로 재설정합니다. 해당 학생은 다음 로그인 시 강제로 비밀번호를 다시 설정해야 합니다.")
            
            all_students = get_all_students()
            if all_students:
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    grades = sorted(list(set([s['grade'] for s in all_students if s['grade'] is not None])))
                    grade_filter = st.selectbox("학년 필터", ["전체"] + [f"{g}학년" for g in grades], key="pwd_reset_grade_filter")
                with col_f2:
                    classes = sorted(list(set([s['class'] for s in all_students if s['class'] is not None])))
                    class_filter = st.selectbox("반 필터", ["전체"] + [f"{c}반" for c in classes], key="pwd_reset_class_filter")
                
                # Filter students
                filtered_students = all_students
                if grade_filter != "전체":
                    selected_grade = int(grade_filter.replace("학년", ""))
                    filtered_students = [s for s in filtered_students if s['grade'] == selected_grade]
                if class_filter != "전체":
                    selected_class = int(class_filter.replace("반", ""))
                    filtered_students = [s for s in filtered_students if s['class'] == selected_class]
                
                if filtered_students:
                    # Clean label formatting: [1학년 1반 01번] 김철수 (student1@daeyang.hs.kr)
                    student_options = {}
                    for s in filtered_students:
                        g = s.get('grade') or 0
                        c = s.get('class') or 0
                        n = s.get('number') or 0
                        name = s.get('name') or "이름없음"
                        email = s.get('email') or ""
                        label = f"[{g}학년 {c}반 {n:02d}번] {name} ({email})"
                        student_options[label] = s
                        
                    selected_student_label = st.selectbox("초기화할 학생 선택", options=list(student_options.keys()), key="pwd_reset_student")
                    
                    if st.button("비밀번호 초기화 실행 🔑", type="secondary", key="pwd_reset_submit"):
                        target_student = student_options[selected_student_label]
                        if update_password(target_student['email'], "student", "dy6400580"):
                            st.success(f"🎉 {target_student['name']} 학생의 비밀번호가 초기값('dy6400580')으로 재설정되었습니다.")
                            st.toast("비밀번호 초기화 완료", icon="🔑")
                        else:
                            st.error("데이터베이스 수정 중 오류가 발생했습니다.")
                else:
                    st.warning("⚠️ 필터 조건에 해당하는 학생이 없습니다.")
            else:
                st.info("등록된 학생이 없습니다.")
                    
        # Admin Management
        with sub_tab_admin:
            st.markdown("#### 1. 개별 관리자 수동 추가")
            
            a_email = st.text_input("관리자 이메일 (@daeyang.hs.kr)", key="a_add_email")
            if st.button("관리자 등록 🛡️", type="primary", key="a_add_submit"):
                if not a_email.endswith("@daeyang.hs.kr"):
                    st.error("❌ 이메일은 반드시 @daeyang.hs.kr 도메인이어야 합니다.")
                else:
                    if add_admin(a_email):
                        st.success(f"🎉 {a_email} 계정이 관리자로 등록되었습니다.")
                        st.rerun()
                    else:
                        st.error("등록 중 오류가 발생했습니다.")
                        
            st.divider()
            st.markdown("#### 2. 관리자 엑셀 일괄 업로드")
            
            # Download Admin Template
            mock_a_df = pd.DataFrame([{"이메일": "admin_test@daeyang.hs.kr"}])
            a_output = io.BytesIO()
            with pd.ExcelWriter(a_output, engine='openpyxl') as writer:
                mock_a_df.to_excel(writer, index=False, sheet_name='관리자등록')
            a_template_data = a_output.getvalue()
            
            st.download_button(
                label="📥 관리자 일괄 등록용 엑셀 양식 다운로드",
                data=a_template_data,
                file_name="대양고_관리자_일괄등록_양식.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_a_template"
            )
            
            a_uploaded_file = st.file_uploader("관리자 등록 엑셀 파일 선택", type=["xlsx"], key="a_excel_upload")
            if a_uploaded_file is not None:
                try:
                    df_a_upload = pd.read_excel(a_uploaded_file)
                    st.dataframe(df_a_upload.head(5))
                    if st.button("관리자 업로드 실행 🚀", key="a_excel_submit"):
                        success_count = 0
                        if "이메일" not in df_a_upload.columns:
                            st.error("❌ '이메일' 열이 존재하지 않습니다.")
                        else:
                            for idx, row in df_a_upload.iterrows():
                                email = str(row["이메일"]).strip()
                                if email.endswith("@daeyang.hs.kr"):
                                    if add_admin(email):
                                        success_count += 1
                            st.success(f"🎉 총 {success_count}명의 관리자 등록이 완료되었습니다.")
                            st.rerun()
                except Exception as e:
                    st.error(f"에러: {e}")
                    
    # Tab 4: Email Log Viewer
    with admin_tab4:
        st.markdown("### 📧 수강 강제취소 이메일 자동 통보 이력")
        st.caption("정원 초과 및 출결 우선순위 밀어내기에 의해 자동으로 발송 처리된 이메일 통보 내역입니다.")
        
        email_logs = get_email_logs()
        if not email_logs:
            st.info("발송된 강제 취소 안내 메일 이력이 없습니다.")
        else:
            df_logs = pd.DataFrame(email_logs)
            st.dataframe(df_logs, use_container_width=True)
