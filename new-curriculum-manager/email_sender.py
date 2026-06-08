import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import streamlit as st
from database import update_email_status

def send_cancellation_email(student_email, student_name, course_name, log_id):
    """
    Sends an email notification to the student whose course enrollment was cancelled/displaced.
    Supports SMTP configuration in Streamlit secrets, otherwise falls back to a mock simulation.
    """
    subject = f"[대양고 수강신청] '{course_name}' 과목 수강신청 자동 취소 안내"
    
    body = f"""
    안녕하세요, {student_name} 학생.
    
    대양고등학교 학점제 수강신청 시스템에서 안내드립니다.
    
    귀하가 신청하신 '{course_name}' 과목은 수강 정원이 초과되었습니다.
    대양고등학교 수강신청 기준에 따라, 등록자 간 출결 감점 점수 및 동점자 우선순위를 심사한 결과
    귀하의 신청 건이 부득이하게 자동 취소 처리되었습니다.
    
    [취소된 신청 정보]
    - 학생명: {student_name}
    - 과목명: {course_name}
    - 취소 사유: 정원 초과 및 출결 순위(미인정 결석/지각 페널티)에 따른 밀어내기
    
    즉시 수강신청 시스템(http://localhost:8501)에 접속하여 정원에 여유가 있는 다른 과목을 선택해 주시기 바랍니다.
    
    감사합니다.
    대양고등학교 교육과정 담당자 드림
    """

    # Check if SMTP configuration is available in streamlit secrets
    smtp_configured = False
    smtp_server = ""
    smtp_port = 587
    smtp_user = ""
    smtp_password = ""
    
    try:
        if "smtp" in st.secrets:
            smtp_server = st.secrets["smtp"].get("server", "")
            smtp_port = int(st.secrets["smtp"].get("port", 587))
            smtp_user = st.secrets["smtp"].get("user", "")
            smtp_password = st.secrets["smtp"].get("password", "")
            if smtp_server and smtp_user and smtp_password:
                smtp_configured = True
    except Exception:
        pass

    if smtp_configured:
        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = student_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, student_email, msg.as_string())
            server.quit()
            
            update_email_status(log_id, "Sent")
            print(f"Email successfully sent to {student_email} via SMTP.")
            return True, "SMTP 발송 성공"
        except Exception as e:
            error_msg = str(e)
            update_email_status(log_id, "Failed", error_msg)
            print(f"Failed to send email to {student_email} via SMTP: {error_msg}")
            return False, f"SMTP 발송 실패: {error_msg}"
    else:
        # Mock Simulation (Log it locally)
        mock_log = f"""
============================================================
[MOCK EMAIL SENT]
To: {student_email}
Subject: {subject}
Content:
{body}
============================================================
"""
        print(mock_log)
        update_email_status(log_id, "Sent (Simulated)")
        return True, "시뮬레이션 발송 완료 (콘솔 로그 기록)"
