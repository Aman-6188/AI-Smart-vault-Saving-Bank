----AI SMART VAULT/SAVING BANK----

VAULTO – AI Smart Vault / Intelligent Saving Bank
A Next-Generation AI + IoT Powered Smart Savings System


OVERVIEW:-

VAULTO is an AI-powered Smart Vault/Piggy Bank designed to revolutionize traditional saving methods. It combines physical money storage with digital tracking, AI assistance, IoT features, security monitoring, and automated analytics.
Unlike ordinary piggy banks, VAULTO tracks deposits automatically, captures depositor photos, generates daily reports, predicts financial habits, and interacts through a voice-enabled AI assistant.


System Architecture:-

1. Hardware Layer (IoT + Sensors)

ESP32 microcontroller

Load/weight sensors for deposit detection

IR sensors for object recognition

Servo motor for vault lock/unlock

LCD Display for user messages

Microphone for wake-word detection

Speaker / DF-Player module for voice responses

Camera module for depositor image capture

Tilt/Motion sensor for theft detection


2. Software / AI Layer (Python Desktop System)

Wake-word engine (“Jarvis”)

Command engine for “Vaulto”

JSON/SQLite-based transaction logging

Daily/Weekly/Monthly analytics

Cloud integration via ThingSpeak

Email report generator (PDF + graphs)

Telegram remote control + alerts

AI-based trend prediction & motivational guidance

How VAULTO Works

User activates the system using the wake word: “Jarvis”

Commands such as:

“Open Vaulto”

“Add money”

“Show today’s report”

“How much have I saved?”

Vault opens using servo lock.

Weight sensors detect the deposited amount.

System updates the balance and logs it with:

Date & time

Value

Depositor image

Python AI module generates:

Graphs

Savings predictions

Motivation feedback

Camera capture ensures deposit transparency.

Tilt detection sends instant Telegram alerts during theft attempts.

Cloud platform shows real-time savings charts.

Daily PDF report sent automatically via email.


KEY FEATURES:-

🔹 Intelligence

AI-powered voice assistant

Predicts savings habits

Motivational voice output

🔹 Security

Servo lock system

Camera-based depositor capture

Motion/tilt theft detection

Telegram emergency alerts

🔹 Automation

Hands-free wake-word activation

Daily PDF + graph report

Cloud monitoring in real time

🔹 Finance Tracking

Automatic deposit logging

Daily/weekly/monthly insights

Real-time savings graphs


TECHNOLOGIES USED:-


ESP32

IR Sensor

Load Cell + HX711

Servo Motor

LCD Display

DF Player Mini

Camera module

Software

Python

Edge-TTS

ThingSpeak

Matplotlib

OpenCV

Telegram API

SQLite / JSON

E-mail 

Project Structure 
Vaulto-AI-Smart-Vault
│
├── hardware/
│   ├── esp32_code/
│   ├── circuit_diagram.png
│
├── software/
│   ├── main.py
│   ├── wake_word/
│   ├── ai_engine/
│   ├── database cloud/
│   ├── reports/
│
├── images/
│   └── prototype.jpg
│
├── README.md

PROTOTYPE:-

The current prototype includes:

LED display

Keypad

Camera

LCD

PLay back module

Servo lock mechanism

Custom-designed external body


