# Generated manually on 2026-06-15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("my_lession", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="resources",
            name="resource_link",
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
    ]
