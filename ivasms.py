
import websocket
import threading
import time
import json
import requests
from datetime import datetime
import html
import os
from flask import Flask, Response

# -------------------- CONFIG --------------------

WS_URL = "wss://ivasms.com:2087/socket.io/?token=eyJpdiI6IkNOejdzQVdEK0pmbkh0VlIrN28wdWc9PSIsInZhbHVlIjoiYUUyNnYwc2ttL1NGOGFTbmNyZVF1NUx4MnUvaFRjNzRyMlBmYk9yendoYWlzMUtBazVZUGJzem5qelRmc0RQaVljZ2lwRU9Nb1hPODVhVkswREcydUVyT2l2NHBROEtYK0tYSW81ck1KZGpmSVlVRU9tSG5xL0dDQU0vVmUzbU1uZ2VKanpRZUplWXV1Tk1kUGpST0dEbS9iU1UyZ0xYSUJVc3J6NkRxTk1IZEE3Wm0yYzkwNzZQaFN2cGZvSUNFRmREQnpGZ2ladG5oTStZWUs1UGd3SE40anU3d3pIdElaeWJJemFxenhpTXh2dXpuVjNjRWRaUDRpMElJUVNqSG5YSjBySW5IT2JmZmtMSThQY0hYTDR3aXlLaW5pQW51Zm9rTkNtTGZRRWlIZGszdGpKUG5jZEhEL1pwOGFxQ2RiTm44dlJRVmhuaDNrS0FNL1U4eHdvdHplWDNscHBUZ0xtSXU0cm1TdjR5L0pwT3VPQVFnQk03ZHp2aVduUklUWDBkSWF4K0Q3c01hZ01aYzROVHUvWUFxMHFFY1NtdHpBZURYK1BUK3JSK2NVUlVGb0I1bXo3L1JJK05GRUJxeFpDMTFFSUFKQ2ZjVjYrSTZXSzNmYVVocGNtSkhLaXZNQnJ1ekhSS1dkNzNEeC9GcWZKZVU0aGJ2QVFMWDRXY3BKV25BVXZqdklwN2RCV1ZqYWxmWXpBPT0iLCJtYWMiOiI4NDYyNzFiNTBiYmUyNDFlZThlNGFlZjYwMDA3MGY3OWQ5ZWM5NzJkMDBjNzE3YTQ3YTk3OTVhY2M0NWYxZWMxIiwidGFnIjoiIn0%3D&user=39847ce326f975d2c33a858c72fae10c&EIO=4&transport=websocket"  # replace this

AUTH_MESSAGE = '42/livesms,["39847ce326f975d2c33a858c72fae10c"]'  # ⚠️ YOUR LIVE TOKEN
PING_INTERVAL = 25
start_pinging = False

BOT_TOKEN = "8239716610:AAF8KwyXHH-aMMJzSzi6i3CuykwQzkZlKn8"
GROUP_ID = "-1002786792728"
CHANNEL_URL = "https://t.me/ws_unlimited"
DEV_URL = "https://t.me/misss_hania"

# -------------------- TELEGRAM --------------------

def send_to_telegram(text):
    buttons = {
        "inline_keyboard": [
            [
                {"text": "📢 Channel", "url": CHANNEL_URL},
                {"text": "👨‍💻 Developer", "url": DEV_URL}
            ]
    ]
    }

    payload = {
        "chat_id": GROUP_ID,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": json.dumps(buttons)
    }

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data=payload
        )
        if response.status_code != 200:
            print("⚠️ Telegram Error:", response.text)
    except Exception as e:
        print("❌ Telegram Send Failed:", e)

# -------------------- FUNCTIONS --------------------

def send_ping(ws):
    global start_pinging
    while ws.keep_running:
        if start_pinging:
            try:
                ws.send("3")
                print("📡 Ping sent (2)")
            except Exception as e:
                print("❌ Failed to send ping:", e)
                break
        time.sleep(PING_INTERVAL)

def on_open(ws):
    global start_pinging
    start_pinging = False
    print("✅ WebSocket connected")

    time.sleep(0.5)
    ws.send("40/livesms")
    print("➡️ Sent: 40/livesms")

    time.sleep(0.5)
    ws.send(AUTH_MESSAGE)
    print("🔐 Sent auth token")

    threading.Thread(target=send_ping, args=(ws,), daemon=True).start()

def on_message(ws, message):
    global start_pinging
    if message == "3":
        print("✅ Pong received")
    elif message.startswith("40/livesms"):
        print("✅ Namespace joined — starting ping")
        start_pinging = True
    elif message.startswith("42/livesms,"):
        try:
            payload = message[len("42/livesms,"):]
            data = json.loads(payload)

            if isinstance(data, list) and len(data) > 1 and isinstance(data[1], dict):
                sms = data[1]
                raw_msg = sms.get("message", "")
                recipient = sms.get("recipient", "Unknown")
                country = sms.get("country_iso", "??").upper()

                import re
                otp_match = re.search(r'\b\d{3}[- ]?\d{3}\b|\b\d{6}\b', raw_msg)
                otp = otp_match.group(0) if otp_match else "N/A"

                formatted_number = recipient[:-4].replace(recipient[:-4], '⁕' * (len(recipient[:-4]))) + recipient[-4:]
                now = datetime.now().strftime("%H:%M:%S")
                service = "WhatsApp" if "whatsapp" in raw_msg.lower() else "Unknown"

                telegram_msg = (
                    f"🔔 <b>OTP Received</b>\n"
                    f"🔑 <b>OTP</b>: <code>{otp}</code>\n"
                    f"🕒 <b>Time</b>: {now}\n"
                    f"⚙️ <b>Service</b>: {service}\n"
                    f"☎️ <b>Number</b>: {recipient[:5]}{formatted_number}\n\n"
                    f"{html.escape(raw_msg)}"
                )
                send_to_telegram(telegram_msg)

            else:
                print("⚠️ Unexpected data format:", data)

        except Exception as e:
            print("❌ Error parsing message:", e)
            print("Raw message:", message)

def on_error(ws, error):
    print("❌ WebSocket error:", error)

def on_close(ws, code, msg):
    global start_pinging
    start_pinging = False
    print("🔌 WebSocket closed. Reconnecting in 1s...")
    time.sleep(1)
    start_ws_thread()  # Reconnect automatically

def connect():
    print("🔄 Connecting to IVASMS WebSocket...")
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Origin": "https://ivasms.com",
        "Referer": "https://ivasms.com/",
        "Host": "ivasms.com"
    }

    ws = websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        header=[f"{k}: {v}" for k, v in headers.items()]
    )

    ws.run_forever()

def start_ws_thread():
    t = threading.Thread(target=connect, daemon=True)
    t.start()

# -------------------- FLASK WEB SERVICE --------------------

app = Flask(__name__)

@app.route("/")
def root():
    return Response("Service is running", status=200)

@app.route("/health")
def health():
    return Response("OK", status=200)

# -------------------- START --------------------

if __name__ == "__main__":
    start_ws_thread()  # Start the WebSocket in background
    port = int(os.environ.get("PORT", 8080))  # Use PORT env variable if provided
    app.run(host="0.0.0.0", port=port, threaded=True)
