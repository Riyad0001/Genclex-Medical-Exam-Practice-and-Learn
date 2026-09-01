"""
Installation:
1. Install CLI on your computer
2. Install stripe package: pip install stripe
3. Authenticate in your terminal: stripe login
4. Enable test mode in your Stripe dashboard and get your API keys
5. Add the keys to your .env file

"""

import stripe
from django.conf import settings
from django.dispatch import receiver
from django.utils import timezone
from .models import Plan, Subscription
from django.db.models.signals import post_save, pre_delete

stripe.api_key = settings.STRIPE_SECRET_KEY


@receiver(post_save, sender=Plan)
def create_stripe_product(sender, instance, created, **kwargs):
    stripe_interval = "month" if instance.interval == "monthly" else "year"
    if not instance.stripe_product_id:
        stripe_product = stripe.Product.create(
            name=instance.name, description=instance.description or ""
        )
        instance.stripe_product_id = stripe_product.id
        instance.save()
    if not instance.stripe_price_id:
        stripe_price = stripe.Price.create(
            product=instance.stripe_product_id,
            currency="USD",
            unit_amount=int(instance.price * 100),
            recurring={
                "interval": stripe_interval,  # Stripe expects month/year
            },
        )
        instance.stripe_price_id = stripe_price.id
        instance.save()


@receiver(post_save, sender=Plan)
def update_stripe_product(sender, instance, created, **kwargs):
    stripe_interval = "month" if instance.interval == "monthly" else "year"
    if instance.stripe_product_id and instance.stripe_price_id:
        stripe_product = stripe.Product.retrieve(instance.stripe_product_id)
        stripe_price = stripe.Price.retrieve(instance.stripe_price_id)

        if stripe_product["name"] != instance.name:
            stripe.Product.modify(stripe_product.id, name=instance.name)

        if stripe_price["unit_amount"] != int(instance.price * 100):
            stripe.Price.modify(instance.stripe_price_id, active=False)

            new_price = stripe.Price.create(
                product=instance.stripe_product_id,
                currency="USD",
                unit_amount=int(instance.price * 100),
                recurring={
                    "interval": stripe_interval,
                },
            )
            instance.stripe_price_id = new_price.id
            instance.save()


@receiver(pre_delete, sender=Plan)
def delete_stripe_product(sender, instance, **kwargs):
    if instance.stripe_product_id:
        stripe.Product.modify(
            instance.stripe_product_id,
            active=False,
        )
        stripe.Price.modify(
            instance.stripe_price_id,
            active=False,
        )
