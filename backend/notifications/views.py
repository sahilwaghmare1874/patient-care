from rest_framework import views, status, permissions
from rest_framework.response import Response
from .models import Notification
from .serializers import NotificationSerializer

class NotificationListView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        user_id = request.query_params.get('user_id')
        unread_only = request.query_params.get('unread_only', '').lower() in ('1', 'true', 'yes')

        if user_id:
            notifications = Notification.objects.filter(recipient_id=user_id)
        elif request.user.is_authenticated:
            notifications = Notification.objects.filter(recipient=request.user)
        else:
            notifications = Notification.objects.all()[:20]

        if unread_only:
            notifications = notifications.filter(is_read=False)

        return Response({
            "notifications": NotificationSerializer(notifications, many=True).data,
            "total": notifications.count() if hasattr(notifications, 'count') else len(notifications),
            "unread": notifications.filter(is_read=False).count() if hasattr(notifications, 'filter') else 0,
        })


class NotificationMarkReadView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, notification_id):
        notif = Notification.objects.filter(id=notification_id).first()
        if not notif:
            return Response({"error": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)

        notif.is_read = True
        notif.save()
        return Response({"message": "Marked as read."})


class NotificationMarkAllReadView(views.APIView):
    """Mark all notifications as read for a given user (by user_id param or authenticated user)."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user_id = request.data.get('user_id') or request.query_params.get('user_id')
        if user_id:
            qs = Notification.objects.filter(recipient_id=user_id, is_read=False)
        elif request.user.is_authenticated:
            qs = Notification.objects.filter(recipient=request.user, is_read=False)
        else:
            return Response(
                {"error": "Provide user_id or authenticate to mark notifications as read."},
                status=status.HTTP_400_BAD_REQUEST
            )
        count = qs.update(is_read=True)
        return Response({"message": f"{count} notification(s) marked as read.", "count": count})


class NotificationUnreadCountView(views.APIView):
    """Returns the count of unread notifications for a user."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        user_id = request.query_params.get('user_id')
        if user_id:
            count = Notification.objects.filter(recipient_id=user_id, is_read=False).count()
        elif request.user.is_authenticated:
            count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        else:
            count = 0
        return Response({"unread_count": count})
