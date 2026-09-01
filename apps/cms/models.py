from django.db import models


class LandingHero(models.Model):
    """
    Hero section for the landing page.
    """
    badge_text = models.CharField(
        max_length=255,
        default="NCLEX-RN & NCLEX-PN Prep Platform. Pass With Confidence — The First Time ✨"
    )
    title = models.CharField(
        max_length=255,
        default="NCLEX-RN & NCLEX-PN Prep Platform."
    )
    title_highlight = models.CharField(
        max_length=255,
        blank=True,
        default="Pass With Confidence — The First Time ✨"
    )
    description = models.TextField(
        default="Prepare smarter with comprehensive question banks, Next Gen clinical cases, high-yield nursing notes, personalized study plans, and an AI nursing tutor available whenever you need help."
    )
    badge_tags = models.JSONField(
        default=list,
        blank=True,
        help_text="List of feature tags shown below description e.g. ['AI Academic Interactive Planner', 'Access 24/7', 'Core Study Plans']"
    )
    primary_cta_text = models.CharField(max_length=100, default="Get Started Free")
    primary_cta_link = models.CharField(max_length=255, default="/auth")
    secondary_cta_text = models.CharField(max_length=100, default="See How It Works")
    secondary_cta_link = models.CharField(max_length=255, default="#how-it-works")
    trust_text = models.CharField(max_length=255, default="No credit card required • Cancel anytime")
    hero_image = models.ImageField(upload_to="cms/hero/", null=True, blank=True)
    floating_features = models.JSONField(
        default=list,
        blank=True,
        help_text="Annotations on hero graphic: [{'title': '...', 'description': '...'}]"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Landing Hero Section"
        verbose_name_plural = "Landing Hero Sections"

    def __str__(self):
        return f"Hero Section ({'Active' if self.is_active else 'Inactive'})"


class LandingStatsBanner(models.Model):
    """
    Banner section with stats and pills.
    """
    title = models.CharField(max_length=255, default="Everything You Need to Pass the NCLEX")
    pills = models.JSONField(
        default=list,
        blank=True,
        help_text="Pills list e.g. ['NCLEX-RN & PN Prep', 'Next Gen Questions', 'AI Tutor 24/7', 'Personalized Study Plans']"
    )
    stats = models.JSONField(
        default=list,
        blank=True,
        help_text="Stats array: [{'value': '40K+', 'label': 'Active Students'}, {'value': '500K+', 'label': 'Questions Answered'}, ...]"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Landing Stats Banner"
        verbose_name_plural = "Landing Stats Banners"

    def __str__(self):
        return self.title


class AITutorSpotlight(models.Model):
    """
    Spotlight section for AI Tutor feature.
    """
    tag = models.CharField(max_length=100, default="MEET YOUR AI STUDY PARTNER")
    heading = models.CharField(max_length=255, default="AI Tutor That Understands You, In Any Language.")
    description = models.TextField(default="Get instant, accurate explanations on any nursing concept. Our AI Tutor speaks your language—literally.")
    languages = models.JSONField(
        default=list,
        blank=True,
        help_text="Supported languages e.g. [{'name': 'English', 'flag': '🇺🇸'}, {'name': 'Spanish', 'flag': '🇪🇸'}, ...]"
    )
    features = models.JSONField(
        default=list,
        blank=True,
        help_text="Feature cards e.g. [{'title': '24/7 Available', 'description': '...', 'icon': 'clock'}]"
    )
    preview_image = models.ImageField(upload_to="cms/ai_tutor/", null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "AI Tutor Spotlight Section"
        verbose_name_plural = "AI Tutor Spotlight Sections"

    def __str__(self):
        return self.heading


class LandingFeature(models.Model):
    """
    Core features shown under 'Everything You Need to Succeed in Nursing School'.
    """
    step_number = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    bullets = models.JSONField(default=list, blank=True, help_text="List of bullet point strings")
    image = models.ImageField(upload_to="cms/features/", null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "step_number", "id"]
        verbose_name = "Landing Feature"
        verbose_name_plural = "Landing Features"

    def __str__(self):
        return f"{self.step_number}. {self.title}"


class PillarsSection(models.Model):
    """
    '4 Roots of Success' / STEMRN Method framework section.
    """
    tag = models.CharField(max_length=100, default="THE STEMRN METHOD")
    heading = models.CharField(max_length=255, default="4 Roots of Success")
    description = models.TextField(default="Our framework isn't about memorization — it's about building the clinical reasoning NCLEX demands from day one of your career.")
    highlight_badge = models.CharField(max_length=255, default="Get Knowledge. Beat Results. Pass the NCLEX Guaranteed.")
    pillars = models.JSONField(
        default=list,
        blank=True,
        help_text="List of 4 pillars e.g. [{'title': 'Practice', 'description': '...', 'color': 'emerald', 'icon': 'target'}, ...]"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pillars Section (4 Roots of Success)"
        verbose_name_plural = "Pillars Sections"

    def __str__(self):
        return self.heading


class AIToolCard(models.Model):
    """
    Cards for 'Powerful AI Tools for Nursing Students'.
    """
    title = models.CharField(max_length=255)
    description = models.TextField()
    icon = models.CharField(max_length=100, blank=True, help_text="Icon identifier or SVG key")
    image = models.ImageField(upload_to="cms/tools/", null=True, blank=True)
    badge = models.CharField(max_length=50, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "AI Tool Card"
        verbose_name_plural = "AI Tool Cards"

    def __str__(self):
        return self.title
