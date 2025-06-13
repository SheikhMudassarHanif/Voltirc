import streamlit as st
import json
import re
import threading
import time
import requests
import smtplib
import csv
from email.mime.text import MIMEText
from datetime import datetime

import os
import pandas as pd
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import threading

CONFIG_FILE = "config.json"
LOG_FILE = "log.csv"

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Thread-safe bot control
bot_control_event = threading.Event()
bot_thread = None
file_lock = threading.Lock()  # Add file lock for thread-safe file operations

# Shared status variable
current_status = {"live": False, "timestamp": "Never", "mode": "Live"}

# Load and Save Config
def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                if "test_mode" not in config:
                    config["test_mode"] = False
                if "monitor_url" not in config:
                    config["monitor_url"] = "https://blspakistan.com"
                if "test_url" not in config:
                    config["test_url"] = ""
                if "emails" not in config:
                    config["emails"] = []
                if "whatsapp_numbers" not in config:
                    config["whatsapp_numbers"] = []
                if "gmail" not in config:
                    config["gmail"] = {"sender_email": "", "app_password": ""}
                if "check_interval_sec" not in config:
                    config["check_interval_sec"] = 300
                if "whatsapp_sender" not in config:
                    config["whatsapp_sender"] = ""
                if "twilio" not in config:
                    config["twilio"] = {
                        "account_sid": "",
                        "auth_token": "",
                        "content_sid": ""
                    }
                return config
    except Exception as e:
        print(f"[{datetime.now()}] Error loading config: {e}")
    
    return {
        "test_mode": False,
        "monitor_url": "https://blspakistan.com",
        "test_url": "",
        "emails": [],
        "whatsapp_numbers": [],
        "gmail": {"sender_email": "", "app_password": ""},
        "check_interval_sec": 300,
        "whatsapp_sender": "",
        "twilio": {
            "account_sid": "",
            "auth_token": "",
            "content_sid": ""
        }
    }

def save_config(data):
    try:
        if "test_urls" in data:
            del data["test_urls"]
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"[{datetime.now()}] Error saving config: {e}")

def format_phone(number):
    number = number.strip()
    if re.match(r"^0\d{10}$", number):
        return "+92" + number[1:]
    elif re.match(r"^\+92\d{10}$", number):
        return number
    return None

# def send_email_alert(subject, body, config):
    try:
        if not config["emails"]:
            print(f"[{datetime.now()}] ⚠️ No email recipients configured")
            return
            
        if not config["gmail"]["sender_email"] or not config["gmail"]["app_password"]:
            print(f"[{datetime.now()}] ❌ Gmail credentials not configured")
            return

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = config["gmail"]["sender_email"]
        msg["To"] = ", ".join(config["emails"])
        
        print(f"[{datetime.now()}] 📧 Attempting to send email to: {config['emails']}")
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(config["gmail"]["sender_email"], config["gmail"]["app_password"])
            server.sendmail(config["gmail"]["sender_email"], config["emails"], msg.as_string())
            print(f"[{datetime.now()}] ✅ Email sent successfully to: {config['emails']}")
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Email failed: {str(e)}")

def send_email_alert(subject, body, config):
    try:
        if not config["emails"]:
            print(f"[{datetime.now()}] ⚠️ No email recipients configured")
            return

        # Hardcoded default Gmail credentials
        default_sender_email = "sheikhmudassar1942003@gmail.com"  # Replace with your actual email
        default_app_password = "fwdg ymtu zwzg lywe"    # Replace with your actual app password

        # Use config credentials if provided, otherwise use defaults
        sender_email = config["gmail"].get("sender_email", "").strip()
        app_password = config["gmail"].get("app_password", "").strip()
        
        if sender_email and app_password:
            print(f"[{datetime.now()}] Using user-provided Gmail credentials: {sender_email}")
        else:
            sender_email = default_sender_email
            app_password = default_app_password
            print(f"[{datetime.now()}] Using default Gmail credentials: {sender_email}")

        if not sender_email or not app_password:
            print(f"[{datetime.now()}] ❌ Gmail credentials not configured")
            return

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = ", ".join(config["emails"])
        
        print(f"[{datetime.now()}] 📧 Attempting to send email to: {config['emails']}")
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, config["emails"], msg.as_string())
            print(f"[{datetime.now()}] ✅ Email sent successfully to: {config['emails']}")
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Email failed: {str(e)}")




def send_whatsapp_alert(message, config):
    try:
        if not config["whatsapp_numbers"]:
            print(f"[{datetime.now()}] ⚠️ No WhatsApp recipients configured")
            return
            
        account_sid = 'ACcb33680cd74385251c187ef3ae745bdc'
        auth_token = '105bb238ff519c37ad48df3373cbc576'
        from_number = '+14155238886'
        content_sid = config["twilio"].get("content_sid", "HXb5b62575e6e4ff6129ad7c8efe1f983e")
        sandbox_name= "brush-experience"

        print(f"[{datetime.now()}] 📱 Attempting to send WhatsApp messages to: {config['whatsapp_numbers']} with content SID: {content_sid if content_sid else 'None'}")
        
        client = Client(account_sid, auth_token)
        for number in config.get("whatsapp_numbers", []):
            formatted = format_phone(number)
            if formatted:
                try:
                    # Try template message if content_sid is provided
                    if content_sid:
                        print(f"[{datetime.now()}] Trying template message for {formatted} with content SID: {content_sid}")
                        message_obj = client.messages.create(
                            from_=f"whatsapp:{from_number}",
                            content_sid=content_sid,
                            content_variables=json.dumps({"1": message}),
                            to=f"whatsapp:{formatted}"
                        )
                        print(f"[{datetime.now()}] ✅ WhatsApp template sent to: {formatted}, SID: {message_obj.sid}, Status: {message_obj.status}")
                    else:
                        # Send plain text message if no content_sid
                        print(f"[{datetime.now()}] Trying plain text message for {formatted}")
                        message_obj = client.messages.create(
                            from_=f"whatsapp:{from_number}",
                            body=message,
                            to=f"whatsapp:{formatted}"
                        )
                        print(f"[{datetime.now()}] ✅ WhatsApp plain text sent to: {formatted}, SID: {message_obj.sid}, Status: {message_obj.status}")
                except TwilioRestException as e:
                    # Log detailed error and try plain text if template fails
                    error_details = f"Code: {e.code}, Status: {e.status}, Message: {str(e)}"
                    if hasattr(e, 'response') and e.response:
                        error_details += f", Response: {e.response.text}"
                    print(f"[{datetime.now()}] ❌ WhatsApp failed to {formatted}: {error_details}")
                    if content_sid:
                        print(f"[{datetime.now()}] Retrying with plain text for {formatted}")
                        try:
                            message_obj = client.messages.create(
                                from_=f"whatsapp:{from_number}",
                                body=message,
                                to=f"whatsapp:{formatted}"
                            )
                            print(f"[{datetime.now()}] ✅ WhatsApp plain text retry sent to: {formatted}, SID: {message_obj.sid}, Status: {message_obj.status}")
                        except TwilioRestException as retry_e:
                            retry_error_details = f"Code: {retry_e.code}, Status: {retry_e.status}, Message: {str(retry_e)}"
                            if hasattr(retry_e, 'response') and retry_e.response:
                                retry_error_details += f", Response: {retry_e.response.text}"
                            print(f"[{datetime.now()}] ❌ WhatsApp plain text retry failed to {formatted}: {retry_error_details}")
                except Exception as e:
                    print(f"[{datetime.now()}] ❌ Unexpected error sending WhatsApp to {formatted}: {str(e)}")
            else:
                print(f"[{datetime.now()}] ❌ Invalid phone number format: {number}")
    except Exception as e:
        print(f"[{datetime.now()}] ❌ WhatsApp alert error: {str(e)}")

def ensure_log_header():
    try:
        if not os.path.exists(LOG_FILE) or os.stat(LOG_FILE).st_size == 0:
            with open(LOG_FILE, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Timestamp", "Status", "Notification Sent", "Mode", "URL", "Response Code", "Error"])
            print("[✔] Log file initialized with header.")
    except Exception as e:
        print(f"[✘] Error ensuring log header: {e}")

def log_status(timestamp, status, sent, mode, url, response_code=None, error=None):
    """Log status with all required fields"""
    ensure_log_header()
    try:
        with open(LOG_FILE, mode='a', newline='') as f:
            writer = csv.writer(f)
            row = [
                timestamp,
                status,
                sent,
                mode,
                url,
                str(response_code or "N/A"),
                str(error or "N/A")
            ]
            writer.writerow(row)
            f.flush()
            print(f"[{timestamp}] Logged: {status} - {url} - Code: {response_code if response_code is not None else 'N/A'}")
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Failed to write to log: {e}")

def check_url(url):
    """Check if a URL is accessible"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        is_live = response.status_code == 200
        print(f"[{datetime.now()}] Checked {url}: Status {response.status_code}, Length {len(response.text)}, Live: {is_live}")
        return is_live, response.status_code, None
    except requests.RequestException as e:
        print(f"[{datetime.now()}] ❌ Error checking {url}: {str(e)}")
        return False, None, str(e)

def run_bot():
    global current_status
    config = load_config()
    TEST_MODE = config.get("test_mode", False)
    URL = config.get("test_url", "") if TEST_MODE else config.get("monitor_url", "")
    INTERVAL = config.get("check_interval_sec", 300)
    was_live = False

    current_status["mode"] = "Test Mode" if TEST_MODE else "Live Mode"

    while bot_control_event.is_set():
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            is_live, status_code, error = check_url(URL)
            
            current_status["live"] = is_live
            current_status["timestamp"] = now

            log_status(
                timestamp=now,
                status="LIVE" if is_live else "OFFLINE",
                sent="No",
                mode=current_status["mode"],
                url=URL,
                response_code=status_code,
                error=error
            )

            if is_live and not was_live:
                subject = f"🔔 Website is LIVE: {URL}"
                if TEST_MODE:
                    subject = "[TEST MODE] " + subject
                body = f"The website at {URL} is now accessible.\nTime: {now}\nStatus Code: {status_code}"
                
                # Send notifications
                print(f"[{datetime.now()}] 🔔 Website is LIVE! Sending notifications...")
                send_email_alert(subject, body, config)
                send_whatsapp_alert(body, config)
                
                log_status(
                    timestamp=now,
                    status="LIVE",
                    sent="Yes",
                    mode=current_status["mode"],
                    url=URL,
                    response_code=status_code,
                    error=None
                )
                was_live = True
            elif not is_live:
                was_live = False
            
            time.sleep(INTERVAL)
        except Exception as e:
            print(f"[{datetime.now()}] ❌ Error in monitor loop: {str(e)}")
            time.sleep(INTERVAL)

# --- Streamlit UI ---

# Initialize session state
st.session_state.setdefault("authenticated", False)
st.session_state.setdefault("bot_status", "Stopped")
st.session_state.setdefault("config_saved", False)

if not st.session_state.authenticated:
    st.title("🔐 BLS Monitor Admin Panel")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login = st.form_submit_button("Login")
    if login:
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            st.session_state.authenticated = True
            st.success("Logged in successfully")
            st.rerun()
        else:
            st.error("Invalid credentials")
else:
    config = load_config()
    st.title("🛠️ Admin Dashboard")

    # Logout button
    if st.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.session_state.bot_status = "Stopped"
        bot_control_event.clear()
        st.success("Logged out")
        st.rerun()

    # Live status display
    st.subheader("🌐 Website Current Status")
    status_text = "🟢 LIVE" if current_status["live"] else "🔴 OFFLINE"
    st.markdown(f"**Status:** {status_text}")
    st.markdown(f"**Last Checked:** {current_status['timestamp']}")
    st.markdown(f"**Mode:** {current_status['mode']}")
    st.markdown(f"**Bot Status:** `{st.session_state.bot_status}`")

    # Interval
    st.subheader("Check Interval (sec)")
    current_interval = config.get("check_interval_sec", 300)
    if current_interval < 30:
        current_interval = 30
        config["check_interval_sec"] = current_interval
        save_config(config)
    
    interval = st.number_input("Interval", min_value=30, value=current_interval)
    if interval != current_interval:
        config["check_interval_sec"] = interval
        save_config(config)
        if st.session_state.bot_status == "Running":
            st.warning("Please restart the bot for interval changes to take effect")

    # Test Mode Toggle
    test_mode = st.checkbox("Enable Test Mode", value=config.get("test_mode", False))
    if test_mode != config.get("test_mode", False):
        config["test_mode"] = test_mode
        save_config(config)
        if st.session_state.bot_status == "Running":
            st.warning("Please restart the bot for test mode changes to take effect")

    # Monitor URL (only show in live mode)
    if not test_mode:
        st.subheader("Live Monitor URL")
        if st.session_state.bot_status == "Running":
            st.markdown(f"**Current URL:** `{config.get('monitor_url', '')}`")
            st.info("Monitor URL cannot be changed while the bot is running")
        else:
            monitor_url = st.text_input("Monitor URL", value=config.get("monitor_url", ""))
            if monitor_url != config.get("monitor_url", ""):
                config["monitor_url"] = monitor_url
                save_config(config)
                st.success("Monitor URL updated")
    else:
        st.subheader("Test URL")
        if st.session_state.bot_status == "Running":
            st.markdown(f"**Current URL:** `{config.get('test_url', '')}`")
            st.info("Test URL cannot be changed while the bot is running")
        else:
            test_url = st.text_input("Test URL", value=config.get("test_url", ""))
            if test_url != config.get("test_url", ""):
                config["test_url"] = test_url
                save_config(config)
                st.success("Test URL updated")

    # WhatsApp Configuration
    st.subheader("WhatsApp Configuration")
    
    st.markdown("**Twilio Credentials**")
    twilio_sid = st.text_input("Twilio Account SID", value=config["twilio"].get("account_sid", ""))
    twilio_token = st.text_input("Twilio Auth Token", type="password", value=config["twilio"].get("auth_token", ""))
    twilio_content = st.text_input("Twilio Content SID", value=config["twilio"].get("content_sid", ""))
    if st.button("Update Twilio Credentials"):
        config["twilio"] = {
            "account_sid": twilio_sid,
            "auth_token": twilio_token,
            "content_sid": twilio_content
        }
        save_config(config)
        st.success("Twilio credentials updated")

    st.markdown("**Sender Number**")
    sender_number = st.text_input("WhatsApp Sender Number (e.g., +14155238886)", value=config.get("whatsapp_sender", ""), disabled=True)
    if st.button("Update Sender Number"):
        formatted_sender = format_phone(sender_number)
        if formatted_sender:
            config["whatsapp_sender"] = formatted_sender
            save_config(config)
            st.success(f"Sender number updated to {formatted_sender}")
        else:
            st.error("Invalid sender number format")
    
    st.markdown("**Recipient Numbers**")
    new_num = st.text_input("Add Recipient Number")
    if st.button("Add Number"):
        formatted = format_phone(new_num)
        if formatted and formatted not in config["whatsapp_numbers"]:
            config["whatsapp_numbers"].append(formatted)
            save_config(config)
            st.success(f"Added {formatted}")
        elif not formatted:
            st.error("Invalid number format")
        else:
            st.warning("Number already exists")
    for i, number in enumerate(config["whatsapp_numbers"]):
        col1, col2 = st.columns([5, 1])
        col1.write(number)
        if col2.button("❌", key=f"del_num_{i}"):
            config["whatsapp_numbers"].pop(i)
            save_config(config)
            st.rerun()

    # Emails
    st.subheader("Email Recipients")
    new_email = st.text_input("Add Email")
    if st.button("Add Email"):
        if re.match(r"[^@]+@[^@]+\.[^@]+", new_email) and new_email not in config["emails"]:
            config["emails"].append(new_email)
            save_config(config)
            st.success("Email added")
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
            st.error("Invalid email format")
        else:
            st.warning("Email already exists")
    for i, email in enumerate(config["emails"]):
        col1, col2 = st.columns([5,1])
        col1.write(email)
        if col2.button("❌", key=f"del_email_{i}"):
            config["emails"].pop(i)
            save_config(config)
            st.rerun()

    # Gmail Credentials
    st.subheader("Gmail Settings")
    sender_email = st.text_input("Sender Email", value=config["gmail"].get("sender_email", ""))
    if sender_email != config["gmail"].get("sender_email", ""):
        config["gmail"]["sender_email"] = sender_email
        save_config(config)
        st.success("Sender email updated")
    
    app_password = st.text_input("App Password", type="password", value=config["gmail"].get("app_password", ""))
    if app_password != config["gmail"].get("app_password", ""):
        config["gmail"]["app_password"] = app_password
        save_config(config)
        st.success("App password updated")

    # Display recent logs
    st.subheader("📋 Recent Activity Log")
    try:
        if os.path.exists(LOG_FILE):
            df = pd.read_csv(LOG_FILE)
            if not df.empty:
                required_columns = ['Timestamp', 'Status', 'Notification Sent', 'Mode', 'URL', 'Response Code', 'Error']
                for col in required_columns:
                    if col not in df.columns:
                        df[col] = "N/A"
                
                df['Status'] = df['Status'].apply(lambda x: f"🟢 {x}" if x == "LIVE" else f"🔴 {x}")
                df['Notification Sent'] = df['Notification Sent'].apply(lambda x: "✅" if x == "Yes" else "❌")
                df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                df = df.sort_values('Timestamp', ascending=False).head(10)
                
                st.dataframe(
                    df.style.apply(
                        lambda x: ['color: green' if 'LIVE' in str(x) else 'color: red' if 'OFFLINE' in str(x) else '' for _ in x],
                        subset=['Status']
                    ),
                    use_container_width=True,
                    height=300
                )
                
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Full Logs",
                    data=csv,
                    file_name="monitoring_logs.csv",
                    mime="text/csv"
                )
            else:
                st.info("No logs available yet.")
        else:
            st.info("Log file not found. Logs will appear once the bot starts monitoring.")
            ensure_log_header()
    except Exception as e:
        st.error(f"Error reading logs: {str(e)}")
        try:
            ensure_log_header()
            st.info("Created new log file with headers")
        except Exception as e:
            st.error(f"Failed to create log file: {str(e)}")

    # Bot Control
    st.subheader("Configuration and Control")
    if st.button("💾 Save Configuration"):
        save_config(config)
        st.session_state.config_saved = True
        st.success("Configuration saved successfully")
    
    def start_bot():
        global bot_thread
        save_config(config)
        bot_control_event.set()
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        st.session_state.bot_status = "Running"
        st.success("Bot started")
        st.rerun()

    if st.session_state.bot_status == "Stopped":
        if st.button("▶️ Start Bot"):
            if not st.session_state.get("config_saved", False):
                st.error("Please save the configuration before starting the bot")
            elif test_mode and not config.get("test_url"):
                st.error("Please add a test URL before starting the bot")
            elif not test_mode and not config.get("monitor_url"):
                st.error("Monitor URL is not configured")
            elif not config["gmail"].get("sender_email") or not config["gmail"].get("app_password"):
                st.error("Gmail sender email and app password must be configured")
            elif not config["emails"] and not config["whatsapp_numbers"]:
                st.error("At least one email or WhatsApp recipient must be configured")
            else:
                start_bot()
    else:
        if st.button("⏹ Stop Bot"):
            bot_control_event.clear()
            if bot_thread:
                bot_thread.join(timeout=1)  # Wait briefly for thread to exit
                bot_thread = None
            st.session_state.bot_status = "Stopped"
            st.success("Bot stopped")
            st.rerun()