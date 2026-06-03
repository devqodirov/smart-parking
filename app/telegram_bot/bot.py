import os
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from ..database import SessionLocal
from .. import models
from ..services.payment import hold_payment
from ..services.nearby import find_nearby_spots
from datetime import datetime, timezone, timedelta

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
DEFAULT_LAT = float(os.getenv("DEFAULT_LAT", "41.2995"))
DEFAULT_LON = float(os.getenv("DEFAULT_LON", "69.2401"))


async def _start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Assalomu alaykum! Smart Parking botiga xush kelibsiz.\n\n"
        "/nearby - Yaqin atrofdagi bo'sh joylarni ko'rish\n"
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
        msg = "Yaqin atrofdagi bo'sh joylar:"
        buttons = []
        for spot in spots:
            msg += f"📍 {spot.address}💰 {spot.hourly_rate} so'm/soat\n\n"
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


def run_bot():
    if not BOT_TOKEN:
        print("[BOT] Token yo'q. Bot ishga tushmadi.")
        return
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", _start))
    app.add_handler(CommandHandler("nearby", _nearby))
    app.add_handler(CommandHandler("register", _register))
    app.add_handler(CommandHandler("balance", _balance))
    app.add_handler(CallbackQueryHandler(_book_callback, pattern="^book_"))
    print("[BOT] Telegram bot polling...")
    app.run_polling()


def start_bot_thread():
    thread = threading.Thread(target=run_bot, daemon=True)
    thread.start()
    print("[BOT] Bot thread started")
