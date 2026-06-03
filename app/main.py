import os
from fastapi import FastAPI
from .database import engine, Base, setup_postgis
from .routers import parking, booking, users, admin, payments
from .services.redis_cache import redis_cache
from .telegram_bot.bot import start_bot_thread

Base.metadata.create_all(bind=engine)
setup_postgis()

app = FastAPI(
    title="Smart Parking API",
    description="Smart Parking - O'zbekiston uchun aqlli avtoturargoh tizimi",
    version="1.2.0",
)

app.include_router(parking.router)
app.include_router(booking.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(payments.router)

redis_host = os.getenv("REDIS_HOST", "localhost")
redis_cache.init(host=redis_host)

if os.getenv("TELEGRAM_BOT_TOKEN"):
    start_bot_thread()


@app.get("/")
def home():
    return {"status": "Running", "version": "1.2.0"}


@app.get("/health")
def health():
    return {"status": "healthy", "database": "connected", "redis": redis_cache._enabled}
