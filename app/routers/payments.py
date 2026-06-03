from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from .. import models, schemas
from ..services.payment_gateway import payment_gateway

router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])


@router.get("/providers")
def get_providers():
    return {
        "available": payment_gateway.available_providers,
        "default": payment_gateway.available_providers[0] if payment_gateway.available_providers else None,
    }


@router.post("/deposit")
def create_deposit(
    user_id: int,
    amount: float,
    provider: Optional[str] = None,
    db: Session = Depends(get_db),
):
    if not payment_gateway.available_providers:
        raise HTTPException(status_code=400, detail="Hech qanday to'lov tizimi ulanmagan. .env ni tekshiring.")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

    if amount < 1000:
        raise HTTPException(status_code=400, detail="Minimal summa 1000 so'm")

    order_id = f"DEPOSIT_{user_id}_{int(__import__('time').time())}"
    description = f"Smart Parking - {user.full_name} ({user.phone_number}) - {amount} so'm"

    result = payment_gateway.create_invoice(amount, description, order_id, provider=provider)

    if "error" in result or "error_code" in result:
        raise HTTPException(status_code=502, detail=f"To'lov tizimi xatosi: {result.get('error', result)}")

    return {
        "order_id": order_id,
        "amount": amount,
        "provider": provider or payment_gateway.available_providers[0],
        "payment_url": result.get("url") or result.get("payment_url") or result.get("result", {}).get("url", ""),
        "invoice_id": result.get("invoice_id") or result.get("result", {}).get("id", ""),
    }


@router.post("/webhook/{provider}")
async def payment_webhook(provider: str, request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Noto'g'ri ma'lumot formati")

    headers = dict(request.headers)
    result = payment_gateway.verify_webhook(provider, data, headers)

    if result is None:
        raise HTTPException(status_code=400, detail="Imzo noto'g'ri yoki to'lov rad etildi")

    if result.get("status") == "completed":
        order_id = result.get("order_id", "")
        amount = result.get("amount", 0)

        if order_id.startswith("DEPOSIT_"):
            parts = order_id.split("_")
            if len(parts) >= 2:
                try:
                    user_id = int(parts[1])
                    user = db.query(models.User).filter(models.User.id == user_id).first()
                    if user:
                        user.balance += amount
                        db.commit()
                except (ValueError, IndexError):
                    pass

    return {"status": "ok", "result": result}


@router.get("/history/{user_id}")
def payment_history(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    return {
        "user_id": user_id,
        "balance": user.balance,
        "message": "To'lov tarixi keyingi versiyada qo'shiladi",
    }
