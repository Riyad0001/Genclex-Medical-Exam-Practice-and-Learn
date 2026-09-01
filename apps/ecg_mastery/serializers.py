from rest_framework import serializers
from apps.ecg_mastery.models import Diagnostic, ECGPage, Dosage


class ECGPageSerializer(serializers.ModelSerializer):
    content_url = serializers.SerializerMethodField()

    class Meta:
        model = ECGPage
        fields = [
            'id',
            'title',
            'content_url',
            'is_saved',
            'user'
        ]

    def get_content_url(self, obj):
        request = self.context.get('request')

        if obj.html_file:
            return request.build_absolute_uri(
                obj.html_file.url
            )
        return None

# ------------------------------ Diagnostic Serializer ------------------------------#
class DiagnosticSerializer(serializers.ModelSerializer):
    content_url = serializers.SerializerMethodField()

    class Meta:
        model = Diagnostic
        fields = [
            'id',
            'title',
            'content_url',
            'title_logo',
            'is_saved',
           

        ]

    def get_content_url(self, obj):
        request = self.context.get('request')

        if obj.html_file:
            return request.build_absolute_uri(
                obj.html_file.url
            )
        return None
    

class DosageSerializer(serializers.ModelSerializer):
    content_url = serializers.SerializerMethodField()

    class Meta:
        model = Dosage
        fields = [
            'id',
            'title',
            'content_url',
            'title_logo',
            'is_saved',
           

        ]

    def get_content_url(self, obj):
        request = self.context.get('request')

        if obj.html_file:
            return request.build_absolute_uri(
                obj.html_file.url
            )
        return None