from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.user.permission import IsNotBlacklisted

from .models import Notification, NotificationPreference
from .serializers import NotificationPreferenceSerializer, NotificationSerializer


class NotificationPreferenceAPIView(APIView):
	permission_classes = [IsAuthenticated, IsNotBlacklisted]

	def get_object(self, user):
		preference, _ = NotificationPreference.objects.get_or_create(user=user)
		return preference

	def get(self, request):
		preference = self.get_object(request.user)
		serializer = NotificationPreferenceSerializer(preference)
		return Response(serializer.data, status=status.HTTP_200_OK)

	def patch(self, request):
		preference = self.get_object(request.user)
		serializer = NotificationPreferenceSerializer(
			preference,
			data=request.data,
			partial=True,
		)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		return Response(serializer.data, status=status.HTTP_200_OK)

	def put(self, request):
		return self.patch(request)

	def post(self, request):
		return self.patch(request)


class NotificationListAPIView(APIView):
	permission_classes = [IsAuthenticated, IsNotBlacklisted]

	def get(self, request):
		notifications = Notification.objects.filter(user=request.user)
		unread_count = notifications.filter(is_read=False).count()
		serializer = NotificationSerializer(notifications, many=True)
		return Response(
			{
				"unread_count": unread_count,
				"notifications": serializer.data,
			},
			status=status.HTTP_200_OK,
		)
	

class NotificationListAPIView(APIView):
	permission_classes = [IsAuthenticated, IsNotBlacklisted]

	def get(self, request):
		notifications = Notification.objects.filter(user=request.user)
		unread_count = notifications.filter(is_read=False).count()
		serializer = NotificationSerializer(notifications, many=True)
		return Response(
			{
				"unread_count": unread_count,
				"notifications": serializer.data,
			},
			status=status.HTTP_200_OK,
		)


class NotificationMarkReadAPIView(APIView):
	permission_classes = [IsAuthenticated, IsNotBlacklisted]

	def patch(self, request, pk):
		notification = Notification.objects.filter(user=request.user, pk=pk).first()
		if not notification:
			return Response({"detail": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)

		notification.mark_read()
		serializer = NotificationSerializer(notification)
		return Response(serializer.data, status=status.HTTP_200_OK)

	def post(self, request, pk):
		return self.patch(request, pk)


class NotificationBulkUpdateAPIView(APIView):
	permission_classes = [IsAuthenticated, IsNotBlacklisted]

	def patch(self, request):
		from django.utils import timezone

		updated_count = Notification.objects.filter(
			user=request.user, is_read=False
		).update(is_read=True, read_at=timezone.now())

		return Response(
			{
				"detail": f"{updated_count} notification(s) marked as read.",
				"updated_count": updated_count,
			},
			status=status.HTTP_200_OK,
		)

	def post(self, request):
		return self.patch(request)


class NotificationDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsNotBlacklisted]

    def delete(self, request, pk=None):
     
        notification_id = pk or request.data.get("notification_id")

        if not notification_id:
            return Response(
                {
                    "success": False,
                    "message": "notification_id is required",
                },
                status=status.HTTP_400_BAD_REQUEST,)

        try:
            notification_id = int(notification_id)
        except (ValueError, TypeError):
            return Response(
                {
                    "success": False,
                    "message": "Invalid notification_id",
                },
                status=status.HTTP_400_BAD_REQUEST,)

      
        notification = Notification.objects.filter(
            id=notification_id,
            user=request.user
        ).first()

        print("Found notification:", notification)

        if not notification:
            return Response(
                {
                    "success": False,
                    "message": "Notification not found",
                    "debug": {
                        "user_id": request.user.id,
                        "notification_id": notification_id
                    }
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        notification.delete()

        return Response(
            {
                "success": True,
                "message": "Notification deleted successfully",
            },
            status=status.HTTP_200_OK,
        )