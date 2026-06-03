import os
from typing import Optional
from .payment_providers.click import ClickProvider
from .payment_providers.payme import PaymeProvider
from .payment_providers.uzum import UzumProvider
from .payment_providers.base import PaymentProvider


class PaymentGateway:
    def __init__(self):
        self._providers: dict[str, PaymentProvider] = {}
        self._default: str = ""

        if os.getenv("CLICK_MERCHANT_ID"):
            self._providers["click"] = ClickProvider()
            self._default = "click"

        if os.getenv("PAYME_MERCHANT_ID"):
            self._providers["payme"] = PaymeProvider()
            self._default = self._default or "payme"

        if os.getenv("UZUM_MERCHANT_ID"):
            self._providers["uzum"] = UzumProvider()
            self._default = self._default or "uzum"

    def _get(self, provider: Optional[str] = None) -> PaymentProvider:
        name = provider or self._default
        if not name:
            raise ValueError("Hech qanday to'lov tizimi sozlanmagan. .env faylini tekshiring.")
        p = self._providers.get(name)
        if not p:
            raise ValueError(f"'{name}' to'lov tizimi topilmadi. Mavjud: {list(self._providers.keys())}")
        return p

    def create_invoice(self, amount: float, description: str, order_id: str, provider: Optional[str] = None, return_url: str = "") -> dict:
        return self._get(provider).create_invoice(amount, description, order_id, return_url)

    def check_invoice(self, invoice_id: str, provider: Optional[str] = None) -> dict:
        return self._get(provider).check_invoice(invoice_id)

    def cancel_invoice(self, invoice_id: str, provider: Optional[str] = None) -> dict:
        return self._get(provider).cancel_invoice(invoice_id)

    def verify_webhook(self, provider: str, data: dict, headers: dict) -> Optional[dict]:
        p = self._providers.get(provider)
        if not p:
            return None
        return p.verify_webhook(data, headers)

    @property
    def available_providers(self) -> list[str]:
        return list(self._providers.keys())


payment_gateway = PaymentGateway()
