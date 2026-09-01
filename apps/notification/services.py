from typing import Any, Dict, Iterable, List, Optional

from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Notification, NotificationPreference

EVENT_TO_PREF_FIELD = {
    "transaction_confirmation": "transaction_confirmation",
    "transaction_edited": "transaction_edited",
    "transaction_invoice": "transaction_invoice",
    "transaction_cancelled": "transaction_cancelled",
    "transaction_refund": "transaction_refund",
    "payment_error": "payment_error",
}


def _normalize_user(user_or_id):
    User = get_user_model()
    if isinstance(user_or_id, User):
        return user_or_id
    return User.objects.get(pk=user_or_id)


def _build_notification_response(payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    message = "Notification sent"
    if payload and payload.get("message"):
        message = payload["message"]

    return {
        "message": message,
        "time": timezone.now().isoformat(),
    }


def _persist_notification(user_obj, event: str, payload: Optional[Dict[str, Any]]) -> Notification:
    message = "Notification sent"
    if payload and payload.get("message"):
        message = payload["message"]

    return Notification.objects.create(
        user=user_obj,
        event=event,
        message=message,
    )


def send_notification(
    user: Any,
    event: str,
    payload: Optional[Dict[str, Any]] = None,
    channels: Optional[Iterable[str]] = None,
    force: bool = False,
    use_celery: bool = False,
) -> Dict[str, Any]:
    """Send or enqueue a notification for a user.

    Usage: call `send_notification(user, "transaction_confirmation", {"amount": 10})`

    This function will:
    - consult the user's NotificationPreference for the given event
    - decide which channels to use (email, in_app, push, realtime)
    - enqueue a background delivery task if Celery is available and `use_celery` is True
    - fall back to synchronous delivery otherwise

    Returns a dict with a minimal result summary.
    """
    if payload is None:
        payload = {}

    # Resolve user instance
    user_obj = _normalize_user(user)

    # Ensure we have a preference row; creating it simplifies callers
    preference, _ = NotificationPreference.objects.get_or_create(user=user_obj)

    # Map event -> preference boolean
    pref_field = EVENT_TO_PREF_FIELD.get(event)

    # Determine allowed channels from preferences
    allowed: List[str] = []
    if channels:
        allowed = list(channels)
    else:
        # Default routing: if user's pref for the event is True, allow email + in_app.
        if pref_field and getattr(preference, pref_field, False):
            if getattr(user_obj, "email", None):
                allowed.append("email")
            allowed.append("in_app")

    if not allowed and not force:
        return _build_notification_response(payload)

    # If Celery usage requested, try to enqueue; otherwise run sync delivery.
    if use_celery:
        try:
            from .tasks import deliver_notification_task

            if deliver_notification_task is not None:
                deliver_notification_task.delay(user_obj.pk, event, payload, allowed)
                return _build_notification_response(payload)
        except Exception:
            # Enqueue failed — fall back to sync delivery
            pass

    # Synchronous delivery path (default)
    try:
        from .tasks import deliver_notification_sync

        deliver_notification_sync(user_obj.pk, event, payload, allowed)
        _persist_notification(user_obj, event, payload)
        return _build_notification_response(payload)
    except Exception:
        try:
            _persist_notification(user_obj, event, payload)
        except Exception:
            pass
        return _build_notification_response(payload)


def send_notification_sync(user: Any, event: str, payload: Optional[Dict[str, Any]] = None, channels: Optional[Iterable[str]] = None, force: bool = False) -> Dict[str, Any]:
    """Explicit synchronous helper that always delivers immediately (no Celery)."""
    return send_notification(user, event, payload=payload, channels=channels, force=force, use_celery=False)
