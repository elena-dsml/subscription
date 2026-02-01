from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.logging_config import logger
from app.models.processed_event import ProcessedEvent
from app.settings import settings
from app.db.session import get_session
from app.kafka.schemas import PaymentEventSchema, RefundEventSchema

from app.models.subscription import Subscription, SubscriptionStatus
from app.services.subscription import SubscriptionService
from app.services.billing_client import BillingClient


async def _already_processed(
    session: AsyncSession,
    event_id: UUID,
) -> bool:
    exists = await session.get(ProcessedEvent, event_id) is not None
    if exists:
        logger.debug("Event %s already processed, skipping.", event_id)
    return exists


async def _mark_processed(
    session: AsyncSession,
    event_id: UUID,
) -> None:
    session.add(ProcessedEvent(id=event_id))
    logger.info("Marked event %s as processed.", event_id)


def _billing_client() -> BillingClient:
    return BillingClient(base_url=settings.bill_api_base_url)


async def handle_payment_event(raw: dict) -> None:
    try:
        event = PaymentEventSchema.model_validate(raw)
        event_id = event.id
        status = event.status
        extra_data = event.extra_data or {}
        subscription_id = extra_data.get("subscription_id")

        logger.info("Handling payment event %s for subscription %s", event_id, subscription_id)

        if not subscription_id:
            logger.warning("Payment event %s has no subscription_id, skipping", event_id)
            return

        async for session in get_session():
            async with session.begin():
                if await _already_processed(session, event_id):
                    return

                if status == "succeeded":
                    service = SubscriptionService(
                        session=session,
                        billing_client=_billing_client(),
                    )
                    await service.activate_from_payment(
                        subscription_id=UUID(subscription_id),
                        payment_id=event_id,
                    )
                    logger.info("Activated subscription %s from payment %s", subscription_id, event_id)

                await _mark_processed(session, event_id)

    except Exception as e:
        logger.exception("Failed to handle payment event: %s", raw)


async def handle_refund_event(raw: dict) -> None:
    try:
        event = RefundEventSchema.model_validate(raw)
        event_id = event.id
        status = event.status
        extra_data = event.extra_data or {}
        subscription_id = extra_data.get("subscription_id")

        logger.info("Handling refund event %s for subscription %s", event_id, subscription_id)

        if not subscription_id:
            logger.warning("Refund event %s has no subscription_id, skipping", event_id)
            return

        async for session in get_session():
            async with session.begin():
                if await _already_processed(session, event_id):
                    return

                if status == "succeeded":
                    subscription = await session.get(Subscription, UUID(subscription_id))
                    if subscription and subscription.status == SubscriptionStatus.REFUND_REQUESTED:
                        subscription.status = SubscriptionStatus.REFUNDED
                        logger.info("Refunded subscription %s from event %s", subscription_id, event_id)

                await _mark_processed(session, event_id)

    except Exception as e:
        logger.exception("Failed to handle refund event: %s", raw)
