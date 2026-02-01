from fastapi import Request
from sqladmin import ModelView
from sqladmin.authentication import AuthenticationBackend

from app.deps.auth import auth_client
from app.models.plan import Plan
from app.models.subscription import Subscription, SubscriptionStatus


class AdminAuth(AuthenticationBackend):

    async def authenticate(self, request: Request) -> bool:
        try:
            payload = await auth_client.authenticate(request)
        except Exception:
            return False

        return payload.get("role") == "superuser"


class PlanAdmin(ModelView, model=Plan):
    name = "Plan"
    name_plural = "Plans"

    column_list = [
        Plan.id,
        Plan.name,
        Plan.amount,
        Plan.currency,
        Plan.period_days,
        Plan.is_active,
    ]

    column_searchable_list = [Plan.name]
    column_filters = [Plan.currency, Plan.is_active]

    form_excluded_columns = [Plan.id]

    can_create = True
    can_edit = True
    can_delete = False
    can_view_details = True


class SubscriptionAdmin(ModelView, model=Subscription):
    name = "Subscription"
    name_plural = "Subscriptions"

    column_list = [
        Subscription.id,
        Subscription.user_id,
        Subscription.plan_id,
        Subscription.status,
        Subscription.created_at,
    ]

    column_filters = [Subscription.status, Subscription.plan_id]
    column_sortable_list = [Subscription.created_at]

    can_create = False
    can_delete = False

    async def on_model_change(self, data, model, is_created):
        if model.status == SubscriptionStatus.REFUNDED and not model.payment_id:
            raise ValueError("Refunded subscription must have payment")
