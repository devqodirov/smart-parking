import os
import base64
import requests
from typing import Optional, Dict, Any
from .base import PaymentProvider


PAYME_MERCHANT_ID = os.getenv("PAYME_MERCHANT_ID", "")
PAYME_KEY = os.getenv("PAYME_KEY", "")
PAYME_API_URL = os.getenv("PAYME_API_URL", "https://checkout.paycom.uz/api")


class PaymeProvider(PaymentProvider):
    def _auth_header(self) -> str:
        creds = f"{PAYME_MERCHANT_ID}:{PAYME_KEY}"
        return base64.b64encode(creds.encode()).decode()

    def _rpc(self, method: str, params: dict) -> dict:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }
        headers = {
            "X-Auth": self._auth_header(),
            "Content-Type": "application/json",
        }
        try:
            r = requests.post(PAYME_API_URL, json=payload, headers=headers, timeout=10)
            return r.json()
        except Exception as e:
            return {"error": {"message": str(e)}, "result": None}

    def create_invoice(self, amount: float, description: str, order_id: str, return_url: str = "") -> dict:
        result = self._rpc("CreateTransaction", {
            "id": order_id,
            "time": int(__import__("time").time() * 1000),
            "amount": int(round(amount * 100)),
            "account": {"order_id": order_id},
        })
        return result

    def check_invoice(self, invoice_id: str) -> dict:
        return self._rpc("CheckTransaction", {"id": invoice_id})

    def cancel_invoice(self, invoice_id: str) -> dict:
        return self._rpc("CancelTransaction", {
            "id": invoice_id,
            "reason": 1,
        })

    def verify_webhook(self, data: dict, headers: dict) -> Optional[Dict[str, Any]]:
        method = data.get("method", "")
        if method != "PerformTransaction":
            return {"action": "continue", "data": data}
        params = data.get("params", {})
        return {
            "transaction_id": params.get("id"),
            "order_id": params.get("account", {}).get("order_id"),
            "amount": float(params.get("amount", 0)) / 100,
            "status": "completed",
            "provider": "payme",
        }
