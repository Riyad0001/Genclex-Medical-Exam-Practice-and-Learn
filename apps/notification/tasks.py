from typing import Any, Dict, Iterable, List

from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string


def deliver_notification_sync(user_id: int, event: str, payload: Dict[str, Any], channels: Iterable[str]):
    """Synchronous delivery implementation.

    This function is intentionally simple and suitable as a fallback when
    a background worker is not configured. For production, prefer running
    `deliver_notification_task` in Celery and moving heavy work off-request.
    """
    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return {"delivered": False, "reason": "user_not_found"}

    results = {"delivered": [], "skipped": []}

    for channel in channels:
        if channel == "email":
            if not getattr(user, "email", None):
                results["skipped"].append("email_no_address")
                continue
            subject = f"Notification: {event.replace('_', ' ').title()}"
            message = payload.get("message") or str(payload)
            from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)
            try:
                # Render HTML email template
                html_content = render_to_string('otp_email_template/notification.html', {
                    'user': user,
                    'notification_title': subject,
                    'notification_message': message,
                    'company_name': getattr(settings, 'COMPANY_NAME', 'Our Platform'),
                })
                
                # Send HTML email
                email_message = EmailMessage(
                    subject=subject,
                    body=html_content,
                    from_email=from_email,
                    to=[user.email],
                )
                email_message.content_subtype = 'html'
                email_message.send(fail_silently=False)
                results["delivered"].append("email")
            except Exception:
                results["skipped"].append("email_failed")

        elif channel == "in_app":
            # If you later add a persisted Notification model, create and save it here.
            # For now we simply record that in-app delivery should occur.
            results["delivered"].append("in_app")

        elif channel == "push":
            # Push provider integration (FCM/APNs) goes here.
            results["skipped"].append("push_not_configured")

        elif channel == "realtime":
            # Real-time (WebSocket) delivery would publish to a channel or group.
            results["skipped"].append("realtime_not_configured")

        else:
            results["skipped"].append(f"unknown:{channel}")

    return results


try:
    # If Celery is installed, expose a shared task wrapper.
    from celery import shared_task


    @shared_task(bind=False)
    def deliver_notification_task(user_id: int, event: str, payload: Dict[str, Any], channels: List[str]):
        return deliver_notification_sync(user_id, event, payload, channels)

except Exception:
    # Celery not available; omit task wrapper. Code that imports
    # `deliver_notification_task` should handle ImportError/AttributeError.
    deliver_notification_task = None
