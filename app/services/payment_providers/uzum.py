import os
import requests
from typing import Optional, Dict, Any
from .base import PaymentProvider


UZUM_MERCHANT_ID = os.getenv("UZUM_MERCHANT_ID", "")
UZUM_SECRET_KEY = os.getenv("UZUM_SECRET_KEY", "")
UZUM_API_URL = os.getenv("UZUM_API_URL", "https://api.uzumbank.uz/v2")


class UzumProvider(PaymentProvider):
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {UZUM_SECRET_KEY}",
            "Content-Type": "application/json",
        }

    def _request(self, endpoint: str, data: dict) -> dict:
        url = f"{UZUM_API_URL}/{endpoint}"
        try:
            r = requests.post(url, json=data, headers=self._headers(), timeout=10)
            return r.json()
        except Exception as e:
            return {"error": str(e), "status": -1}

    def create_invoice(self, amount: float, description: str, order_id: str, return_url: str = "") -> dict:
        data = {
            "service_id": UZUM_MERCHANT_ID,
            "transaction_id": order_id,
            "amount": int(round(amount * 100)),
            "description": description,
            "callback_url": "https://smart-parking.uz/api/v1/payments/webhook/uzum",
            "return_url": return_url or "https://t.me/smart_parking_bot",
        }
        return self._request("payment/create", data)

    def check_invoice(self, invoice_id: str) -> dict:
        return self._request(f"payment/status/{invoice_id}", {})

    def cancel_invoice(self, invoice_id: str) -> dict:
        return self._request(f"payment/cancel/{invoice_id}", {})

    def verify_webhook(self, data: dict, headers: dict) -> Optional[Dict[str, Any]]:
        status = data.get("status")
        if status != "completed":
            return None
        return {
            "transaction_id": data.get("transaction_id"),
            "order_id": data.get("transaction_id"),
            "amount": float(data.get("amount", 0)) / 100,
            "status": "completed",
            "provider": "uzum",
        }
