from rest_framework import serializers
from django.utils.safestring import mark_safe
from .models import LearningCategory, LearningContent, Library, LearningContentIcon
# import timesince
from django.utils.timesince import timesince

class LearningContentSerializer(serializers.ModelSerializer):
    content_file_url = serializers.SerializerMethodField()
    content_cover_url = serializers.SerializerMethodField()
    # category = serializers.StringRelatedField()
    is_saved = serializers.SerializerMethodField()
    is_completed = serializers.SerializerMethodField()
    class Meta:

        model = LearningContent
        fields = [
            "id",
            # "category",
            "content_name",
            "content_file_url",
            "content_cover_url",
            "is_saved",
            "is_completed"
        ]

    def get_content_file_url(self, obj):
        if obj.content_file:
            return self.context['request'].build_absolute_uri(obj.content_file.url)
        return None

    def get_content_cover_url(self, obj):
        if obj.content_cover:
            return self.context['request'].build_absolute_uri(obj.content_cover.url)
        return None
    
    def get_is_saved(self, obj):
        # is_saved true if it is in SavedNotes model
        return obj.saved_notes.exists()

    def get_is_completed(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.progress.filter(user=request.user, is_completed=True).exists()
        return False
    
    
    # validate to get only is_active content
    def validate(self, data):
        if not data.get("is_active", True):
            raise serializers.ValidationError("Content is not active.")
        return data


class LearningCategorySerializer(serializers.ModelSerializer):
    # only get active content
    contents = LearningContentSerializer(many=True, read_only=True)

    class Meta:
        model = LearningCategory
        fields = [
            "id",
            "topic",
            "title",
            "subtitle",
            "description",
            "cover",
            "contents"
        ]
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.cover:
            representation['cover'] = self.context['request'].build_absolute_uri(instance.cover.url)
        else:
            representation['cover'] = None
        return representation

class LibrarySerializer(serializers.ModelSerializer):
    # icon = serializers.SerializerMethodField()
    notes = serializers.SerializerMethodField()
    total_notes = serializers.SerializerMethodField()

    class Meta:
        model = Library
        fields = [
            "id",
            "name",
            "icon",       
            # "icon_data",  
            # "color",
            "notes",
            "total_notes",
        ]
    
    # def get_icon(self, obj):
    #     if obj.icon:
    #         return {
    #             "id": obj.icon.id,
    #             "icon": obj.icon.icon.url if obj.icon else None
    #         }
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['icon'] = {
            "id": instance.icon.id if instance.icon else None,
            "icon": instance.icon.icon.url if instance.icon else None
        }
        return data
    def get_notes(self, obj):
        notes = obj.notes.all()
        return [
            {
                "id": note.id,
                "content_id": note.content.id,
                "content_name": note.content.content_name,
                "added": f"{timesince(note.created_at)} ago"
            }
            for note in notes
        ]

    def get_total_notes(self, obj):
        return obj.notes.count()
    