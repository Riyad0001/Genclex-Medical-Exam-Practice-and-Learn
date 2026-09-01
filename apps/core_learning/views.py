from django.db.models import Prefetch
from rest_framework.permissions import IsAuthenticated
from .models import LearningContentIcon, LearningContentColor
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import LimitOffsetPagination

from .utils import calculate_category_progress
from .models import (
    LearningCategory,
    LearningContent,
    SavedNotes,
    LearningProgress,
    Library,
    
)
from .serializers import (
    LearningCategorySerializer,
    LearningContentSerializer,
    LibrarySerializer,
)


class LearningContentView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, topic=None):
        user = request.user

        topic = topic.lower()
        paginator = LimitOffsetPagination()
        paginator.default_limit = 6
        paginator.max_limit = 100

        try:
            categories = LearningCategory.objects.prefetch_related(
                Prefetch(
                    "contents", queryset=LearningContent.objects.filter(is_active=True)
                )
            ).filter(topic__iexact=topic)
        except LearningCategory.DoesNotExist:
            raise ValidationError(f"No learning category found for topic: {topic}")

        # content = categories.contents.filter(is_active=True)
        paginated_queryset = paginator.paginate_queryset(categories, request, view=self)
        serializer = LearningCategorySerializer(
            paginated_queryset, many=True, context={"request": request}
        )

        ## STUDY NOTES PROGRESS
        if topic in ["study_notes", "stem_toons", "cheat_sheet"]:
            for category_data, category_obj in zip(serializer.data, categories):
                category_data["progress"] = calculate_category_progress(
                    user,
                    category_obj
                )   
        ## STUDY NOTES PROGRESS END
        # FIXME: REDUCE DUPLICATE QUERIES
        response_data = {
            "code": status.HTTP_200_OK,
            "status": "success",
            "message": f"Learning content for topic '{topic}' retrieved successfully.",
            "data": serializer.data,
            "pagination": {
                "count": paginator.count,
                "limit": paginator.limit,
                "offset": paginator.offset,
                "next": paginator.get_next_link(),
                "previous": paginator.get_previous_link(),
            },
        }
        return Response(response_data, status=status.HTTP_200_OK)


class LearningContentDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, category_id=None, content_id=None):
        user = request.user

        if content_id:
            try:
                content = LearningContent.objects.get(id=content_id, is_active=True)
            except LearningContent.DoesNotExist:
                raise ValidationError(
                    f"Learning content with id {content_id} does not exist."
                )
            serializer = LearningContentSerializer(
                content, context={"request": request}
            )
            response_data = {
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": f"Learning content with id {content_id} retrieved successfully.",
                "data": serializer.data,
            }
            return Response(response_data, status=status.HTTP_200_OK)
        ## LEARNING CONTENT DETAIL VIEW - END
        if category_id:
            try:
                category = LearningCategory.objects.get(id=category_id)
            except LearningCategory.DoesNotExist:
                raise ValidationError(
                    f"Learning category with id {category_id} does not exist."
                )
            serializer = LearningCategorySerializer(
                category, context={"request": request}
            )
            response_data = {
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": f"Learning category with id {category_id} retrieved successfully.",
                "data": serializer.data,
            }
            return Response(response_data, status=status.HTTP_200_OK)
        raise ValidationError(f"Not Found!")
class LibraryView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request): 
        user = request.user
        libraries = Library.objects.filter(user=user, is_active=True)
        serializer = LibrarySerializer(libraries, many=True, context={"request": request})
        response_data = {
            "code": status.HTTP_200_OK,
            "status": "success",
            "message": "User libraries retrieved successfully.",
            "data": serializer.data,
        }
        return Response(response_data, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        data = request.data
        data["user"] = request.user.id
        serializer = LibrarySerializer(data=data, context={request: request})
        if serializer.is_valid():
            library = serializer.save(user=user)
            response_data = {
                "code": status.HTTP_201_CREATED,
                "status": "success",
                "message": "Library created successfully.",
                # "library_id": library.id,
                "data": serializer.data,
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        raise ValidationError(serializer.errors)


class SavedNotesView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        content_id = request.data.get("content_id")
        folder_id = request.data.get("folder_id")

        try:
            content = LearningContent.objects.get(id=content_id)
            library = Library.objects.get(id=folder_id, user=user)
        except LearningContent.DoesNotExist:
            raise ValidationError(f"Content or Folder Does Not Exist")
        except Library.DoesNotExist:
            raise ValidationError(f"Folder Does Not Exist")

        try:
            saved_note, created = SavedNotes.objects.get_or_create(
                user=user,
                content=content,
                library=library
            )
        except Exception as e:
            raise ValidationError("Something wrong")

        if not created:
            saved_note.delete()
            return Response({
                "code": status.HTTP_200_OK,
                "status": "success",
                "message": "Saved Lectures deleted Successfullly!"
            }, status=status.HTTP_200_OK)

        response_data = {
            "code": status.HTTP_200_OK,
            "status": "success",
            "message": "Notes saved successfully.",
            "data": {
                "id": saved_note.id,
                "save_on": saved_note.library.name,
            }
        }
        return Response(response_data, status=status.HTTP_200_OK)


class MarkAsCompletedAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, content_id):
        user = request.user
        try:
            content = LearningContent.objects.get(id=content_id)
        except LearningContent.DoesNotExist:
            raise ValidationError("Content not Found!")

        progress, created = LearningProgress.objects.get_or_create(
            user=user,
            content=content,
            defaults={"is_completed": True}
        )

        if not created:
            # Toggle: if already completed → mark incomplete; if incomplete → mark complete
            progress.is_completed = not progress.is_completed
            progress.save(update_fields=["is_completed"])

            if progress.is_completed:
                return Response({
                    "code": status.HTTP_200_OK,
                    "status": "success",
                    "message": "Content is marked as read"
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "code": status.HTTP_200_OK,
                    "status": "success",
                    "message": "Content is marked as un-read and removed from tracking list"
                }, status=status.HTTP_200_OK)

        response_data = {
            "code": status.HTTP_200_OK,
            "status": "success",
            "message": "Content is marked as read"
        }
        return Response(response_data, status=status.HTTP_200_OK)


class LearningIconAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        icons = LearningContentIcon.objects.filter(is_active=True).order_by("id")
        icon_data = []
        for x in icons:
            file_url = getattr(x.icon, "url", None)
            icon_data.append({"id": x.id, "icon": file_url})

        response_data = {
            "code": status.HTTP_200_OK,
            "success": True,
            "message": "Icon List",
            "data": icon_data
        }
        return Response(response_data, status=status.HTTP_200_OK)


class LibraryColorAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        colors = LearningContentColor.objects.filter(is_active=True).order_by("id")
        color_data = [{"id": x.id, "color": x.color} for x in colors]

        response_data = {
            "code": status.HTTP_200_OK,
            "success": True,
            "message": "Color List",
            "data": color_data
        }
        return Response(response_data, status=status.HTTP_200_OK)


class LibraryDetailView(APIView):

    permission_classes = [permissions.IsAuthenticated]

    # DELETE = folder delete
    def delete(self, request, pk):
        user = request.user

        try:
            library = Library.objects.get(pk=pk, user=user)
            library.delete()

            return Response({
                "code": 200,
                "status": "success",
                "message": "Library deleted successfully."
            }, status=status.HTTP_200_OK)

        except Library.DoesNotExist:
            return Response({
                "code": 404,
                "status": "error",
                "message": "Library not found."
            }, status=status.HTTP_404_NOT_FOUND)

    # PATCH = rename folder
    def patch(self, request, pk):
        user = request.user
        new_name = request.data.get("name")

        if not new_name:
            return Response({
                "code": 400,
                "status": "error",
                "message": "Name is required."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            library = Library.objects.get(pk=pk, user=user)

            if Library.objects.filter(user=user, name__iexact=new_name).exclude(pk=pk).exists():
                return Response({
                    "code": 400,
                    "status": "error",
                    "message": "Library name already exists."
                }, status=status.HTTP_400_BAD_REQUEST)

            library.name = new_name
            library.save()

            return Response({
                "code": 200,
                "status": "success",
                "message": "Library renamed successfully.",
                "data": {
                    "id": library.id,
                    "name": library.name
                }
            }, status=status.HTTP_200_OK)

        except Library.DoesNotExist:
            return Response({
                "code": 404,
                "status": "error",
                "message": "Library not found."
            }, status=status.HTTP_404_NOT_FOUND)




class LearningDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        categories = LearningCategory.objects.prefetch_related(
            "contents"
        ).order_by("id")

        total_categories = categories.count()

        total_contents = LearningContent.objects.filter(
            is_active=True
        ).count()

        completed_contents = LearningProgress.objects.filter(
            user=user,
            is_completed=True,
            content__is_active=True
        ).count()

        completed_category_count = 0
        in_progress_category_count = 0
        not_started_category_count = 0

        topics = []
        recent_activity = []

        for category in categories:

            contents = category.contents.filter(is_active=True)

            total = contents.count()

            completed = LearningProgress.objects.filter(
                user=user,
                content__category=category,
                is_completed=True
            ).count()

            percentage = (
                round((completed / total) * 100)
                if total else 0
            )

            if completed == 0:

                category_status = "not_started"
                not_started_category_count += 1

            elif completed == total:

                category_status = "completed"
                completed_category_count += 1

                latest = (
                    LearningProgress.objects.filter(
                        user=user,
                        content__category=category,
                        is_completed=True
                    )
                    .order_by("-completed_at")
                    .first()
                )

                recent_activity.append({
                    "category_id": category.id,
                    "title": category.title,
                    "subtitle": category.subtitle,
                    "cover": (
                        request.build_absolute_uri(category.cover.url)
                        if category.cover else None
                    ),
                    "completed_at": latest.completed_at if latest else None
                })

            else:

                category_status = "in_progress"
                in_progress_category_count += 1

            topics.append({
                "category_id": category.id,
                "title": category.title,
                "subtitle": category.subtitle,
                "cover": (
                    request.build_absolute_uri(category.cover.url)
                    if category.cover else None
                ),
                "progress": f"{completed}/{total}",
                "percentage": f"{percentage}%",
                "status": category_status
            })

        recent_activity.sort(
            key=lambda x: x["completed_at"] or "",
            reverse=True
        )

        content_summary = {

            "total_completed": {
                "progress": f"{completed_contents}/{total_contents}",
                "percentage": (
                    f"{round((completed_contents / total_contents) * 100)}%"
                    if total_contents else "0%"
                )
            },

            "marked_completed": {
                "count": completed_category_count,
                "percentage": (
                    f"{round((completed_category_count / total_categories) * 100)}%"
                    if total_categories else "0%"
                )
            },

            "in_progress": {
                "count": in_progress_category_count,
                "percentage": (
                    f"{round((in_progress_category_count / total_categories) * 100)}%"
                    if total_categories else "0%"
                )
            },

            "not_started": {
                "count": not_started_category_count,
                "percentage": (
                    f"{round((not_started_category_count / total_categories) * 100)}%"
                    if total_categories else "0%"
                )
            },
        }

        return Response(
            {
                "success": True,
                "message": "Dashboard fetched successfully.",
                "status": status.HTTP_200_OK,
                "data": {
                    "content_summary": content_summary,
                    "topics": topics,
                    "recent_activity": recent_activity[:5]
                }
            },
            status=status.HTTP_200_OK
        )