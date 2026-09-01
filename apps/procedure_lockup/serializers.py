from rest_framework import serializers
from apps.procedure_lockup.models import ProcedureModule, Lecture_Notes


class ProcedureSerializer(serializers.ModelSerializer):
    procedure_html = serializers.SerializerMethodField()
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = ProcedureModule
        fields = [
            'id',
            'title',
            'logo_url',
            'procedure_html',
        ]

    def get_logo_url(self, obj):
        request = self.context.get('request')
        if obj.logo:
            return request.build_absolute_uri(obj.logo.url)
        return None

    def get_procedure_html(self, obj):
        request = self.context.get('request')

        if obj.procedure_html:
            return request.build_absolute_uri(obj.procedure_html.url)

        return None
    


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lecture_Notes
        fields = "__all__"
        read_only_fields = ["user"]

    
class AIFormatSerializer(serializers.Serializer):
    html = serializers.CharField()