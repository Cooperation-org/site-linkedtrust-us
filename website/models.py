from django.db import models
from django.utils.text import Truncator, slugify


class TeamMember(models.Model):
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='team/')
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2, help_text="Hourly rate in USD")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def truncated_description(self):
        return Truncator(self.description).words(15, truncate='...')

    def formatted_hourly_rate(self):
        return int(self.hourly_rate)

    def __str__(self):
        return self.name


class PortfolioProject(models.Model):
    CATEGORY_CHOICES = [
        ('client_work', 'Client Work'),
        ('internal_product', 'Internal Product'),
        ('open_source', 'Open Source'),
        ('research', 'Research'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    client_name = models.CharField(max_length=200, blank=True)
    short_description = models.CharField(max_length=300, help_text="One-liner for card display")
    full_description = models.TextField(blank=True, help_text="Full project description for detail page")
    hero_image = models.ImageField(upload_to='portfolio/', blank=True)
    thumbnail_image = models.ImageField(upload_to='portfolio/thumbs/', blank=True)
    demo_url = models.URLField(blank=True)
    repo_url = models.URLField(blank=True)
    tech_tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated: React, Django, FastAPI")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='client_work')
    featured = models.BooleanField(default=False, help_text="Show on homepage")
    sort_order = models.IntegerField(default=0, help_text="Lower = appears first")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', '-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_tech_list(self):
        return [t.strip() for t in self.tech_tags.split(',') if t.strip()]

    def __str__(self):
        return self.title


class CaseStudy(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    project = models.OneToOneField(PortfolioProject, on_delete=models.CASCADE, related_name='case_study')
    problem_text = models.TextField(help_text="What was the problem?")
    solution_text = models.TextField(help_text="What did we build?")
    result_text = models.TextField(help_text="What was the outcome?")
    hero_image = models.ImageField(upload_to='case_studies/', blank=True)
    client_quote = models.TextField(blank=True)
    client_name = models.CharField(max_length=100, blank=True)
    client_title = models.CharField(max_length=200, blank=True)
    metrics = models.JSONField(blank=True, default=dict, help_text='e.g. {"cost_saved": "40%", "time": "2 weeks"}')
    featured = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order', '-created_at']
        verbose_name_plural = 'Case studies'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Testimonial(models.Model):
    PLACEMENT_CHOICES = [
        ('hero', 'Hero (top of homepage, row layout)'),
        ('homepage', 'Homepage (below hero)'),
        ('wall', 'Badge Wall page'),
        ('page', 'Specific project page only'),
    ]
    LAYOUT_CHOICES = [
        ('row', 'Row (horizontal rectangle — good for stacking)'),
        ('card', 'Card (vertical — good for standalone)'),
    ]

    person_name = models.CharField(max_length=100)
    person_title = models.CharField(max_length=200, blank=True)
    person_image = models.ImageField(upload_to='testimonials/', blank=True)
    quote_text = models.TextField()
    linked_claim_id = models.CharField(max_length=50, blank=True, help_text="LinkedTrust claim ID for badge embed")
    has_video = models.BooleanField(default=False)
    project = models.ForeignKey(PortfolioProject, on_delete=models.SET_NULL, null=True, blank=True, related_name='testimonials')
    featured = models.BooleanField(default=False, help_text="Show on homepage")
    placement = models.CharField(max_length=20, choices=PLACEMENT_CHOICES, default='homepage', help_text="Where this badge appears on the site")
    badge_layout = models.CharField(max_length=10, choices=LAYOUT_CHOICES, default='row', help_text="Badge display layout")
    badge_theme = models.CharField(max_length=10, choices=[('dark', 'Dark'), ('light', 'Light')], default='dark', help_text="Badge color theme")
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', '-created_at']

    def __str__(self):
        return f"{self.person_name} — {self.person_title}"


class ServicePackage(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Emoji or icon class")
    short_description = models.CharField(max_length=300, help_text="One-liner for card display")
    full_description = models.TextField(blank=True, help_text="Full description for detail page")
    price_range = models.CharField(max_length=100, blank=True, help_text='e.g. "$1.5K-3K"')
    example_projects = models.ManyToManyField(PortfolioProject, blank=True, related_name='service_packages')
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sort_order']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ContactInquiry(models.Model):
    SUBJECT_CHOICES = [
        ('consulting', 'Consulting'),
        ('site_issue', 'Site Issue'),
        ('developer', 'Developer question'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=150, blank=True)
    email = models.EmailField()
    subject = models.CharField(max_length=30, choices=SUBJECT_CHOICES, default='consulting')
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Contact inquiries'

    def __str__(self):
        return f"{self.email} — {self.get_subject_display()} ({self.created_at:%Y-%m-%d})"