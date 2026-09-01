import os

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile

from apps.core_learning.models import LearningCategory, LearningContent


class Command(BaseCommand):
    help = "Seed LearningCategory and LearningContent safely."

    def handle(self, *args, **kwargs):

        base_dir = os.path.dirname(__file__)
        new_html_path = os.path.join(base_dir, "new.html")

        if not os.path.exists(new_html_path):
            self.stdout.write(
                self.style.ERROR("new.html not found in command folder.")
            )
            return

        with open(new_html_path, "rb") as f:
            new_html = f.read()

        created_count = 0

        CONTENT_NAMES = [
            "Cardiovascular System",
            "Respiratory System",
            "Skeletal System",
            "Gastrointestinal",
            "Nervous System",
            "Muscular System",
            "Degestive System",
    
        ]

        STUDY_NOTE_CATEGORIES = [
            "Medical-Surgical Nursing",
            "Fundamentals Of Nursing",
            "Mental-Newborn Nursing",
            "Pharmacology",
            "Mental Health Nursing",
            "Community & Public Health Nursing",
          
        ]

        BODY_SYSTEM_CATEGORIES = [
            "Cardiovascular System",
            "Respiratory System",
            "Skeletal System",
            "Gastrointestinal",
            "Nervous System",
            "Muscular System",
            "Degestive System",
        ]

        DEFAULT_TOPICS = [
            "ecg",
            "stem_toons",
            "cheat_sheet",
            "dosage_calculation",      # Fix spelling if your DB uses this value
            "nursing_assessment",
        ]

        def create_contents(category):
            nonlocal created_count

            for name in CONTENT_NAMES:
                content, created = LearningContent.objects.get_or_create(
                    category=category,
                    content_name=name,
                )

                if created:
                    content.content_file.save(
                        f"{name.lower().replace(' ', '_')}.html",
                        ContentFile(new_html),
                        save=True,
                    )
                    created_count += 1

        # ----------------------------------------------------
        # Study Notes
        # ----------------------------------------------------
        for title in STUDY_NOTE_CATEGORIES:

            category, _ = LearningCategory.objects.get_or_create(
                topic="study_notes",
                title=title,
                defaults={
                    "subtitle": f"{title} Notes",
                    "description": f"{title} study materials",
                },
            )

            create_contents(category)

        # ----------------------------------------------------
        # Body System
        # ----------------------------------------------------
        for title in BODY_SYSTEM_CATEGORIES:

            category, _ = LearningCategory.objects.get_or_create(
                topic="body_system",
                title=title,
                defaults={
                    "subtitle": f"{title} Body System",
                    "description": f"{title} body system materials",
                },
            )

            create_contents(category)

        # ----------------------------------------------------
        # Remaining Topics
        # ----------------------------------------------------
        for topic in DEFAULT_TOPICS:

            category, _ = LearningCategory.objects.get_or_create(
                topic=topic,
                title="Default",
                defaults={
                    "subtitle": f"{topic.replace('_', ' ').title()}",
                    "description": f"Default category for {topic}",
                },
            )

            create_contents(category)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeding completed successfully. Created {created_count} new contents."
            )
        )