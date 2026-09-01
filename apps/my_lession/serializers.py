from rest_framework import serializers
from apps.my_lession.models import Module, VideoContent, Resources,VedioProgress
from django.contrib.contenttypes.models import ContentType



class VideoBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoContent
        fields = ["id", "title", "description", "thumbnail"]


class ModuleSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="name")
    total_topic = serializers.SerializerMethodField()
    videos = VideoBasicSerializer(
        source="vedio", many=True
    )

    class Meta:
        model = Module
        fields = [
            "id",
            "title",
            "logo",
            "total_topic",
            "videos"
        ]

    def get_total_topic(self, obj):
        total = obj.vedio.count()

        watched = 2  

        if watched > total:
            watched = total  
        return f"{watched}/{total}"


class ResourceSerializer(serializers.ModelSerializer):
    object_type = serializers.SerializerMethodField()
    object_name = serializers.SerializerMethodField()

    class Meta:
        model = Resources
        fields = [
            "id",
            "source_object_id",
            "object_type",
            "object_name",
        ]

    def get_object_type(self, obj):
        return obj.source_content_type.model if obj.source_content_type else None

    def get_object_name(self, obj):
        return str(obj.source_object) if obj.source_object else None


class VideoDetailsSerializer(serializers.ModelSerializer):
    module = serializers.PrimaryKeyRelatedField(queryset=Module.objects.all())
    resources = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    class Meta:
        model = VideoContent
        fields = [
            "id",
            "module",
            "serial_number",
            "title",
            "thumbnail",
            "description",
            "video_url",
            "overview",
            "resources",
            "progress" 

        ]
        read_only_fields = ["id", "serial_number", "resources"]

    def get_resources(self, obj):

        content_type = ContentType.objects.get_for_model(VideoContent)

        resources = Resources.objects.filter(
            content_type=content_type,
            object_id=obj.id
        )

        return ResourceSerializer(resources, many=True).data
    
    def get_progress(self, obj):
        try:
            progress = obj.vedio_progress
            return {
                "total_duration": progress.total_duration,
                "current_duration": progress.current_duration,
                "is_completed": progress.is_completed
            }
        except:
            return {
                "total_duration": 0,
                "current_duration": 0,
                "is_completed": False
            }


class VedioProgressSerializer(serializers.ModelSerializer):

    class Meta:
        model = VedioProgress
        fields = [
            'id',
            'vedio_content',
            'total_duration',
            'current_duration'
          
        ]
