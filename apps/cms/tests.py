from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.cms.models import LandingHero


class CMSTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        LandingHero.objects.create(
            title="NCLEX Prep Platform",
            badge_text="Pass With Confidence",
            description="Test description",
            is_active=True,
        )

    def test_landing_page_endpoint(self):
        response = self.client.get("/api/cms/landing-page/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.data.get("data", response.data)
        self.assertIn("hero", content)
        self.assertEqual(content["hero"]["title"], "NCLEX Prep Platform")

    def test_hero_list_endpoint(self):
        response = self.client.get("/api/cms/hero/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.data.get("data", response.data)
        self.assertGreaterEqual(len(content), 1)
