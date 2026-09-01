from django.core.management.base import BaseCommand
from apps.cms.models import (
    LandingHero,
    LandingStatsBanner,
    AITutorSpotlight,
    LandingFeature,
    PillarsSection,
    AIToolCard,
)


class Command(BaseCommand):
    help = "Seed CMS landing page content"

    def handle(self, *args, **options):
        self.stdout.write("Seeding CMS landing page data...")

        # 1. Hero Section
        LandingHero.objects.update_or_create(
            is_active=True,
            defaults={
                "badge_text": "NCLEX-RN & NCLEX-PN Prep Platform. Pass With Confidence — The First Time ✨",
                "title": "NCLEX-RN & NCLEX-PN Prep Platform.",
                "title_highlight": "Pass With Confidence — The First Time ✨",
                "description": "Prepare smarter with comprehensive question banks, Next Gen clinical cases, high-yield nursing notes, personalized study plans, and an AI nursing tutor available whenever you need help.",
                "badge_tags": [
                    "AI Academic Interactive Planner",
                    "Access 24/7",
                    "Core Study Plans",
                ],
                "primary_cta_text": "Get Started Free",
                "primary_cta_link": "/auth",
                "secondary_cta_text": "See How It Works",
                "secondary_cta_link": "#how-it-works",
                "trust_text": "No credit card required • Cancel anytime",
                "floating_features": [
                    {
                        "title": "Academic Planner",
                        "description": "Auto-syncs your syllabus for auto-scheduled study guides",
                    },
                    {
                        "title": "AI Study Notes",
                        "description": "Transform long lecture notes into study guides",
                    },
                    {
                        "title": "NCLEX Next Gen QBank",
                        "description": "Prepare with 5000+ NGN questions & detailed rationale",
                    },
                    {
                        "title": "AI Tutor 24/7",
                        "description": "Ask questions, get explanations and feedback instantly",
                    },
                    {
                        "title": "Quiz Modules",
                        "description": "Generate custom practice quizzes to test your knowledge",
                    },
                    {
                        "title": "Care Plan Builder",
                        "description": "Formulate complete personalized care plans in seconds",
                    },
                ],
            },
        )

        # 2. Stats Banner
        LandingStatsBanner.objects.update_or_create(
            is_active=True,
            defaults={
                "title": "Everything You Need to Pass the NCLEX",
                "pills": [
                    "NCLEX-RN & PN Prep",
                    "Next Gen Questions",
                    "AI Tutor 24/7",
                    "Personalized Study Plans",
                ],
                "stats": [
                    {"value": "40K+", "label": "Active Students", "icon": "users"},
                    {"value": "500K+", "label": "Questions Answered", "icon": "help-circle"},
                    {"value": "95%", "label": "First-Time Pass Rate", "icon": "award"},
                    {"value": "24/7", "label": "AI Tutor Support", "icon": "clock"},
                ],
            },
        )

        # 3. AI Tutor Spotlight
        AITutorSpotlight.objects.update_or_create(
            is_active=True,
            defaults={
                "tag": "MEET YOUR AI STUDY PARTNER",
                "heading": "AI Tutor That Understands You, In Any Language.",
                "description": "Get instant, accurate explanations on any nursing concept. Our AI Tutor speaks your language—literally.",
                "languages": [
                    {"name": "English", "code": "en", "flag": "🇺🇸"},
                    {"name": "Spanish", "code": "es", "flag": "🇪🇸"},
                    {"name": "German", "code": "de", "flag": "🇩🇪"},
                    {"name": "French", "code": "fr", "flag": "🇫🇷"},
                    {"name": "Chinese", "code": "zh", "flag": "🇨🇳"},
                    {"name": "Hindi", "code": "hi", "flag": "🇮🇳"},
                ],
                "features": [
                    {
                        "title": "24/7 Available",
                        "description": "Get instant help anytime, day or night.",
                        "icon": "clock",
                    },
                    {
                        "title": "Evidence-Based",
                        "description": "Trained on nursing curriculum & NCLEX standards.",
                        "icon": "check-shield",
                    },
                    {
                        "title": "Personalized",
                        "description": "Adapts to your learning style and pace.",
                        "icon": "user-check",
                    },
                ],
            },
        )

        # 4. Features
        features_data = [
            {
                "step_number": 1,
                "title": "Academic Planner",
                "subtitle": "Upload your syllabus, AI builds your entire semester plan.",
                "description": "Upload your syllabus (PDF) and our AI automatically extracts key exam dates, study schedule, topic outlines, quiz deadlines, and links them to topic study resources.",
                "bullets": [
                    "Automatically builds study guides",
                    "AI-generated full unit schedules",
                    "Visual timeline and task tracking",
                    "Direct access to study resources",
                ],
                "order": 1,
            },
            {
                "step_number": 2,
                "title": "Lecture Notes",
                "subtitle": "Turn your raw notes into structured study notes.",
                "description": "Upload raw notes, video transcriptions, audio/lecture records, charts, and diagrams. AI turns your content into structured study notes automatically.",
                "bullets": [
                    "Upload raw text or audio recordings",
                    "Auto-generated key points",
                    "Smart summary & key vocabulary",
                    "Download or share study notes",
                ],
                "order": 2,
            },
            {
                "step_number": 3,
                "title": "NCLEX Next Gen QBank",
                "subtitle": "Practice course with Next Gen questions & detailed rationales.",
                "description": "Practice with 5000+ NGN questions (case studies, trend, matrix, dropdown, bow-tie, etc.) with comprehensive answer rationales.",
                "bullets": [
                    "5000+ NGN questions, 100% video rationale",
                    "Detailed rationales for choices",
                    "Diagnostic feedback",
                    "Track progress & improve performance",
                ],
                "order": 3,
            },
        ]

        for item in features_data:
            LandingFeature.objects.update_or_create(
                step_number=item["step_number"],
                defaults=item,
            )

        # 5. Pillars Section
        PillarsSection.objects.update_or_create(
            is_active=True,
            defaults={
                "tag": "THE STEMRN METHOD",
                "heading": "4 Roots of Success",
                "description": "Our framework isn't about memorization — it's about building the clinical reasoning NCLEX demands from day one of your career.",
                "highlight_badge": "Get Knowledge. Beat Results. Pass the NCLEX Guaranteed.",
                "pillars": [
                    {
                        "number": 1,
                        "title": "Practice",
                        "description": "5000+ NCLEX questions with NGN format cases: item types (multiple response, matrix, bow-tie, NGN case studies). Detailed rationale behind every answer.",
                        "color": "emerald",
                        "icon": "target",
                    },
                    {
                        "number": 2,
                        "title": "Knowledge",
                        "description": "Take advantage of our AI smart tutor, topic summaries, nurse Q/A generators, diagnostic tests, auto-assessment, remediation plan.",
                        "color": "rose",
                        "icon": "brain",
                    },
                    {
                        "number": 3,
                        "title": "Strategy",
                        "description": "The exact system to approach a question, test-taking strategies, NCLEX rules, safety, prioritization, select-all-apply.",
                        "color": "blue",
                        "icon": "shield",
                    },
                    {
                        "number": 4,
                        "title": "Organization",
                        "description": "Upload your syllabus, calendar, track your study plan. Thanks to auto-sync, system handles the rest.",
                        "color": "purple",
                        "icon": "folder",
                    },
                ],
            },
        )

        # 6. AI Tool Cards
        ai_tools_data = [
            {
                "title": "Case Studies",
                "description": "Practice real clinical scenarios with interactive question formats.",
                "icon": "briefcase",
                "order": 1,
            },
            {
                "title": "Notes to Flashcards",
                "description": "Convert your lecture notes into flashcards instantly.",
                "icon": "cards",
                "order": 2,
            },
            {
                "title": "Notes to Quiz",
                "description": "Turn notes into custom practice quizzes for active recall.",
                "icon": "quiz",
                "order": 3,
            },
            {
                "title": "Drug Cards",
                "description": "Generate comprehensive pharmacology cards with dosage, side effects, and warnings.",
                "icon": "pill",
                "order": 4,
            },
            {
                "title": "Concept Map",
                "description": "Visual nursing concept and care maps in a matter of seconds.",
                "icon": "mindmap",
                "order": 5,
            },
            {
                "title": "Care Plan Builder",
                "description": "Generate complete, evidence-based care plans with nursing diagnosis, goals, & interventions.",
                "icon": "clipboard",
                "order": 6,
            },
        ]

        for tool in ai_tools_data:
            AIToolCard.objects.update_or_create(
                title=tool["title"],
                defaults=tool,
            )

        self.stdout.write(self.style.SUCCESS("Successfully seeded CMS landing page data!"))
