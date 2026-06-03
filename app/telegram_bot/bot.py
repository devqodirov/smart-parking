import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from ..database import SessionLocal, is_postgres
from .. import models
from ..services.payment import hold_payment
from ..services.nearby import find_nearby_spots
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
APP_URL = os.getenv("APP_URL", "https://smart-parking.fly.dev")
DEFAULT_LAT = float(os.getenv("DEFAULT_LAT", "41.2995"))
DEFAULT_LON = float(os.getenv("DEFAULT_LON", "69.2401"))

_bot_app: Application = None


async def _start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Assalomu alaykum! Smart Parking botiga xush kelibsiz.\n\n"
        "/nearby - Yaqin atrofdagi bo'sh joylarni ko'rish\n"
        "/book <id> - Joyni bron qilish\n"
        "/balance - Balansni ko'rish\n"
        "/register <telefon> <ism> - Ro'yxatdan o'tish"
    )


async def _nearby(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = SessionLocal()
    try:
        spots = find_nearby_spots(db, DEFAULT_LAT, DEFAULT_LON, radius_km=3.0)
        if not spots:
            await update.message.reply_text("Yaqin atrofda bo'sh joy topilmadi.")
            return
        msg = "Yaqin atrofdagi bo'sh joylar:\n\n"
        buttons = []
        for spot in spots:
            msg += f"📍 {spot.address}\n💰 {spot.hourly_rate} so'm/soat\n🆔 ID: {spot.id}\n\n"
            buttons.append([InlineKeyboardButton(f"Bron {spot.id}", callback_data=f"book_{spot.id}")])
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(buttons))
    finally:
        db.close()


async def _book_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    spot_id = int(query.data.split("_")[1])
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.phone_number == str(update.effective_user.id)).first()
        if not user:
            await query.edit_message_text("Avval /register orqali ro'yxatdan o'ting.")
            return
        spot = db.query(models.ParkingSpot).filter(models.ParkingSpot.id == spot_id).first()
        if not spot or spot.is_occupied:
            await query.edit_message_text("Bu joy band yoki mavjud emas.")
            return
        hours, total = 1, spot.hourly_rate
        if not hold_payment(db, user.id, total):
            await query.edit_message_text("Mablag' yetarli emas.")
            return
        reservation = models.Reservation(
            driver_id=user.id, parking_spot_id=spot.id,
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc) + timedelta(hours=hours),
            total_price=total, status="active",
        )
        spot.is_occupied = True
        db.add(reservation)
        db.commit()
        await query.edit_message_text(f"✅ {spot.address} bron qilindi!\n{hours} soat - {total} so'm")
    finally:
        db.close()


async def _register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("/register <telefon> <ism>")
        return
    phone, name = args[0], " ".join(args[1:])
    db = SessionLocal()
    try:
        if db.query(models.User).filter(models.User.phone_number == phone).first():
            await update.message.reply_text("Bu raqam avval ro'yxatdan o'tgan.")
            return
        db.add(models.User(phone_number=phone, full_name=name, role="driver", balance=50000.0))
        db.commit()
        await update.message.reply_text(f"✅ {name}, ro'yxatdan o'tdingiz! Boshlang'ich balans: 50,000 so'm")
    finally:
        db.close()


async def _balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.phone_number == str(update.effective_user.id)).first()
        if not user:
            await update.message.reply_text("Avval /register orqali ro'yxatdan o'ting.")
            return
        await update.message.reply_text(f"💰 Balansingiz: {user.balance:,.0f} so'm")
    finally:
        db.close()


def get_bot_app() -> Application:
    global _bot_app
    if _bot_app is not None:
        return _bot_app
    if not BOT_TOKEN:
        return None
    _bot_app = Application.builder().token(BOT_TOKEN).build()
    _bot_app.add_handler(CommandHandler("start", _start))
    _bot_app.add_handler(CommandHandler("nearby", _nearby))
    _bot_app.add_handler(CommandHandler("register", _register))
    _bot_app.add_handler(CommandHandler("balance", _balance))
    _bot_app.add_handler(CallbackQueryHandler(_book_callback, pattern="^book_"))
    return _bot_app


async def setup_webhook():
    app = get_bot_app()
    if not app:
        return
    webhook_url = f"{APP_URL}/telegram-webhook"
    await app.bot.set_webhook(url=webhook_url)
    print(f"[BOT] Webhook set: {webhook_url}")


async def handle_webhook(data: dict):
    app = get_bot_app()
    if not app:
        return {"ok": False, "error": "Bot not configured"}
    update = Update.de_json(data, app.bot)
    await app.process_update(update)
    return {"ok": True}
