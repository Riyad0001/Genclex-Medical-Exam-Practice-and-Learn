from django.urls import path
from .views import *
urlpatterns = [
    path("plans/", ListPlansView.as_view()),
    path("subscribe/", CreateCheckoutView.as_view()),
    path("subscription/cancel/", CancelSubscriptionView.as_view()),
    path("subscription/upgrade/", UpgradeSubscriptionView.as_view()),
    path("subscription/my/", MySubscriptionView.as_view()),
    path("payment-history/", InvoiceHistoryView.as_view()),
    path("webhook/stripe/", stripe_webhook),
    # path("cards/save/", SaveCardView.as_view()),
    path("cards/list/", ListSavedCardsView.as_view()),
    path("cards/delete/", DeleteAllCardsView.as_view()),
    # path("payment/success/", StripePaymentSuccessView.as_view()),
    # path("subscription/cancel/", StripePaymentCancelled.as_view()),
]