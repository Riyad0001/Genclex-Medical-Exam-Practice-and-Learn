from django.urls import path

from .views import (
    NotificationBulkUpdateAPIView,
    NotificationListAPIView,
    NotificationMarkReadAPIView,
    NotificationPreferenceAPIView,
    NotificationDetailAPIView
)

urlpatterns = [
    path("notifications/preferences/", NotificationPreferenceAPIView.as_view(), name="notification-preferences"),
    path("notifications/settings/", NotificationPreferenceAPIView.as_view(), name="notification-settings"),
    path("notifications/", NotificationListAPIView.as_view(), name="notifications-list"),
    path("notifications/<int:pk>/read/", NotificationMarkReadAPIView.as_view(), name="notifications-mark-read"),
    path("notifications/bulk-update/",NotificationBulkUpdateAPIView.as_view(),name="notification-bulk-update",),

   path("notifications/<int:pk>/", NotificationDetailAPIView.as_view()),
]