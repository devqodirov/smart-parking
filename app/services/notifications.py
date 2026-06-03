import os
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")


def send_telegram(chat_id: str, text: str):
    if not TELEGRAM_BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=5)
    except Exception:
        pass


def notify_low_battery(spot_id: int, level: float):
    msg = f"Datchik No.{spot_id} batareyasi {level:.0f}%. Almashtirish kerak!"
    send_telegram(ADMIN_CHAT_ID, msg)
    print(f"[BATTERY] {msg}")


def notify_booking_reminder(chat_id: str, spot_address: str, minutes_left: int):
    msg = f"Eslatma: {spot_address} joyidagi broningiz {minutes_left} daqiqadan so'ng tugaydi."
    send_telegram(chat_id, msg)
