from decimal import Decimal
from uuid import UUID
import aiohttp

from app.logging_config import logger


class BillingClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def create_payment(
        self,
        *,
        user_id: UUID,
        amount: Decimal,
        currency: str,
        return_url: str,
        extra_data: dict | None = None,
        handler_url: str | None = None,
    ) -> None:
        payload = {
            "user_id": str(user_id),
            "amount": str(amount),
            "currency": currency,
            "return_url": return_url,
        }
        if extra_data:
            payload["extra_data"] = extra_data
        if handler_url:
            payload["handler_url"] = handler_url

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/v1/payment",
                    json=payload,
                ) as resp:
                    resp.raise_for_status()
            logger.info(
                "Created payment for user_id=%s, amount=%s %s, return_url=%s",
                user_id, amount, currency, return_url
            )
        except Exception as e:
            logger.exception(
                "Failed to create payment for user_id=%s: %s", user_id, e
            )
            raise

    async def create_refund(
        self,
        *,
        payment_id: UUID,
        amount: Decimal,
        currency: str,
        extra_data: dict | None = None,
        handler_url: str | None = None,
    ) -> None:
        payload = {
            "amount": str(amount),
            "currency": currency,
        }
        if extra_data:
            payload["extra_data"] = extra_data
        if handler_url:
            payload["handler_url"] = handler_url

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/v1/payment/{payment_id}/refund",
                    json=payload,
                ) as resp:
                    resp.raise_for_status()
            logger.info(
                "Created refund for payment_id=%s, amount=%s %s",
                payment_id, amount, currency
            )
        except Exception as e:
            logger.exception(
                "Failed to create refund for payment_id=%s: %s", payment_id, e
            )
            raise
