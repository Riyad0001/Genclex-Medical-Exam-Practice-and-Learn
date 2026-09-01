from django.core.management.base import BaseCommand
from apps.new_nclex.models import NCLEXExam, NCLEXQuestion


class Command(BaseCommand):
    help = "Seed the 5 standard NCLEX Final Exams matching the client simulator design."

    def handle(self, *args, **options):
        all_questions = list(NCLEXQuestion.objects.all())
        total_available = len(all_questions)

        exams_data = [
            {
                "order": 1,
                "title": "NCLEX Practice Exam 1",
                "subtitle": "Diagnostic Assessment",
                "tag": "Start Here",
                "level": "Foundational",
                "total_question": 85,
                "time_limit_mins": 150,
            },
            {
                "order": 2,
                "title": "NCLEX Practice Exam 2",
                "subtitle": "Targeted Review",
                "tag": "",
                "level": "Progressive",
                "total_question": 85,
                "time_limit_mins": 150,
            },
            {
                "order": 3,
                "title": "NCLEX Practice Exam 3",
                "subtitle": "Advanced Application",
                "tag": "Up next",
                "level": "Progressive",
                "total_question": 85,
                "time_limit_mins": 150,
            },
            {
                "order": 4,
                "title": "NCLEX Practice Exam 4",
                "subtitle": "Comprehensive",
                "tag": "",
                "level": "Advanced",
                "total_question": 85,
                "time_limit_mins": 150,
            },
            {
                "order": 5,
                "title": "NCLEX Practice Exam 5",
                "subtitle": "Pass Prediction",
                "tag": "Pass Predictor",
                "level": "Expert",
                "total_question": 85,
                "time_limit_mins": 150,
            },
        ]

        for data in exams_data:
            exam, created = NCLEXExam.objects.update_or_create(
                order=data["order"],
                defaults={
                    "title": data["title"],
                    "subtitle": data["subtitle"],
                    "tag": data["tag"],
                    "level": data["level"],
                    "total_question": data["total_question"],
                    "time_limit_mins": data["time_limit_mins"],
                    "is_active": True,
                },
            )
            # Assign questions to exam
            if all_questions:
                # If we have 75+ questions, assign up to total_question, or assign all available
                exam.questions.set(all_questions[:data["total_question"]] if total_available >= data["total_question"] else all_questions)
            
            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{action} {exam.title} (Order {exam.order}, {exam.questions.count()} questions assigned)"))

        self.stdout.write(self.style.SUCCESS("Successfully seeded all 5 NCLEX Final Exams."))
