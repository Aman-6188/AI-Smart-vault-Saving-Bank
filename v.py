# v.py - AI Voice smart Bank (wake word + continuous serial + command mode)
import serial
import threading
import time
import os
import uuid
import requests
import asyncio
from edge_tts import Communicate
import speech_recognition as sr
import cv2
from datetime import datetime, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import matplotlib.pyplot as plt
import webbrowser
import json
import speech_recognition as sr
import asyncio
import webbrowser
import threading
import time
# --- Missing imports ---
import re
from datetime import timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from email.mime.base import MIMEBase
from email import encoders


# --- Global folders ---
IMAGES_FOLDER = "Depositor_Images"
GRAPHS_FOLDER = "graphs"
REPORTS_FOLDER = "reports"

os.makedirs(IMAGES_FOLDER, exist_ok=True)
os.makedirs(GRAPHS_FOLDER, exist_ok=True)
os.makedirs(REPORTS_FOLDER, exist_ok=True)

# --- Global deposit storage ---
daily_deposits = []
monthly_deposits = []
balance_lock = threading.Lock()


# --- Email sending helper (Gmail version) ---
def send_email_with_attachments(subject, body, attachments=None):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER       
        msg["To"] = EMAIL_RECEIVER      
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        if attachments:
            for file_path in attachments:
                if os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            "Content-Disposition",
                            f"attachment; filename={os.path.basename(file_path)}"
                        )
                        msg.attach(part)

        # --- GMAIL SMTP ---
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)  # Gmail + App Password
        server.send_message(msg)
        server.quit()

        return True

    except Exception as e:
        safe_print("Email sending error:", e)
        return False


# --- ThingSpeak update ---
def update_thingspeak(value):
    try:
        url = f"https://api.thingspeak.com/update?api_key={THINGSPEAK_API_KEY}&field1={value}"
        requests.get(url, timeout=5)
    except:
        safe_print("ThingSpeak update error")




PORT = ""
BAUD = 115200

THINGSPEAK_CHANNEL_ID = ""
THINGSPEAK_API_KEY = ""

TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""

EMAIL_SENDER = ""
EMAIL_PASSWORD = "add ur own"
EMAIL_RECEIVER = "kaman171230@gmail.com"

WAKE_WORDS = ["jarvis", "vaulto"]
        
VOICE_NAME = "en-IN-NeerjaNeural"   
REMINDER_HOUR = 9
TARGET_AMOUNT = 100




daily_deposits = []         
last_total_reported = None  

tts_queue = []
tts_lock = threading.Lock()
tts_worker_running = True

try:
    ser = serial.Serial(PORT, BAUD, timeout=1)
    time.sleep(1)
except Exception as e:
    print("Serial open error:", e)
    ser = None

def safe_print(*args, **kwargs):
    """Thread-safe print if needed"""
    print(*args, **kwargs)

async def _speak_async(text: str):
    """Edge TTS async save + play"""
    try:
        filename = f"voice_{uuid.uuid4().hex}.mp3"
        tts = Communicate(text, voice=VOICE_NAME)
        await tts.save(filename)
        # playsound with small safety
        import playsound
        playsound.playsound(filename)
        os.remove(filename)
    except Exception as e:
        safe_print("Error in speak():", e)

def speak_enqueue(text: str):
    """Add text to TTS queue"""
    with tts_lock:
        tts_queue.append(text)

def tts_worker():
    """Background worker that speaks queued texts one by one."""
    while tts_worker_running:
        item = None
        with tts_lock:
            if tts_queue:
                item = tts_queue.pop(0)
        if item:
            try:
                asyncio.run(_speak_async(item))
            except Exception as e:
                safe_print("TTS run error:", e)
        else:
            time.sleep(0.15)

def send_telegram_message(message, photo_path=None):
    try:
        base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
        requests.post(f"{base_url}/sendMessage",
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": message})
        if photo_path and os.path.exists(photo_path):
            with open(photo_path, "rb") as photo:
                requests.post(f"{base_url}/sendPhoto",
                              data={"chat_id": TELEGRAM_CHAT_ID},
                              files={"photo": photo})
        safe_print("Telegram notification sent.")
    except Exception as e:
        safe_print("Telegram error:", e)



WAKE_WORDS = ["jarvis", "vaulto"]


GRAPH_URL = f"https://thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/charts/1"

r = sr.Recognizer()

def listen_command(timeout=5, phrase_time_limit=6):
    with sr.Microphone() as source:
        print("Listening...")
        audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        try:
            text = r.recognize_google(audio).lower()
            print("Heard:", text)
            return text
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            return ""

def handle_command(cmd):
    cmd = cmd.lower()
    if "show" in cmd and "graph" in cmd:
        safe_print(" Opening graph window...")
        webbrowser.open(GRAPH_URL)
        speak_enqueue("Opening your savings graph now, Aman.")

    elif "close" in cmd and "graph" in cmd:
        safe_print("Closing graph window...")

        os.system("taskkill /IM msedge.exe /F 2>nul")
        os.system("taskkill /IM chrome.exe /F 2>nul")
        speak_enqueue("Closed the graph window.")

    elif "balance" in cmd:
        balance = get_current_balance()
        speak_enqueue(f"Your current balance is {balance} rupees.")

    else:
        speak_enqueue("Sorry Aman, I didn't understand that.")

def wake_word_listener():
    import asyncio
    active_mode = False
    last_active_time = 0
    mic_ready = False

    time.sleep(2)
    safe_print("Wake-word listener ready (passive). Say 'Jarvis' or 'Vaulto' to activate.")

    while True:
        try:
            if not active_mode:
                safe_print(" Passive mode: waiting for wake word...")
                cmd = listen_command(timeout=10, phrase_time_limit=5)

                if any(word in cmd for word in WAKE_WORDS):
                    speak_enqueue("Yes Aman, I am listening.")
                    safe_print(" Wake word detected.")
                    active_mode = True
                    last_active_time = time.time()

            else:
                safe_print("Active mode: waiting for command...")
                cmd = listen_command(timeout=10, phrase_time_limit=8)
                print("You said:", cmd)   
                if cmd:

                   
                    if ("daily report" in cmd or
                        "send me daily report" in cmd or
                        "send daily report" in cmd or
                        "today report" in cmd or
                        "email daily report" in cmd):

                        speak_enqueue("Sending daily report to your email now.")
                        send_daily_report(manual=True)

                   
                    elif ("monthly report" in cmd or
                          "send me monthly report" in cmd or
                          "send monthly report" in cmd or
                          "this month report" in cmd or
                          "email monthly report" in cmd):

                        speak_enqueue("Sending monthly report to your email.")
                        send_monthly_report(manual=True)

                   
                    elif "graph" in cmd:
                        if "show" in cmd:
                            speak_enqueue("Opening your savings graph now, Aman.")
                            show_graph()
                        elif "close" in cmd:
                            os.system("taskkill /IM msedge.exe /F")
                            speak_enqueue("Closed the graph window.")

                    elif "balance" in cmd:
                        bal = get_current_balance()
                        speak_enqueue(f"Your current balance is {bal} rupees.")

                    elif "exit" in cmd or "sleep" in cmd:
                        speak_enqueue("Okay Aman, going to sleep mode.")
                        active_mode = False

                    else:
                        speak_enqueue("Sorry Aman, I didn't understand that.")

                    last_active_time = time.time()

                
                if time.time() - last_active_time > 15:
                    safe_print("💤 No voice detected — going back to sleep.")
                    speak_enqueue("Going back to sleep mode.")
                    active_mode = False

        except Exception as e:
            safe_print("Wake listener error:", e)
            time.sleep(0.5)


def capture_photo():
    try:
        cam = cv2.VideoCapture(0)
        time.sleep(0.5)
        ret, frame = cam.read()
        if ret:
            folder = "Depositor_Images"
            os.makedirs(folder, exist_ok=True)
            filename = os.path.join(folder, f"deposit_{uuid.uuid4().hex}.jpg")
            cv2.imwrite(filename, frame)
            cam.release()
            cv2.destroyAllWindows()
            safe_print(f"Photo saved as {filename}")
            return filename
        cam.release()
        cv2.destroyAllWindows()
    except Exception as e:
        safe_print("Camera error:", e)
    return None

def get_current_balance():
    try:
        url = f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/feeds.json?api_key={THINGSPEAK_API_KEY}&results=1"
        response = requests.get(url, timeout=6)
        if response.status_code == 200:
            data = response.json()
            feeds = data.get("feeds")
            if not feeds:
                return 0.0
            last_entry = feeds[-1]
            for i in range(1, 9):
                v = last_entry.get(f"field{i}")
                if v is not None and str(v).strip() != "":
                    try:
                        return float(v)
                    except:
                        continue
    except Exception as e:
        safe_print("Error getting balance:", e)
    return 0.0


def check_motivation(balance):
    if balance >= TARGET_AMOUNT:
        speak_enqueue(f"Congratulations Aman! You've reached your target of {TARGET_AMOUNT} rupees!")
    elif balance >= 30:
        speak_enqueue("You're very close to your target, Aman! Keep it up!")
    elif balance >= 20:
        speak_enqueue("Great work Aman! You’ve saved over twenty rupees.")
    elif balance >= 10:
        speak_enqueue("Nice work Aman! You’ve reached ten rupees. Keep going strong!")



def generate_daily_graph(deposits, save_path):
    """
    deposits: list of dicts [{'amount':float,'time': 'HH:MM ...'}, ...]
    Saves a PNG graph and returns filepath.
    """
    try:
        if not deposits:
            return None
        # x = index, y = cumulative or per-deposit? We'll plot cumulative for clarity
        xs = []
        ys = []
        cum = 0
        for i, d in enumerate(deposits):
            cum += float(d['amount'])
            xs.append(i+1)
            ys.append(cum)
        plt.figure(figsize=(8,4))
        plt.plot(xs, ys, marker='o')
        plt.title("Daily Savings Progress")
        plt.xlabel("Deposit #")
        plt.ylabel("Cumulative Balance (₹)")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()
        safe_print("Saved graph:", save_path)
        return save_path
    except Exception as e:
        safe_print("generate_daily_graph error:", e)
        return None

def generate_pdf_report(deposits, report_title, save_path, include_graph_path=None):
    """
    Create a simple PDF report using reportlab.
    deposits: list of dicts [{'amount':, 'time':}, ...]
    """
    try:
        c = canvas.Canvas(save_path, pagesize=letter)
        width, height = letter
        margin = 50
        y = height - margin

        c.setFont("Helvetica-Bold", 16)
        c.drawString(margin, y, report_title)
        y -= 30

        c.setFont("Helvetica", 11)
        c.drawString(margin, y, f"Date: {datetime.now().strftime('%d %B %Y')}")
        y -= 25

        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, y, "Deposits:")
        y -= 20

        c.setFont("Helvetica", 11)
        total = 0
        for entry in deposits:
            line = f"₹{entry['amount']}  —  {entry['time']}"
            c.drawString(margin + 10, y, line)
            y -= 18
            total += float(entry['amount'])
            if y < 80:
                c.showPage()
                y = height - margin
        y -= 6
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, y, f"Total Saved Today: ₹{total}")
        y -= 30
        c.setFont("Helvetica", 10)
        final_balance = get_current_balance()
        c.drawString(margin, y, f"Current Total Balance: ₹{final_balance}")

        # optionally insert graph image
        if include_graph_path and os.path.exists(include_graph_path):
            try:
                c.showPage()
                # draw graph centered
                c.drawImage(include_graph_path, margin, height/3, width - 2*margin, height/3)
            except Exception as e:
                safe_print("Error adding graph image to PDF:", e)

        c.save()
        safe_print("PDF saved:", save_path)
        return save_path
    except Exception as e:
        safe_print("generate_pdf_report error:", e)
        return None

# ============== Report sending functions ==============
def send_daily_report(manual=False):
    """
    Generate daily PDF + graph, send via email + telegram.
    manual: if True, speak confirmation to user immediately
    """
    try:
        if not daily_deposits:
            speak_enqueue("No deposits made today yet, Aman.")
            return False

        today_label = datetime.now().strftime("%Y-%m-%d")
        graph_path = os.path.join(GRAPHS_FOLDER, f"daily_graph_{today_label}.png")
        pdf_path = os.path.join(REPORTS_FOLDER, f"Daily_Report_{today_label}.pdf")

        # create graph (cumulative)
        generate_daily_graph(daily_deposits, graph_path)

        # create pdf
        generate_pdf_report(daily_deposits, f"AI Piggy Bank - Daily Report ({today_label})", pdf_path, include_graph_path=graph_path)

        # email subject/body
        subject = f"AI Piggy Bank Daily Report - {today_label}"
        body = f"Hello Aman,\n\nAttached is the daily savings report for {today_label}.\nTotal saved today: ₹{sum(d['amount'] for d in daily_deposits)}.\n\nKeep saving!\n"

        # send email (attachments)
        attachments = [pdf_path, graph_path] if os.path.exists(pdf_path) else ([graph_path] if os.path.exists(graph_path) else None)
        ok = send_email_with_attachments(subject, body, attachments)

        # telegram quick summary + photo (first depositor photo if exists)
        ts = datetime.now().strftime("%I:%M %p on %d %b %Y")
        msg = f"Daily report for {today_label}. Total today: ₹{sum(d['amount'] for d in daily_deposits)}."
        photo = None
        # use last saved photo if any
        img_files = sorted([os.path.join(IMAGES_FOLDER, f) for f in os.listdir(IMAGES_FOLDER)], key=os.path.getmtime) if os.path.exists(IMAGES_FOLDER) else []
        if img_files:
            photo = img_files[-1]
        threading.Thread(target=send_telegram_message, args=(msg, photo), daemon=True).start()

        if manual:
            if ok:
                speak_enqueue("Daily report emailed successfully, Aman.")
            else:
                speak_enqueue("Failed to send daily report, check email settings.")

        return ok
    except Exception as e:
        safe_print("send_daily_report error:", e)
        speak_enqueue("Error generating daily report.")
        return False

def send_monthly_report(manual=False):
    """
    Create summary for the previous month.
    """
    try:
        # Determine previous month range
        today = datetime.now().date()
        first_of_this_month = today.replace(day=1)
        prev_month_last = first_of_this_month - timedelta(days=1)
        prev_month_start = prev_month_last.replace(day=1)
        # Filter deposits that occurred in previous month from monthly_deposits or daily_deposits history
        # For simplicity we will use 'monthly_deposits' list; if absent, we can approximate using 'daily_deposits' saved historically
        # If you want persistent storage across reboots, consider saving to JSON file.
        # Here we'll parse monthly_deposits (if you update it on each deposit)
        entries = [d for d in monthly_deposits if prev_month_start <= datetime.strptime(d['time'], "%I:%M %p on %d %b %Y").date() <= prev_month_last] if monthly_deposits else []

        # fallback: if monthly_deposits empty, we can't build full monthly report — still send summary of daily_deposits if any in this month
        if not entries:
            # try approximate: use daily_deposits that have date in previous month
            entries = []
            # If you want persistent history, save monthly_deposits on each deposit to file.
        # Build PDF + graph from entries
        month_label = prev_month_start.strftime("%Y-%m")
        graph_path = os.path.join(GRAPHS_FOLDER, f"monthly_graph_{month_label}.png")
        pdf_path = os.path.join(REPORTS_FOLDER, f"Monthly_Report_{month_label}.pdf")

        if entries:
            generate_daily_graph(entries, graph_path)
            generate_pdf_report(entries, f"AI Piggy Bank - Monthly Report ({month_label})", pdf_path, include_graph_path=graph_path)

            subject = f"Vaulto Monthly Report - {month_label}"
            body = f"Monthly summary for {month_label}.\nTotal entries: {len(entries)}"
            attachments = [pdf_path, graph_path] if os.path.exists(pdf_path) else None
            ok = send_email_with_attachments(subject, body, attachments)
            threading.Thread(target=send_telegram_message, args=(f"Monthly report {month_label} sent.", None), daemon=True).start()
            if manual:
                if ok:
                    speak_enqueue("Monthly report emailed successfully, Aman.")
                else:
                    speak_enqueue("Failed to send monthly report.")
            return ok
        else:
            speak_enqueue("No data available for previous month.")
            return False
    except Exception as e:
        safe_print("send_monthly_report error:", e)
        speak_enqueue("Error creating monthly report.")
        return False

# ============== Serial parsing & deposit handling ==============
# deposit parsing regexes
deposit_patterns = [
    re.compile(r'^\s*DEPOSIT\s*[:\-]\s*(\d+(?:\.\d+)?)\s*$', re.IGNORECASE),
    re.compile(r'^\s*(\d+(?:\.\d+)?)\s*$'),
    re.compile(r'entered\s*amount.*?(\d+(?:\.\d+)?)', re.IGNORECASE),
    re.compile(r'added\s*amount.*?(\d+(?:\.\d+)?)', re.IGNORECASE),
    re.compile(r'added[:\s]+(\d+(?:\.\d+)?)', re.IGNORECASE)
]
total_patterns = [re.compile(r'total[:\s=]*?(\d+(?:\.\d+)?)', re.IGNORECASE)]

def process_deposit(amount):
    global daily_deposits, monthly_deposits
    try:
        amt = float(amount)
        ts = datetime.now().strftime("%I:%M %p on %d %b %Y")
        with balance_lock:
            daily_deposits.append({"amount": amt, "time": ts})
            monthly_deposits.append({"amount": amt, "time": ts})
        # notify actions
        photo = capture_photo()
        text = f"Aman deposited ₹{amt} at {ts}."
        safe_print(text)
        threading.Thread(target=send_telegram_message, args=(text, photo), daemon=True).start()
        update_thingspeak(sum(d['amount'] for d in monthly_deposits))  # optional: write cumulative or actual balance based on your channel
        speak_enqueue(f"Thank you Aman, ₹{int(amt)} added. Your total today is ₹{int(sum(d['amount'] for d in daily_deposits))}.")
        check_motivation(sum(d['amount'] for d in monthly_deposits))
    except Exception as e:
        safe_print("process_deposit error:", e)

def serial_reader():
    """Continuously read serial lines from ESP32 and handle Added/Total messages.
       Speaks via the TTS queue so it won't interfere with commands."""
    global last_total_reported
    if ser is None:
        safe_print("Serial port not configured. Serial reader not started.")
        return

    while True:
        try:
            if not ser.is_open:
                try:
                    ser.open()
                except Exception:
                    time.sleep(1)
                    continue

            raw = ser.readline().decode(errors='ignore').strip()
            if not raw:
                continue
            safe_print("Received:", raw)

            if "Channel update successful" in raw or "Channel updated" in raw:
                continue
            if "Update error" in raw or "Error" in raw:
                continue

            
            if "Added Amount" in raw:
             
                try:
                    num = int(''.join(filter(str.isdigit, raw)))
                    speak_enqueue(f"User added {num} rupees.")
                 
                    timestamp = datetime.now().strftime("%I:%M %p on %d %b %Y")
                    daily_deposits.append({"amount": num, "time": timestamp})
                except Exception:
                    speak_enqueue(raw)  

            elif raw.startswith("Total"):
     
                try:
                    total_val = int(''.join(filter(str.isdigit, raw)))
                except:
                    try:
                        total_val = int(float(''.join(ch for ch in raw if (ch.isdigit() or ch=='.'))))
                    except:
                        total_val = None

                if total_val is not None:
               
                    if last_total_reported != total_val:
                        last_total_reported = total_val
                        timestamp = datetime.now().strftime("%I:%M %p on %d %b %Y")
                        photo = capture_photo()
                        msg = f"User deposited ₹{num}. Total balance is now ₹{total_val} at {timestamp}."
                        speak_enqueue(f"Your total is now {total_val} rupees, Aman.")
                    
                        threading.Thread(target=send_telegram_message, args=(msg, photo), daemon=True).start()
                        check_motivation(total_val)
                else:
                    speak_enqueue(raw)
            else:
              
            
                speak_enqueue(raw)

        except serial.SerialException:
            safe_print("Serial port temporarily unavailable, retrying...")
            time.sleep(2)
            continue
        except Exception as e:
            safe_print("Serial reader error:", e)
            time.sleep(0.5)

# ----------------------- THINGSPEAK GRAPH -----------------------
def show_graph():
    """Downloads the last N ThingSpeak points and opens a PNG graph."""
    try:
        results = 50
        url = f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/feeds.json?api_key={THINGSPEAK_API_KEY}&results={results}"

        resp = requests.get(url, timeout=8)
        if resp.status_code != 200:
            speak_enqueue("Unable to fetch graph data from ThingSpeak.")
            return
        data = resp.json()
        feeds = data.get("feeds", [])
        times = []
        vals = []
        for f in feeds:
 
            val = None
            for i in range(1, 9):
                v = f.get(f"field{i}")
                if v not in (None, ""):
                    try:
                        val = float(v)
                        break
                    except:
                        val = None
            if val is not None:
                vals.append(val)
                times.append(f.get("created_at"))

        if not vals:
            speak_enqueue("No numeric data found to plot.")
            return

        plt.figure(figsize=(8,4))
        plt.plot(vals)
        plt.title("AI Smart Bank - Recent Balance Graph")
        plt.xlabel("Smart Vualt Graph")
        plt.ylabel("Balance (₹)")
        plt.tight_layout()
        os.makedirs("graphs", exist_ok=True)
        fname = os.path.join("graphs", f"graph_{int(time.time())}.png")
        plt.savefig(fname)
        plt.close()
        safe_print("Graph saved to", fname)
     
        webbrowser.open(f"file://{os.path.abspath(fname)}")
        speak_enqueue("I've opened the graph for you.")
    except Exception as e:
        safe_print("Graph error:", e)
        speak_enqueue("Sorry, I couldn't create the graph.")




def daily_reminder_loop():
    while True:
        now = datetime.now()
        if now.hour == REMINDER_HOUR and now.minute == 0:
            speak_enqueue("Good morning Aman! Don’t forget to deposit today.")
            time.sleep(60)
        time.sleep(10)

def safe_shutdown():
    global tts_worker_running
    tts_worker_running = False
    time.sleep(0.5)
    try:
        if ser and ser.is_open:
            ser.close()
    except:
        pass
    os._exit(0)

if __name__ == "__main__":

    t1 = threading.Thread(target=tts_worker, daemon=True)
    t1.start()

    
    t2 = threading.Thread(target=serial_reader, daemon=True)
    t2.start()


    t3 = threading.Thread(target=wake_word_listener, daemon=True)
    t3.start()

    t4 = threading.Thread(target=daily_reminder_loop, daemon=True)
    t4.start()

  
    bal_now = get_current_balance()
    speak_enqueue(f"Hello Aman! Your AI Smart Bank is ready. You currently have {bal_now} rupees saved. dont forget to save today")
    safe_print("AI Smart Vault Bank is Running...")
    safe_print("Waiting for ESP32 data and wake word...")

 
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        safe_shutdown()




