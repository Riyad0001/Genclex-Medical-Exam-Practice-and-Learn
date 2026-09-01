# Generated manually on 2026-06-15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("my_lession", "0002_resources_resource_link"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="resources",
            name="resource_link",
        ),
        migrations.AlterField(
            model_name="resources",
            name="content_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="video_content_resources",
                to="contenttypes.contenttype",
            ),
        ),
        migrations.AddField(
            model_name="resources",
            name="source_content_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="lesson_source_resources",
                to="contenttypes.contenttype",
            ),
        ),
        migrations.AddField(
            model_name="resources",
            name="source_object_id",
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
    ]
