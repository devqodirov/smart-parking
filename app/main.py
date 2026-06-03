import os
from fastapi import FastAPI, Request
from .database import engine, Base, setup_postgis
from .routers import parking, booking, users, admin, payments
from .services.redis_cache import redis_cache
from .telegram_bot.bot import setup_webhook, handle_webhook, get_bot_app

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


@app.on_event("startup")
async def startup():
    if os.getenv("TELEGRAM_BOT_TOKEN"):
        await setup_webhook()


@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    return await handle_webhook(data)


@app.get("/")
def home():
    return {"status": "Running", "version": "1.2.0"}


@app.get("/health")
def health():
    return {"status": "healthy", "database": "connected", "redis": redis_cache._enabled}
