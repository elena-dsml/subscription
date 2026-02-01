from uuid import UUID
from typing import Literal, Optional
from pydantic import BaseModel


class PaymentEventSchema(BaseModel):
    id: UUID
    status: Literal["succeeded", "cancelled"]
    external_cancellation_reason: Optional[str] = None
    extra_data: dict | None = None


class RefundEventSchema(BaseModel):
    id: UUID
    status: Literal["succeeded", "cancelled"]
    external_cancellation_reason: Optional[str] = None
    extra_data: dict | None = None
