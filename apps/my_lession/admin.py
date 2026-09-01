from django.contrib import admin
import json

from django import forms
from django.contrib.contenttypes.models import ContentType
from unfold.admin import GenericTabularInline, ModelAdmin
from unfold.widgets import UnfoldAdminSelectWidget

from apps.core_learning.models import LearningContent
from apps.flashcard.models import Card
from apps.my_lession.models import Module, VideoContent, Resources, VedioProgress
from apps.nclex.models import Exam


RESOURCE_MODELS = (Card, LearningContent, Exam)
RESOURCE_MODEL_LABELS = {
    Card: "Flash Card",
    LearningContent: "Learning Content",
    Exam: "Exam",
}


def get_resource_content_types():
    content_types = ContentType.objects.get_for_models(
        *RESOURCE_MODELS,
        for_concrete_models=False,
    )
    ids = [content_types[model].id for model in RESOURCE_MODELS]
    return ContentType.objects.filter(id__in=ids).order_by("app_label", "model")


def get_resource_object_map():
    content_types = ContentType.objects.get_for_models(
        *RESOURCE_MODELS,
        for_concrete_models=False,
    )
    object_map = {}

    for model in RESOURCE_MODELS:
        content_type = content_types[model]
        object_map[str(content_type.id)] = [
            [str(obj.pk), str(obj)]
            for obj in model.objects.all().order_by("pk")
        ]

    return object_map


def get_resource_type_label(content_type):
    model = content_type.model_class()
    return RESOURCE_MODEL_LABELS.get(model, str(content_type))


class ResourcesInlineForm(forms.ModelForm):
    source_content_type = forms.ModelChoiceField(
        queryset=ContentType.objects.none(),
        label="Resource type",
        widget=UnfoldAdminSelectWidget(
            attrs={"class": "js-resource-content-type"}
        ),
    )
    source_object_id = forms.ChoiceField(
        label="Resource object",
        widget=UnfoldAdminSelectWidget(
            attrs={"class": "js-resource-object-id"}
        ),
    )

    class Meta:
        model = Resources
        fields = ("source_content_type", "source_object_id")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        object_map = get_resource_object_map()

        self.fields["source_content_type"].queryset = get_resource_content_types()
        self.fields["source_content_type"].label_from_instance = get_resource_type_label

        selected_content_type = ""
        if self.is_bound:
            selected_content_type = self.data.get(f"{self.prefix}-source_content_type", "")
        elif self.instance and self.instance.pk:
            selected_content_type = self.instance.source_content_type_id or ""

        selected_content_type = str(selected_content_type)
        self.fields["source_object_id"].choices = [
            ("", "---------"),
            *object_map.get(selected_content_type, []),
        ]
        self.fields["source_object_id"].widget.attrs.update({
            "data-resource-objects": json.dumps(object_map),
        })

    def clean(self):
        cleaned_data = super().clean()
        source_content_type = cleaned_data.get("source_content_type")
        source_object_id = cleaned_data.get("source_object_id")

        if not source_content_type and not source_object_id:
            return cleaned_data

        if not source_content_type or not source_object_id:
            raise forms.ValidationError("Select both a resource type and resource object.")

        allowed_content_type_ids = set(
            get_resource_content_types().values_list("id", flat=True)
        )
        if source_content_type.id not in allowed_content_type_ids:
            raise forms.ValidationError("Select a valid resource type.")

        model = source_content_type.model_class()
        if not model.objects.filter(pk=source_object_id).exists():
            raise forms.ValidationError("Select a valid resource object.")

        return cleaned_data

class ResourcesInline(GenericTabularInline):
    model = Resources
    form = ResourcesInlineForm
    ct_field = "content_type"
    ct_fk_field = "object_id"
    fields = ("source_content_type", "source_object_id")
    extra = 1

    class Media:
        js = ("my_lession/admin/resources_inline.js",)

@admin.register(Module)
class ModuleAdmin(ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']

    fieldsets = (
        ('Module Information', {
            'fields': ('name', 'logo')
        }),
    )


@admin.register(VideoContent)
class VideoContentAdmin(ModelAdmin):
    list_display = ['id', 'title', 'module', 'serial_number']
    search_fields = ['title', 'module__name']
    list_filter = ['module']

    readonly_fields = ['serial_number']

    fieldsets = (
        ('Video Information', {
            'fields': (
                'serial_number',
                'module',
                'title',
                'thumbnail',
                'video_url',
                'description',
                'overview',
            )
        }),
    )

    inlines = [ResourcesInline]

@admin.register(Resources)
class ResourcesAdmin(ModelAdmin):
    list_display = (
        "id",
        "content_type",
        "object_id",
        "source_content_type",
        "source_object_id",
    )
    search_fields = (
        "object_id",
        "source_object_id",
    )
    list_filter = (
        "content_type",
        "source_content_type",
    )
    ordering = ("id",)
    inlines = []


@admin.register(VedioProgress)
class VedioProgressAdmin(ModelAdmin):
    list_display = (
        "user",
        "vedio_content",
        "current_duration",
        "total_duration",
        "is_completed",
        "updated_at",
    )
    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "vedio_content__title",
    )
    list_filter = (
        "is_completed",
        "updated_at",
    )
    readonly_fields = (
        "updated_at",
    )
    ordering = ("id",)
    inlines = []

