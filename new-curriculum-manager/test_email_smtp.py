import os
import smtplib
import toml
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_smtp():
    secrets_path = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")
    if not os.path.exists(secrets_path):
        print(f"Error: secrets.toml not found at {secrets_path}")
        return

    try:
        config = toml.load(secrets_path)
        smtp_config = config.get("smtp", {})
    except Exception as e:
        print(f"Error reading secrets.toml: {e}")
        return

    smtp_server = smtp_config.get("server")
    smtp_port = smtp_config.get("port", 587)
    smtp_user = smtp_config.get("user")
    smtp_password = smtp_config.get("password")

    if not smtp_server or not smtp_user or not smtp_password:
        print("Error: SMTP configurations are missing in secrets.toml.")
        print(f"Loaded config: server={smtp_server}, port={smtp_port}, user={smtp_user}, password={'***' if smtp_password else None}")
        return

    print("SMTP Configuration Loaded Successfully:")
    print(f"  Server: {smtp_server}")
    print(f"  Port: {smtp_port}")
    print(f"  User: {smtp_user}")
    print("Sending test email...")

    subject = "[대양고 수강신청] SMTP 설정 테스트 메일"
    body = f"""
    안녕하세요, 관리자님.
    
    대양고등학교 학점제 수강신청 시스템의 SMTP 메일 발송 설정이 정상적으로 완료되었습니다.
    본 이메일은 설정된 계정({smtp_user})의 발송 테스트 메일입니다.
    
    감사합니다.
    """

    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = smtp_user  # Send to self (the admin)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        print(f"Connecting to {smtp_server}:{smtp_port}...")
        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        print("Logging in...")
        server.login(smtp_user, smtp_password)
        print(f"Sending email to {smtp_user}...")
        server.sendmail(smtp_user, smtp_user, msg.as_string())
        server.quit()
        print("\nSUCCESS: Test email successfully sent! Please check your inbox.")
    except Exception as e:
        print(f"\nFAILURE: Failed to send test email: {e}")

if __name__ == "__main__":
    test_smtp()
