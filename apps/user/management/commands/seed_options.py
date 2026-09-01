from django.core.management.base import BaseCommand
from apps.user.models import NursingProgram, StateCountry, AboutSource


def get_default_programs():
    return [
        "BSN (Bachelor of Science in Nursing)",
        "ADN (Associate Degree in Nursing)",
        "LPN/LVN Program",
        "Accelerated BSN (ABSN)",
        "MSN / Graduate Entry",
        "RN-to-BSN Bridge",
        "Already Licensed RN (Repeat NCLEX)",
    ]


def get_default_states():
    return [
        "Alabama", "California", "Florida", "Georgia", "Illinois",
        "New York", "North Carolina", "Ohio", "Texas", "Virginia",
        "Washington", "Other US State", "International Student", "Canada",
        "Philippines",
    ]


def get_default_sources():
    return [
        "Google Search", "Instagram", "TikTok", "YouTube", "Facebook",
        "X", "Reddit (r/nursing)", "Friend or Classmate", "Professor / Instructor",
        "Clinical Instructor", "Nursing School Website", "Podcast", "LinkedIn", "Other",
    ]


class Command(BaseCommand):
    help = 'Seed initial options for NursingProgram, StateCountry and AboutSource'

    def handle(self, *args, **options):
        programs = get_default_programs()
        states = get_default_states()
        sources = get_default_sources()

        for p in programs:
            NursingProgram.objects.get_or_create(name=p)

        for s in states:
            StateCountry.objects.get_or_create(name=s)

        for src in sources:
            AboutSource.objects.get_or_create(name=src)

        self.stdout.write(self.style.SUCCESS('Seeded default option data'))
