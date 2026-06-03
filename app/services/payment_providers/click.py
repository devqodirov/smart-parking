import os
import hashlib
import hmac
import requests
from typing import Optional, Dict, Any
from .base import PaymentProvider


CLICK_MERCHANT_ID = os.getenv("CLICK_MERCHANT_ID", "")
CLICK_SERVICE_ID = os.getenv("CLICK_SERVICE_ID", "")
CLICK_SECRET_KEY = os.getenv("CLICK_SECRET_KEY", "")
CLICK_API_URL = os.getenv("CLICK_API_URL", "https://api.click.uz/v2/merchant")


class ClickProvider(PaymentProvider):
    def _sign(self, params: dict) -> str:
        text = "".join(str(v) for v in params.values()) + CLICK_SECRET_KEY
        return hashlib.md5(text.encode()).hexdigest()

    def _request(self, endpoint: str, data: dict) -> dict:
        url = f"{CLICK_API_URL}/{endpoint}"
        data["merchant_id"] = CLICK_MERCHANT_ID
        data["sign_time"] = None
        data["sign_string"] = self._sign(data)
        try:
            r = requests.post(url, json=data, timeout=10)
            return r.json()
        except Exception as e:
            return {"error": str(e), "status": -1}

    def create_invoice(self, amount: float, description: str, order_id: str, return_url: str = "") -> dict:
        data = {
            "service_id": CLICK_SERVICE_ID,
            "merchant_trans_id": order_id,
            "amount": round(amount),
            "return_url": return_url or "https://t.me/smart_parking_bot",
        }
        return self._request("invoice/create", data)

    def check_invoice(self, invoice_id: str) -> dict:
        data = {"invoice_id": invoice_id}
        return self._request("invoice/status/check", data)

    def cancel_invoice(self, invoice_id: str) -> dict:
        data = {"invoice_id": invoice_id}
        return self._request("invoice/cancel", data)

    def verify_webhook(self, data: dict, headers: dict) -> Optional[Dict[str, Any]]:
        received_sign = data.get("sign_string", "")
        computed_sign = self._sign(data)
        if received_sign != computed_sign:
            return None
        return {
            "transaction_id": data.get("invoice_id"),
            "order_id": data.get("merchant_trans_id"),
            "amount": float(data.get("amount", 0)) / 100,
            "status": "completed" if data.get("status") == 2 else "failed",
            "provider": "click",
        }
