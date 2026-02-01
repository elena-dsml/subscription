from uuid import UUID
from fastapi import APIRouter, Depends
from pydantic import BaseModel, HttpUrl

from app.services.subscription import SubscriptionService
from app.services.billing_client import BillingClient
from app.db.session import get_session
from app.deps.auth import get_current_user_id
from app.models.subscription import Subscription, SubscriptionStatus

from sqlalchemy.ext.asyncio import AsyncSession

from app.settings import settings


router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


def get_subscription_service(
    session: AsyncSession = Depends(get_session),
) -> SubscriptionService:
    return SubscriptionService(
        session=session,
        billing_client=BillingClient(settings.base_url),
    )


class CreateSubscriptionRequest(BaseModel):
    plan_id: UUID
    return_url: HttpUrl


class SubscriptionResponse(BaseModel):
    id: UUID
    plan_id: UUID
    status: SubscriptionStatus

    class Config:
        from_attributes = True


class RefundRequest(BaseModel):
    handler_url: HttpUrl


@router.post(
    "",
    summary="Create subscription and start payment",
)
async def create_subscription(
    body: CreateSubscriptionRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionResponse:
    subscription = await service.create_subscription(
        user_id=user_id,
        plan_id=body.plan_id,
        return_url=str(body.return_url),
    )

    return SubscriptionResponse.model_validate(subscription)


@router.post(
    "/{subscription_id}/cancel",
    summary="Cancel active subscription",
)
async def cancel_subscription(
    subscription_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: SubscriptionService = Depends(get_subscription_service),
) -> None:
    await service.cancel(
        subscription_id=subscription_id,
        user_id=user_id,
    )


@router.post(
    "/{subscription_id}/refund",
    summary="Request refund for subscription",
)
async def refund_subscription(
    subscription_id: UUID,
    body: RefundRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: SubscriptionService = Depends(get_subscription_service),
) -> None:
    await service.request_refund(
        subscription_id=subscription_id,
        user_id=user_id,
        handler_url=str(body.handler_url),
    )


@router.get(
    "",
    summary="List user's subscriptions",
)
async def list_subscriptions(
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
) -> list[SubscriptionResponse]:
    from sqlalchemy import select

    result = await session.execute(
        select(Subscription).where(Subscription.user_id == user_id)
    )

    subscriptions = result.scalars().all()

    return [
        SubscriptionResponse.model_validate(sub)
        for sub in subscriptions
    ]
