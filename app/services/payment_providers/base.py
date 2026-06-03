from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class PaymentProvider(ABC):
    @abstractmethod
    def create_invoice(self, amount: float, description: str, order_id: str, return_url: str = "") -> dict:
        ...

    @abstractmethod
    def check_invoice(self, invoice_id: str) -> dict:
        ...

    @abstractmethod
    def cancel_invoice(self, invoice_id: str) -> dict:
        ...

    @abstractmethod
    def verify_webhook(self, data: dict, headers: dict) -> Optional[Dict[str, Any]]:
        ...
