import os
import time
import threading
import requests
from ..database import SessionLocal
from .. import models
from ..services.payment import hold_payment
from ..services.nearby import find_nearby_spots
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
DEFAULT_LAT = float(os.getenv("DEFAULT_LAT", "41.2995"))
DEFAULT_LON = float(os.getenv("DEFAULT_LON", "69.2401"))


def _send(chat_id: int, text: str, keyboard=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if keyboard:
        data["reply_markup"] = {"inline_keyboard": keyboard}
    try:
        requests.post(f"{API_URL}/sendMessage", json=data, timeout=5)
    except Exception:
        pass


def _handle(text: str, chat_id: int, user_id: int):
    args = text.strip().split()

    if text == "/start":
        _send(chat_id, "Assalomu alaykum! Smart Parking botiga xush kelibsiz.\n\n"
               "/nearby - Yaqin atrofdagi bo'sh joylar\n"
               "/register <tel> <ism> - Ro'yxatdan o'tish\n"
               "/balance - Balans")

    elif text == "/nearby":
        db = SessionLocal()
        try:
            spots = find_nearby_spots(db, DEFAULT_LAT, DEFAULT_LON, radius_km=3.0)
            if not spots:
                _send(chat_id, "Yaqin atrofda bo'sh joy topilmadi.")
                return
            msg = "Yaqin atrofdagi joylar:\n\n"
            keyboard = []
            for s in spots:
                msg += f"📍 {s.address}\n💰 {s.hourly_rate} so'm/soat\n\n"
                keyboard.append([{"text": f"Bron {s.id}", "callback_data": f"book_{s.id}"}])
            _send(chat_id, msg, keyboard)
        finally:
            db.close()

    elif text.startswith("/register"):
        if len(args) < 3:
            _send(chat_id, "/register <telefon> <ism>\nMasalan: /register 998901234567 Alisher")
            return
        phone, name = args[1], " ".join(args[2:])
        db = SessionLocal()
        try:
            if db.query(models.User).filter(models.User.phone_number == phone).first():
                _send(chat_id, "Bu raqam avval ro'yxatdan o'tgan.")
                return
            db.add(models.User(phone_number=phone, full_name=name, role="driver", balance=50000.0))
            db.commit()
            _send(chat_id, f"✅ {name}, ro'yxatdan o'tdingiz! Boshlang'ich balans: 50,000 so'm")
        finally:
            db.close()

    elif text == "/balance":
        db = SessionLocal()
        try:
            user = db.query(models.User).filter(models.User.phone_number == str(user_id)).first()
            if not user:
                _send(chat_id, "Avval /register orqali ro'yxatdan o'ting.")
                return
            _send(chat_id, f"💰 Balansingiz: {user.balance:,.0f} so'm")
        finally:
            db.close()

    elif text.startswith("book_"):
        spot_id = int(text.split("_")[1])
        db = SessionLocal()
        try:
            user = db.query(models.User).filter(models.User.phone_number == str(user_id)).first()
            if not user:
                _send(chat_id, "Avval /register orqali ro'yxatdan o'ting.")
                return
            spot = db.query(models.ParkingSpot).filter(models.ParkingSpot.id == spot_id).first()
            if not spot or spot.is_occupied:
                _send(chat_id, "Bu joy band yoki mavjud emas.")
                return
            total = spot.hourly_rate
            if not hold_payment(db, user.id, total):
                _send(chat_id, "Mablag' yetarli emas.")
                return
            reservation = models.Reservation(
                driver_id=user.id, parking_spot_id=spot.id,
                start_time=datetime.now(timezone.utc),
                end_time=datetime.now(timezone.utc) + timedelta(hours=1),
                total_price=total, status="active",
            )
            spot.is_occupied = True
            db.add(reservation)
            db.commit()
            _send(chat_id, f"✅ {spot.address} bron qilindi!\n1 soat - {total} so'm")
        finally:
            db.close()


def _poll():
    last_id = 0
    while True:
        try:
            r = requests.get(f"{API_URL}/getUpdates", params={
                "offset": last_id + 1, "timeout": 30,
            }, timeout=35)
            data = r.json()
            if not data.get("ok"):
                continue
            for update in data["result"]:
                last_id = update["update_id"]
                msg = update.get("message") or update.get("callback_query", {}).get("message")
                if not msg:
                    continue
                chat_id = msg["chat"]["id"]
                user_id = msg["from"]["id"]
                text = ""

                if "text" in msg:
                    text = msg["text"]
                elif "callback_query" in update:
                    text = update["callback_query"]["data"]
                    cb_id = update["callback_query"]["id"]
                    requests.post(f"{API_URL}/answerCallbackQuery", json={
                        "callback_query_id": cb_id,
                    }, timeout=3)

                if text:
                    _handle(text, chat_id, user_id)
        except Exception as e:
            print(f"[BOT] Poll error: {e}")
            time.sleep(3)


def start_bot_thread():
    if not BOT_TOKEN:
        print("[BOT] Token yo'q. Bot ishga tushmadi.")
        return
    thread = threading.Thread(target=_poll, daemon=True)
    thread.start()
    print("[BOT] Bot polling thread started")
