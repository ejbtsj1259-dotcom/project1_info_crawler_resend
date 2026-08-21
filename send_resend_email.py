import os
import sys
import datetime
import pandas as pd
from dotenv import load_dotenv
import resend

# Ensure console output is in UTF-8 on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Load environment variables from .env file
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
HTML_PREVIEW_PATH = os.path.join(REPORTS_DIR, "email_preview.html")
LOG_CSV_PATH = os.path.join(REPORTS_DIR, "resend_send_log.csv")
ERROR_LOG_PATH = os.path.join(LOGS_DIR, "resend_error_log.txt")

os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

def migrate_old_log_if_needed(df):
    # If columns are from the old schema (timestamp, receiver, status, message_id...), rename and align
    if "timestamp" in df.columns and "receiver" in df.columns:
        df = df.rename(columns={
            "timestamp": "sent_at",
            "receiver": "receiver_email",
            "message_id": "resend_email_id"
        })
        if "subject" not in df.columns:
            # Add historical default subject
            df["subject"] = f"🚀 [IT 정책 뉴스] 일간 추천 리포트 - {datetime.datetime.now().strftime('%Y-%m-%d')}"
        # Keep only required columns
        required_cols = ["sent_at", "receiver_email", "subject", "status", "resend_email_id"]
        df = df[[col for col in required_cols if col in df.columns]]
    return df

def log_sending_status(receiver, subject, status, email_id=""):
    sent_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_log = {
        "sent_at": [sent_at],
        "receiver_email": [receiver],
        "subject": [subject],
        "status": [status],
        "resend_email_id": [email_id]
    }
    new_df = pd.DataFrame(new_log)
    
    if os.path.exists(LOG_CSV_PATH):
        try:
            old_df = pd.read_csv(LOG_CSV_PATH, encoding="utf-8")
            old_df = migrate_old_log_if_needed(old_df)
            
            combined_df = pd.concat([old_df, new_df], ignore_index=True)
            combined_df.to_csv(LOG_CSV_PATH, index=False, encoding="utf-8-sig")
        except Exception as e:
            log_error_file(f"로그 기록 중 예외 (새로 저장 진행): {str(e)}")
            new_df.to_csv(LOG_CSV_PATH, index=False, encoding="utf-8-sig")
    else:
        new_df.to_csv(LOG_CSV_PATH, index=False, encoding="utf-8-sig")

def log_error_file(error_msg):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(ERROR_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {error_msg}\n")

def check_duplicate_send(receiver, subject):
    if not os.path.exists(LOG_CSV_PATH):
        return False
        
    try:
        df = pd.read_csv(LOG_CSV_PATH, encoding="utf-8")
        df = migrate_old_log_if_needed(df)
        
        required_cols = ["sent_at", "receiver_email", "subject", "status", "resend_email_id"]
        if not all(col in df.columns for col in required_cols):
            return False
            
        # Get today's date
        today_str = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # Filter for same receiver, subject, success status, and sent today
        duplicate_rows = df[
            (df['receiver_email'] == receiver) & 
            (df['subject'] == subject) & 
            (df['status'] == "Success") & 
            (df['sent_at'].str.startswith(today_str))
        ]
        
        return len(duplicate_rows) > 0
    except Exception as e:
        log_error_file(f"중복 체크 중 에러: {str(e)}")
        return False

def print_403_guidance(sender):
    print("\n" + "=" * 60)
    print("      ⚠️ [403 Forbidden] 발신 도메인 검증 오류 발생 안내")
    print("=" * 60)
    print("  Resend API에서 403 권한 에러(Unauthorized/Forbidden)가 발생했습니다.")
    print("  이는 사용하시려는 발신 주소(SENDER_EMAIL)가 인증되지 않았기 때문입니다.\n")
    print("  💡 해결 방법:")
    print("   1. 기본 Onboarding 주소 사용:")
    print(f"      - 현재 발신자: {sender}")
    print("      - Resend 무료 플랜은 도메인을 인증하기 전까지는 오직")
    print("        'onboarding@resend.dev' 주소로만 발송할 수 있습니다.")
    print("        .env 파일에서 SENDER_EMAIL=onboarding@resend.dev 로 맞춰주세요.")
    print("   2. 개인 도메인 인증:")
    print("      - 만약 개인 도메인 주소(예: info@yourdomain.com)를 발신자로 쓰고 싶다면,")
    print("        Resend Dashboard -> Domains 메뉴에서 본인 도메인의 DNS 레코드(SPF, DKIM)")
    print("        등록을 완료하고 상태가 'Verified'로 설정되어 있는지 확인해 주세요.")
    print("=" * 60 + "\n")

def main():
    print("==========================================")
    print("     📧 Resend 이메일 발송 모듈 (v2.1)     ")
    print("==========================================\n")
    
    # 1. Check if HTML preview file exists
    if not os.path.exists(HTML_PREVIEW_PATH):
        print(f"❌ 발송할 이메일 HTML 파일이 존재하지 않습니다: {HTML_PREVIEW_PATH}")
        print("email_report_builder.py를 먼저 실행해 주세요.")
        sys.exit(1)
        
    try:
        with open(HTML_PREVIEW_PATH, "r", encoding="utf-8") as f:
            html_content = f.read()
    except Exception as e:
        print(f"❌ HTML 파일을 읽는 도중 오류가 발생했습니다: {str(e)}")
        sys.exit(1)
        
    # 2. Read and validate environment variables
    api_key = os.getenv("RESEND_API_KEY")
    sender = os.getenv("SENDER_EMAIL")
    receiver = os.getenv("RECEIVER_EMAIL")
    enable_send_str = str(os.getenv("ENABLE_REAL_EMAIL_SEND", "false")).lower()
    enable_send = (enable_send_str == "true" or enable_send_str == "1")
    
    # Generate standard subject
    subject = f"🚀 [IT 정책 뉴스] 일간 추천 리포트 - {datetime.datetime.now().strftime('%Y-%m-%d')}"
    
    if not api_key or api_key == "re_your_api_key_here" or not enable_send:
        print("🔍 [미리보기 모드] 실제 발송이 활성화되어 있지 않습니다 (.env 확인 필요)")
        sys.exit(0)
        
    # 3. Duplicate Send Check
    print("🔍 중복 발송 여부를 조회 중입니다...")
    if check_duplicate_send(receiver, subject):
        print("\n" + "=" * 60)
        print("  🚫 [발송 차단] 중복 발송 방지 가동")
        print("=" * 60)
        print(f"  • 대상 수신자: {receiver}")
        print(f"  • 메일 제목: {subject}")
        print("  • 결과: 오늘 이미 동일한 수신자와 제목으로 성공적으로")
        print("          발송된 기록이 존재하여 발송을 안전하게 취소합니다.")
        print("=" * 60 + "\n")
        sys.exit(0)
    else:
        print("  ✔ 중복 기록 없음. 신규 발송을 계속 진행합니다.")
        
    # 4. Actual Send
    print(f"\n🚀 [실제 발송 모드] Resend API 발송을 요청합니다...")
    print(f"  • 발신자: {sender}")
    print(f"  • 수신자: {receiver}")
    
    try:
        resend.api_key = api_key
        
        params = {
            "from": sender,
            "to": [receiver],
            "subject": subject,
            "html": html_content
        }
        
        response = resend.Emails.send(params)
        message_id = response.get("id", "N/A")
        
        print(f"\n✔ 이메일 발송 성공!")
        print(f"  • Resend 응답 ID (Message ID): {message_id}")
        
        # Log success in csv
        log_sending_status(receiver, subject, "Success", email_id=message_id)
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ 이메일 발송 실패: {error_msg}")
        
        # Log failure in error file
        log_error_file(f"발송 실패 (수신자: {receiver}): {error_msg}")
        
        # Log failure in csv
        log_sending_status(receiver, subject, "Failed")
        
        # Diagnose 403 error
        if "403" in error_msg or "unauthorized" in error_msg.lower() or "forbidden" in error_msg.lower():
            print_403_guidance(sender)
            
    print("\n==========================================")

if __name__ == "__main__":
    main()
