import stripe
from django.conf import settings
from ..models import Plan

stripe.api_key = settings.STRIPE_SECRET_KEY
def create_checkout_session(user, package, billing=None):
    if billing:
        plan = Plan.objects.filter(name=package, interval=billing).first()
    else:
        plan = Plan.objects.filter(name=package).order_by("interval").first()

    if not plan or not plan.stripe_price_id:
        raise ValueError("Invalid package or billing option")

    if not billing:
        billing = plan.interval
    price_id = plan.stripe_price_id
    
    customer = stripe.Customer.create(email=user.email)
    subscription_data = {}
    if plan.trial_days and plan.trial_days > 0:
        subscription_data["trial_period_days"] = plan.trial_days

    session = stripe.checkout.Session.create(
        customer=customer.id,
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        subscription_data=subscription_data,
        success_url="https://stemrn.vercel.app/payment-success",
        cancel_url="https://stemrn.vercel.app/payment-cancel",
    )
    return session.url

