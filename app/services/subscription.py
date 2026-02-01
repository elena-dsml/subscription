from uuid import UUID
from fastapi import HTTPException

from app.logging_config import logger
from app.models.subscription import Subscription, SubscriptionStatus
from app.services.billing_client import BillingClient
from app.models.plan import Plan


class SubscriptionService:
    def __init__(self, session, billing_client: BillingClient):
        self.session = session
        self.billing = billing_client

    async def create_subscription(
        self,
        user_id: UUID,
        plan_id: UUID,
        return_url: str,
    ) -> Subscription:
        plan = await self.session.get(Plan, plan_id)
        if not plan or not plan.is_active:
            logger.warning("Attempted to subscribe to unavailable plan_id=%s by user_id=%s", plan_id, user_id)
            raise HTTPException(404, "Plan not available")

        subscription = Subscription(
            user_id=user_id,
            plan_id=plan.id,
            status=SubscriptionStatus.PENDING_PAYMENT,
        )
        self.session.add(subscription)
        await self.session.flush()

        try:
            await self.billing.create_payment(
                user_id=user_id,
                amount=plan.amount,
                currency=plan.currency,
                return_url=return_url,
                extra_data={
                    "subscription_id": str(subscription.id),
                    "plan_id": str(plan.id),
                },
            )
            logger.info(
                "Created subscription %s for user_id=%s, plan_id=%s, amount=%s %s",
                subscription.id, user_id, plan.id, plan.amount, plan.currency
            )
        except Exception as e:
            logger.exception(
                "Failed to create payment for subscription %s (user_id=%s, plan_id=%s): %s",
                subscription.id, user_id, plan.id, e
            )
            raise

        return subscription

    async def activate_from_payment(
        self,
        subscription_id: UUID,
        payment_id: UUID,
    ) -> None:
        subscription = await self.session.get(Subscription, subscription_id)
        if not subscription:
            logger.warning("Subscription %s not found for activation", subscription_id)
            return

        if subscription.status != SubscriptionStatus.PENDING_PAYMENT:
            logger.info("Subscription %s activation skipped (status=%s)", subscription_id, subscription.status)
            return

        subscription.status = SubscriptionStatus.ACTIVE
        subscription.payment_id = payment_id
        logger.info(
            "Activated subscription %s from payment %s", subscription_id, payment_id
        )

    async def cancel(self, subscription_id: UUID, user_id: UUID) -> None:
        subscription = await self.session.get(Subscription, subscription_id)
        if not subscription or subscription.user_id != user_id:
            logger.warning("Cancel failed: subscription %s not found for user_id=%s", subscription_id, user_id)
            raise HTTPException(status_code=404)

        if subscription.status != SubscriptionStatus.ACTIVE:
            logger.warning("Cancel failed: subscription %s status=%s", subscription_id, subscription.status)
            raise HTTPException(status_code=409, detail="Cannot cancel")

        subscription.status = SubscriptionStatus.CANCELLED
        logger.info("Cancelled subscription %s for user_id=%s", subscription_id, user_id)

    async def request_refund(
        self,
        subscription_id: UUID,
        user_id: UUID,
        handler_url: str,
    ) -> None:
        subscription = await self.session.get(Subscription, subscription_id)
        if not subscription or subscription.user_id != user_id:
            logger.warning("Refund failed: subscription %s not found for user_id=%s", subscription_id, user_id)
            raise HTTPException(status_code=404)

        if subscription.status not in {
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.CANCELLED,
        }:
            logger.warning("Refund not allowed: subscription %s status=%s", subscription_id, subscription.status)
            raise HTTPException(status_code=409, detail="Refund not allowed")

        if not subscription.payment_id:
            logger.warning("Refund not allowed: subscription %s payment not completed", subscription_id)
            raise HTTPException(status_code=409, detail="Payment not completed")

        plan = await self.session.get(Plan, subscription.plan_id)
        if not plan:
            logger.error("Refund failed: plan %s not found for subscription %s", subscription.plan_id, subscription_id)
            raise HTTPException(status_code=404, detail="Plan not found")

        try:
            await self.billing.create_refund(
                payment_id=subscription.payment_id,
                amount=plan.amount,
                currency=plan.currency,
                handler_url=handler_url,
                extra_data={"subscription_id": str(subscription.id)},
            )
            subscription.status = SubscriptionStatus.REFUND_REQUESTED
            logger.info(
                "Refund requested for subscription %s (payment_id=%s, amount=%s %s)",
                subscription_id, subscription.payment_id, plan.amount, plan.currency
            )
        except Exception as e:
            logger.exception(
                "Failed to request refund for subscription %s (payment_id=%s): %s",
                subscription_id, subscription.payment_id, e
            )
            raise
