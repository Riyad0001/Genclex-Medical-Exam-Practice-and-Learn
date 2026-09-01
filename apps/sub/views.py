from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
from apps.notification.services import send_notification

import logging
logger = logging.getLogger(__name__)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import make_aware
from .models import Plan, Subscription
from .utils.stripe_utils import create_checkout_session
import stripe, datetime
from django.conf import settings
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import stripe, json
from .models import Plan, Subscription
from django.utils.timezone import make_aware
from datetime import datetime
from rest_framework.exceptions import NotFound
from django.contrib.auth import get_user_model
User = get_user_model()

# client real payment packages

stripe.api_key = settings.STRIPE_SECRET_KEY



class BaseAPIView(APIView):
    def success_response(self, message="Your request Accepted", data=None, status_code= status.HTTP_200_OK):
        return Response(
            {
            "success": True,
            "message": message,
            "status": status_code,
            "data": data or {}
            },
            status=status_code )
    def error_response(self, message="Your request rejected", data=None, status_code= status.HTTP_422_UNPROCESSABLE_ENTITY):
        return Response(
            {
            "success": False,
            "message": message,
            "status": status_code,
            "data": data or {}
            },
            status=status_code ) 


# List available plans for checkout
class ListPlansView(BaseAPIView):
    def get(self, request):
        plans = Plan.objects.order_by("price")
        data = [
            {
                "name": plan.name,
                "info": plan.description,
                "price": float(plan.price),
                "interval": plan.interval,
                "display_title": plan.display_title,
                "duration_label": plan.duration_label,
                "price_label": plan.price_label,
                "price_sub_label": plan.price_sub_label,
                "billing_note": plan.billing_note,
                "badge_text": plan.badge_text,
                "cta_text": plan.cta_text,
                "features": plan.features,
                "is_featured": plan.is_featured,
                "trial_days": plan.trial_days,
            }
            for plan in plans
        ]

        return self.success_response("Plans retrieved successfully.", data={"plans": data})


#  User payment checkout url give in stripe redirection    
class CreateCheckoutView(BaseAPIView):  # Inherit from BaseAPIView
    permission_classes = [IsAuthenticated]

    def post(self, request):
        package = request.data.get("package")
        billing = request.data.get("billing")

        if not package:
            return self.error_response("Package is required")

        try:
            session_url = create_checkout_session(request.user, package, billing)
            return self.success_response(
                message="Checkout session created successfully",
                data={"checkout_url": session_url},
                status_code=status.HTTP_200_OK
            )
        except ValueError as e:
            return self.error_response(
                message=str(e),
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        except Exception as e:
            return self.error_response(
                message=f"Checkout failed: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# user Subscription plan cancellation which only auto renual off and cancel at period end
class CancelSubscriptionView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            sub = Subscription.objects.get(user=request.user)
        except Subscription.DoesNotExist:
            return self.error_response("No active subscription found for this user.", status_code=404)

        try:
            stripe.Subscription.modify(
                sub.stripe_subscription_id,
                cancel_at_period_end=True
            )
            sub.auto_renew = False
            sub.cancel_at_period_end = True
            sub.save()
        except stripe.error.StripeError as e:
            return self.error_response("Stripe error: " + str(e), status_code=400)

        return self.success_response("Subscription cancellation scheduled at period end.", data={"auto_renew": False})




# user Subscription plan upgrade which only monthly subscription can be upgraded yearly
class UpgradeSubscriptionView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        new_package = request.data.get("package")
        new_billing = normalize_interval(request.data.get("billing"))

        if not new_package:
            return self.error_response("Package is required.", status_code=400)

        try:
            sub = Subscription.objects.get(user=user)
        except Subscription.DoesNotExist:
            return self.error_response("No active subscription found.", status_code=404)

        current_package = sub.package
        plan = None
        if new_billing:
            plan = Plan.objects.filter(name=new_package, interval=new_billing).first()
        if not plan:
            plan = Plan.objects.filter(name=new_package).first()
        new_price_id = plan.stripe_price_id if plan else None

        if not new_price_id:
            return self.error_response("Invalid package or billing option.", status_code=400)

        normalized_current_interval = normalize_interval(sub.billing_interval)
        if new_package == current_package and new_billing == normalized_current_interval:
            return self.error_response("Already subscribed to this package.", status_code=400)

        try:
            stripe_sub = stripe.Subscription.retrieve(sub.stripe_subscription_id)
            item_id = stripe_sub["items"]["data"][0]["id"]

            if stripe_sub.get("cancel_at_period_end"):
                stripe.Subscription.modify(
                    sub.stripe_subscription_id,
                    cancel_at_period_end=False
                )

            stripe.Subscription.modify(
                sub.stripe_subscription_id,
                items=[{
                    "id": item_id,
                    "price": new_price_id
                }],
                proration_behavior="create_prorations",
                payment_behavior="error_if_incomplete",
            )

            updated_sub = stripe.Subscription.retrieve(
                sub.stripe_subscription_id,
                expand=["latest_invoice.payment_intent", "customer"],
            )

            customer = updated_sub.get("customer") or {}
            customer_id = customer.get("id") if isinstance(customer, dict) else customer
            if customer_id and not sub.stripe_customer_id:
                sub.stripe_customer_id = customer_id
                sub.save(update_fields=["stripe_customer_id"])

            default_pm = updated_sub.get("default_payment_method") or customer.get("invoice_settings", {}).get("default_payment_method")
            if not default_pm:
                return self.error_response(
                    "No default payment method found for this customer.",
                    status_code=400,
                )

            if not updated_sub.get("default_payment_method"):
                stripe.Subscription.modify(
                    sub.stripe_subscription_id,
                    default_payment_method=default_pm,
                )

            invoice_obj = updated_sub.get("latest_invoice")
            invoice_id = invoice_obj.get("id") if isinstance(invoice_obj, dict) else invoice_obj
            if not invoice_id:
                invoice = stripe.Invoice.create(
                    customer=updated_sub["customer"],
                    subscription=updated_sub["id"],
                    auto_advance=True,
                )
                invoice_id = invoice.get("id")

            invoice = stripe.Invoice.retrieve(invoice_id, expand=["payment_intent"])
            if invoice.get("status") == "draft":
                invoice = stripe.Invoice.finalize_invoice(invoice_id)

            if invoice.get("status") in ["open", "uncollectible"]:
                invoice = stripe.Invoice.pay(invoice_id)

            invoice = stripe.Invoice.retrieve(invoice_id, expand=["payment_intent"])

            payment_intent = invoice.get("payment_intent")
            if isinstance(payment_intent, dict):
                pi_status = payment_intent.get("status")
                if pi_status == "requires_action":
                    return self.error_response(
                        "Payment requires additional authentication.",
                        status_code=402,
                        data={"payment_intent_id": payment_intent.get("id")},
                    )

            amount_due = invoice.get("amount_due") or 0
            if not invoice.get("paid") and amount_due > 0:
                return self.error_response(
                    "Payment did not complete.",
                    status_code=402,
                    data={
                        "invoice_id": invoice_id,
                        "invoice_status": invoice.get("status"),
                        "amount_due": amount_due,
                    },
                )

            sub.package = new_package
            sub.billing_interval = new_billing or normalized_current_interval
            sub.auto_renew = True
            sub.save()

            return self.success_response(
                "Subscription upgraded successfully.",
                data={
                    "invoice_id": invoice_id,
                    "invoice_status": invoice.get("status"),
                    "amount_paid": invoice.get("amount_paid"),
                },
            )

        except Exception as e:
            return self.error_response(str(e), status_code=500)

from django.utils import timezone
# user Subscription status and details
class MySubscriptionView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            sub = Subscription.objects.get(user=request.user)
        except Subscription.DoesNotExist:
            return self.error_response(
                "No active subscription found for this user.",
                status_code=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION
            )

        # If trial is ongoing
        is_trialing = (
            sub.trial_start is not None and 
            sub.trial_end is not None and 
            sub.trial_end > timezone.now()
        )

        normalized_interval = normalize_interval(sub.billing_interval)

        # 1) Use the direct FK relationship (most reliable)
        plan = sub.plan

        # 2) Fallback: resolve via Stripe subscription's actual price_id
        if not plan and sub.stripe_subscription_id:
            try:
                stripe_sub = stripe.Subscription.retrieve(sub.stripe_subscription_id)
                items_data = stripe_sub.get("items", {}).get("data", [])
                if items_data:
                    price_id = items_data[0].get("price", {}).get("id")
                    if price_id:
                        plan = Plan.objects.filter(stripe_price_id=price_id).first()
                        # Backfill the FK for future requests
                        if plan:
                            sub.plan = plan
                            sub.save(update_fields=["plan"])
            except Exception:
                pass

        # 3) Fallback: match by package name + interval
        if not plan:
            plan = Plan.objects.filter(
                name=sub.package,
                interval=normalized_interval
            ).first()

        # 4) Fallback: match by package name only
        if not plan:
            plan = Plan.objects.filter(name=sub.package).first()

        access_days = None
        if normalized_interval == "monthly":
            access_days = 30
        elif normalized_interval == "yearly":
            access_days = 365

        data = {
            # "subscription_id": sub.id,
            "plan_id": plan.id if plan else None,
            "plan_name": plan.name if plan else None,
            # "package": sub.package,
            "billing_interval": sub.billing_interval,
            "is_active": sub.is_active,
            "auto_renew": sub.auto_renew,
            "cancel_at_period_end": sub.cancel_at_period_end,
            "current_period_start": sub.current_period_start,
            "current_period_end": sub.current_period_end,
            "is_trialing": is_trialing,
            "trial_start": sub.trial_start,
            "trial_end": sub.trial_end,
            "package_price": float(plan.price) if plan else None,
            "access_days": access_days,
            "features": plan.features if plan else [],
        }

        return self.success_response("Subscription data retrieved successfully.", data)

# All payment and payment history 
class InvoiceHistoryView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            try:
                sub = Subscription.objects.select_related('user').get(user=request.user)
            except Subscription.DoesNotExist:
                return self.error_response(
                    message="No subscription found for this user",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            try:
                invoices = stripe.Invoice.list(
                    customer=sub.stripe_customer_id,
                    limit=100,
                    expand=["data.lines"],
                )

                invoice_data = []
                for inv in invoices["data"]:
                    paid_at = None
                    if inv.get("status_transitions", {}).get("paid_at"):
                        paid_at = make_aware(
                            datetime.fromtimestamp(inv["status_transitions"]["paid_at"])
                        ).isoformat()

                    line_item = None
                    lines = inv.get("lines", {}).get("data", [])
                    if lines:
                        line_item = lines[0]

                    price_id = None
                    if line_item and line_item.get("price"):
                        price_id = line_item["price"].get("id")

                    package_name = get_package_from_price_id(price_id) if price_id else "unknown"

                    invoice_data.append(
                        {
                            "invoice_id": inv["id"],
                            "paid_date": paid_at,
                            "package": package_name,
                            "amount": inv["amount_paid"] / 100,
                            "invoice_url": inv.get("invoice_pdf"),
                        }
                    )

                return self.success_response(
                    message="Invoice history retrieved successfully",
                    data={"invoices": invoice_data}
                )

            except stripe.error.StripeError as e:
                return self.error_response(
                    message=f"Stripe API error: {str(e)}",
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
                )

        except Exception as e:
            return self.error_response(
                message="An unexpected error occurred",
                data={"error": str(e)},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# Card Save Features
# class SaveCardView(BaseAPIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         payment_method_id = request.data.get("payment_method_id")
#         if not payment_method_id:
#             return self.error_response("Payment method ID is required", status_code=400)

#         try:
#             sub = Subscription.objects.get(user=request.user)
#             customer_id = sub.stripe_customer_id

#             # Attach to customer
#             stripe.PaymentMethod.attach(
#                 payment_method_id,
#                 customer=customer_id
#             )

#             # Optionally set as default
#             stripe.Customer.modify(
#                 customer_id,
#                 invoice_settings={
#                     'default_payment_method': payment_method_id,
#                 }
#             )

#             return self.success_response("Card saved successfully.")

#         except Exception as e:
#             return self.error_response(str(e), status_code=500)

# Payment Saved card class
class ListSavedCardsView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            sub = Subscription.objects.get(user=request.user)
            customer_id = sub.stripe_customer_id

            cards = stripe.PaymentMethod.list(
                customer=customer_id,
                type="card"
            )

            data = [
                {
                    "id": card.id,
                    "brand": card.card.brand,
                    "last4": card.card.last4,
                    "exp_month": card.card.exp_month,
                    "exp_year": card.card.exp_year,
                    "is_default": (card.id == stripe.Customer.retrieve(customer_id).invoice_settings.default_payment_method)
                }
                for card in cards.data
            ]

            return self.success_response("Saved cards retrieved.", data=data)

        except Exception as e:
            return self.error_response(str(e), status_code=500)

# Delete user saved card class 
class DeleteAllCardsView(BaseAPIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        try:
            # Get user's subscription
            sub = Subscription.objects.get(user=request.user)
            customer_id = sub.stripe_customer_id

            # List all cards attached to this customer
            cards = stripe.PaymentMethod.list(customer=customer_id, type="card")

            # Detach each card
            for card in cards.data:
                stripe.PaymentMethod.detach(card.id)

            # Clear default payment method
            stripe.Customer.modify(customer_id, invoice_settings={"default_payment_method": None})

            return self.success_response(
                "All saved cards deleted successfully. Next payment will require a new card."
            )

        except Subscription.DoesNotExist:
            return self.error_response("No active subscription found for user.", status_code=404)
        except stripe.error.StripeError as e:
            return self.error_response(f"Stripe error: {str(e)}", status_code=500)
        except Exception as e:
            return self.error_response(str(e), status_code=500)

# Payments success after user redirection
class StripePaymentSuccessView(BaseAPIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return self.success_response(message="Payment completed successfully.")
class StripePaymentCancelled(BaseAPIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return self.error_response(
            message="Payment was cancelled. No charges were made.",
            status_code=400
        )


# Stripe Webhook to handle events like subscription creation,cancellation,and invoice creation
@csrf_exempt
def stripe_webhook(request):
    print("🔔 Stripe Webhook triggered")

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    if sig_header is None:
        return JsonResponse({'error': 'missing signature header'}, status=422)

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        return JsonResponse({'error': 'invalid signature'}, status=422)
    except Exception as e:
        print(f" Exception during event parsing: {e}")
        return JsonResponse({'error': str(e)}, status=422)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        customer_id = session.get("customer")
        subscription_id = session.get("subscription")
        email = session.get("customer_email") or session.get("customer_details", {}).get("email")

        if not email:
            return JsonResponse({"error": "No customer email found in session"}, status=422)

        user = User.objects.filter(email=email).first()
        if not user:
            return JsonResponse({"error": f"No user found with email {email}"}, status=404)

        print(f" Matched user: {user.email}")

        try:
            stripe_sub = stripe.Subscription.retrieve(subscription_id)
            # print(" Stripe Subscription:", stripe_sub)

            item_data = stripe_sub.get("items", {}).get("data", [])
            if item_data:
                item = item_data[0]  # First subscription item
                period_start_ts = item.get("current_period_start")  # Access from item, not stripe_sub
                period_end_ts = item.get("current_period_end")
                trial_start_ts = stripe_sub.get("trial_start")
                trial_end_ts = stripe_sub.get("trial_end")
                price_id = item["price"]["id"]
                price = item.get("price", {})
                price_id = price.get("id")
                recurring = price.get("recurring", {})
                interval = normalize_interval(recurring.get("interval"))
                print("Interval:", interval)
                package = get_package_from_price_id(price_id)
                plan_obj = Plan.objects.filter(stripe_price_id=price_id).first()
            else:
                item = {}
                package = "unknown"
                plan_obj = None
                interval = None
                period_start_ts = period_end_ts = None
                trial_start_ts = trial_end_ts = None
            print("database going process")
            Subscription.objects.update_or_create(
                user=user,
                defaults={
                    "plan": plan_obj,
                    "stripe_customer_id": customer_id,
                    "stripe_subscription_id": subscription_id,
                    "package": package,
                    "billing_interval": interval,
                    "current_period_start": make_aware(datetime.fromtimestamp(period_start_ts)) if period_start_ts else None,
                    "current_period_end": make_aware(datetime.fromtimestamp(period_end_ts)) if period_end_ts else None,
                    "trial_start" :       make_aware(datetime.fromtimestamp(trial_start_ts)) if trial_start_ts else None,
                    "trial_end" :         make_aware(datetime.fromtimestamp(trial_end_ts)) if trial_end_ts else None,
                    "auto_renew": not stripe_sub.get("cancel_at_period_end", False),
                    "cancel_at_period_end": stripe_sub.get("cancel_at_period_end", False),
                    "is_active": True
                }
            )
            print(" Subscription updated/created")
            send_notification(user, "subscription_created", {"message": "Subscription received successfully"})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=422)
    elif event["type"] == "customer.subscription.updated":
        data = event["data"]["object"]
        print("data:",data)

        subscription_id = data.get("id")
        customer_id = data.get("customer")
        status = data.get("status")
        
        # Get subscription item info
        items_data = data.get("items", {}).get("data", [])
        if items_data:
            item = items_data[0]
            period_start_ts = item.get("current_period_start")
            period_end_ts = item.get("current_period_end")
            trial_start_ts = data.get("trial_start")
            trial_end_ts = data.get("trial_end")
            price = item.get("price", {})
            price_id = price.get("id")
            recurring = price.get("recurring", {})
            interval = normalize_interval(recurring.get("interval"))
            package = get_package_from_price_id(price_id)  # your function
            plan_obj = Plan.objects.filter(stripe_price_id=price_id).first()
        else:
            item = {}
            package = "unknown"
            plan_obj = None
            interval = None
            period_start_ts = period_end_ts = None
            trial_start_ts = trial_end_ts = None

        # Find user linked to this Stripe customer
        customer_obj = Subscription.objects.filter(stripe_customer_id=customer_id).first()
        if customer_obj:
            customer_obj.plan = plan_obj
            customer_obj.stripe_subscription_id = subscription_id
            customer_obj.status = status
            customer_obj.package = package
            customer_obj.billing_interval = interval
            customer_obj.current_period_start = make_aware(datetime.fromtimestamp(period_start_ts)) if period_start_ts else None
            customer_obj.current_period_end = make_aware(datetime.fromtimestamp(period_end_ts)) if period_end_ts else None
            customer_obj.trial_start = make_aware(datetime.fromtimestamp(trial_start_ts)) if trial_start_ts else None
            customer_obj.trial_end = make_aware(datetime.fromtimestamp(trial_end_ts)) if trial_end_ts else None
            customer_obj.auto_renew = not data.get("cancel_at_period_end", False)
            customer_obj.cancel_at_period_end = data.get("cancel_at_period_end", False)
            customer_obj.is_active = status in ["active", "trialing"]
            customer_obj.save()
            logger.info(f"🔄 StripeCustomer updated for {customer_obj.user.email}")
        else:
            logger.warning(f"⚠️ No StripeCustomer found for customer_id={customer_id}")


    elif event["type"] == "customer.subscription.deleted":
        print(" Handling customer.subscription.deleted")
        stripe_sub = event["data"]["object"]
        sub = Subscription.objects.filter(stripe_subscription_id=stripe_sub["id"]).first()
        if sub:
            sub.is_active = False
            sub.cancel_at_period_end = True
            sub.save()
            print(f" Subscription {sub.id} marked inactive")

    elif event["type"] == "invoice.created":
        invoice = event["data"]["object"]
        print(f"🧾 Invoice created: {invoice['id']}")
        return JsonResponse({'status': 'invoice.created received'}, status=200)

    return JsonResponse({"status": "ok"})

# 🔍 Debugging for package ID resolution
def get_package_from_price_id(price_id):
    if not price_id:
        return "unknown"
    plan = Plan.objects.filter(stripe_price_id=price_id).first()
    return plan.name if plan else "unknown"


def normalize_interval(interval):
    if not interval:
        return interval
    if interval == "month":
        return "monthly"
    if interval == "year":
        return "yearly"
    return interval







# permission classes 
from rest_framework.permissions import BasePermission  
class HasPackageSubscription(BasePermission):
    def has_permission(self, request, view):
        try:
            sub = Subscription.objects.get(user=request.user)
            return (
                sub.is_active
            )
        except Subscription.DoesNotExist:
            return False
        
