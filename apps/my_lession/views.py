from requests import request
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.contenttypes.fields import GenericRelation
from rest_framework.permissions import IsAuthenticated
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404

from apps.my_lession.models import Module, VideoContent, VedioProgress
from .serializers import (
    ModuleSerializer,
    VideoDetailsSerializer,
    VedioProgressSerializer
)


class ModuleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_overall_video_summary(self, user):
       
        all_videos = VideoContent.objects.all()

        progress = VedioProgress.objects.filter(user=user)

        print("User:",user.email,)
        print(
            list(
                progress.values(
                    "user_id",
                    "vedio_content_id",
                    "current_duration",
                    "total_duration",
                    "is_completed",
                )
            )
        )

        progress_map = {
            p.vedio_content_id: p
            for p in progress
        }

        watched = 0
        in_progress = 0
        not_started = 0

        for video in all_videos:
            p = progress_map.get(video.id)

            if p:
                if p.is_completed:
                    watched += 1
                elif p.current_duration > 0:
                    in_progress += 1
                else:
                    not_started += 1
            else:
                not_started += 1

        return {
            "total_videos": all_videos.count(),
            "watched_count": watched,
            "in_progress_count": in_progress,
            "not_started_count": not_started,
        }

    def get_video_summary(self, module, user):
        print("Summary user:", user.id, user.email)
      
        all_videos = VideoContent.objects.filter(module=module)

    
        progress = VedioProgress.objects.filter(
            user=user,
            vedio_content__module=module
        )

        progress_map = {
            p.vedio_content_id: p
            for p in progress
        }

        watched = 0
        in_progress = 0
        not_started = 0

        for video in all_videos:
            p = progress_map.get(video.id)

            if p:
                if p.is_completed:
                    watched += 1
                elif p.current_duration > 0:
                    in_progress += 1
                else:
                    not_started += 1
            else:
                not_started += 1

        return {
            "total_videos": all_videos.count(),
            "watched_count": watched,
            "in_progress_count": in_progress,
            "not_started_count": not_started,
        }

    def get(self, request, pk=None):
        print("Logged in user:", request.user.id, request.user.email)
        user = request.user

        # Single Module
        if pk:
            module = get_object_or_404(
                Module.objects.prefetch_related("vedio"),
                pk=pk
            )

            serializer = ModuleSerializer(module)

            return Response({
                "success": True,
                "message": "Module fetched successfully",
                "status": 200,
                "data": {
                    "video_progress": self.get_video_summary(module, user),
                    "module": serializer.data,
                }
            })

    
        modules = Module.objects.prefetch_related("vedio").all()

        module_data = []

        for module in modules:
            module_data.append({
                "video_progress": self.get_video_summary(module, user),
                "module": ModuleSerializer(module).data,
            })

        return Response({
            "success": True,
            "message": "Modules fetched successfully",
            "status": 200,
            "data": {
                "video_progress": self.get_overall_video_summary(user),
                "modules": module_data,
            }
        })
    

class VideoDetailsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            video = VideoContent.objects.get(
                id=pk
            )

            serializer = VideoDetailsSerializer(
                video
            )

            return Response({
                "success": True,
                "message": "Video details fetched successfully",
                "status": 200,
                "data": serializer.data
            })

        except VideoContent.DoesNotExist:
            return Response({
                "success": False,
                "message": "Video not found",
                "status": 404
            }, status=status.HTTP_404_NOT_FOUND)
    

class VideoProgressCreateUpdateView(APIView):

    def post(self, request, video_id):
        
        print("Progress User:", request.user.id)
        print("Progress Email:", request.user.email)

        total_duration = request.data.get('total_duration')
        current_duration = request.data.get('current_duration', 0)
        is_completed = request.data.get('is_completed', False)

        video = VideoContent.objects.get(id=video_id)

        progress, created = VedioProgress.objects.get_or_create(
            user=request.user,
            vedio_content=video,
            defaults={
                "total_duration": total_duration,
                "current_duration": current_duration,
                "is_completed": is_completed
            }
        )

        if not created:
            progress.total_duration = total_duration
            progress.current_duration = current_duration
            progress.is_completed = is_completed
            progress.save()

        serializer = VedioProgressSerializer(progress)

        return Response({
            "success": True,
            "message": "Request successful",
            "status": 200,
            "data": serializer.data
        })
    


class VideoProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        all_videos = VideoContent.objects.all()
        progresses = VedioProgress.objects.filter(user=request.user)

        print(progresses.values(
            "user_id",
            "vedio_content_id",
            "current_duration",
            "is_completed"
        ))

        watched_count = 0
        in_progress_count = 0
        not_started_count = 0

        for video in all_videos:

            progress = progresses.filter(
                vedio_content=video
            ).first()

            print(
                "Video:",
                video.id,
                "Progress User:",
                progress.user.id if progress else None
            )

            if progress is None:
                not_started_count += 1

            elif progress.is_completed:
                watched_count += 1

            elif progress.current_duration > 0:
                in_progress_count += 1

            else:
                not_started_count += 1

        return Response({
            "total_videos": all_videos.count(),
            "watched_count": watched_count,
            "in_progress_count": in_progress_count,
            "not_started_count": not_started_count,
        })



class LibraryDashboardAPIView(APIView):
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print("Dashboard User:", request.user.id)
        print("Dashboard Email:", request.user.email)
        user = request.user

        modules = Module.objects.prefetch_related(
            Prefetch(
                "vedio",
                queryset=VideoContent.objects.prefetch_related(
                    Prefetch(
                        "progresses",
                        queryset=VedioProgress.objects.filter(user=user)
                    )
                ),
            )
        )

        total_videos = 0
        completed_videos = 0
        in_progress_videos = 0
        not_started_videos = 0

        topics = []

        for module in modules:

            module_total = module.vedio.count()
            module_completed = 0

            for video in module.vedio.all():

                total_videos += 1

                progress = next(iter(video.progresses.all()), None)

                if progress is None:
                    not_started_videos += 1

                elif progress.is_completed:
                    completed_videos += 1
                    module_completed += 1

                elif progress.current_duration > 0:
                    in_progress_videos += 1

                else:
                    not_started_videos += 1

            percentage = (
                round((module_completed / module_total) * 100)
                if module_total else 0
            )

            topics.append({
                "module_id": module.id,
                "module_name": module.name,
                "logo": (
                    request.build_absolute_uri(module.logo.url)
                    if module.logo else None
                ),
                "progress": f"{module_completed}/{module_total}",
                "percentage": f"{percentage}%"
            })

        def calculate_percentage(count):
            if total_videos == 0:
                return "0%"
            return f"{round((count / total_videos) * 100)}%"

        recent_progresses = (
            VedioProgress.objects.filter(user=user)
            .select_related(
                "vedio_content",
                "vedio_content__module"
            )
            .order_by("-updated_at")[:5]
        )

        recently_watched = []

        for progress in recent_progresses:

            watch_percentage = (
                round(
                    (progress.current_duration / progress.total_duration) * 100
                )
                if progress.total_duration
                else 0
            )

            recently_watched.append({
                "module_id": progress.vedio_content.module.id,
                "module_name": progress.vedio_content.module.name,
                "lesson": progress.vedio_content.title,
                "duration": progress.total_duration,
                "current_duration": progress.current_duration,
                "watched_at": progress.updated_at,
                "status": (
                    "Completed"
                    if progress.is_completed
                    else "In Progress"
                ),
                "completed_percentage": (
                    "100%"
                    if progress.is_completed
                    else f"{watch_percentage}%"
                )
            })

        return Response({
            "success": True,
            "data": {
                "library_summary": {
                    "total_videos": total_videos,

                    "completed": {
                        "progress": f"{completed_videos}/{total_videos}",
                        "percentage": calculate_percentage(completed_videos),
                    },

                    "in_progress": {
                        "progress": f"{in_progress_videos}/{total_videos}",
                        "percentage": calculate_percentage(in_progress_videos),
                    },

                    "not_started": {
                        "progress": f"{not_started_videos}/{total_videos}",
                        "percentage": calculate_percentage(not_started_videos),
                    },
                },

                "topics": topics,

                "recently_watched": recently_watched,
            }
        })
