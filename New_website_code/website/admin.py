from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html
from django.db.models import Avg, Sum
from django.utils import timezone
from datetime import timedelta
from .models import TeamMember, PortfolioProject, CaseStudy, Testimonial, ServicePackage

class LinkedtrustAdminSite(AdminSite):
    site_header = 'Linkedtrust Administration'
    site_title = 'Linkedtrust Admin Portal'
    index_title = 'Welcome to Linkedtrust Admin Portal'

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Get the date 7 days ago
        week_ago = timezone.now() - timedelta(days=7)
        
        extra_context.update({
            'team_count': TeamMember.objects.count(),
            'avg_rate': TeamMember.objects.aggregate(Avg('hourly_rate'))['hourly_rate__avg'] or 0,
            'recent_updates': TeamMember.objects.order_by('-updated_at')[:5],
            
            # Team member statistics
            'active_members': TeamMember.objects.filter(updated_at__gte=week_ago).count(),
            'total_team_value': TeamMember.objects.aggregate(total=Sum('hourly_rate'))['total'] or 0,
            
            # Recent activity
            'recent_members': TeamMember.objects.order_by('-created_at')[:5],
        })
        return super().index(request, extra_context=extra_context)

# Create the admin site instance
admin_site = LinkedtrustAdminSite(name='linkedtrust_admin')

# Create the TeamMemberAdmin class
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'title', 'display_image', 'hourly_rate', 'created_at', 'truncated_description']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['name', 'title', 'description']
    readonly_fields = ['created_at', 'updated_at', 'display_image']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'title', 'image', 'display_image')
        }),
        ('Details', {
            'fields': ('description', 'hourly_rate')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%;" />', obj.image.url)
        return "No image"
    display_image.short_description = 'Profile Picture'

    def truncated_description(self, obj):
        return obj.truncated_description
    truncated_description.short_description = 'Description'

    # Custom actions
    actions = ['reset_hourly_rate']

    def reset_hourly_rate(self, request, queryset):
        queryset.update(hourly_rate=0)
    reset_hourly_rate.short_description = "Reset hourly rate to 0"

# --- PortfolioProject ---
class CaseStudyInline(admin.StackedInline):
    model = CaseStudy
    extra = 0

class TestimonialInline(admin.TabularInline):
    model = Testimonial
    extra = 0
    fields = ['person_name', 'person_title', 'quote_text', 'linked_claim_id', 'featured']

class PortfolioProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'client_name', 'category', 'featured', 'sort_order', 'display_thumb']
    list_filter = ['category', 'featured']
    list_editable = ['featured', 'sort_order']
    search_fields = ['title', 'client_name', 'short_description', 'tech_tags']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [CaseStudyInline, TestimonialInline]

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'client_name', 'category', 'featured', 'sort_order')
        }),
        ('Content', {
            'fields': ('short_description', 'full_description', 'tech_tags')
        }),
        ('Images', {
            'fields': ('hero_image', 'thumbnail_image')
        }),
        ('Links', {
            'fields': ('demo_url', 'repo_url')
        }),
    )

    def display_thumb(self, obj):
        if obj.thumbnail_image:
            return format_html('<img src="{}" width="60" height="40" style="border-radius:4px;object-fit:cover;" />', obj.thumbnail_image.url)
        return "—"
    display_thumb.short_description = 'Thumbnail'


# --- CaseStudy ---
class CaseStudyAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'featured', 'sort_order']
    list_filter = ['featured']
    list_editable = ['featured', 'sort_order']
    search_fields = ['title', 'problem_text', 'solution_text', 'result_text']
    prepopulated_fields = {'slug': ('title',)}


# --- Testimonial ---
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['person_name', 'person_title', 'project', 'linked_claim_id', 'has_video', 'featured', 'sort_order']
    list_filter = ['featured', 'has_video']
    list_editable = ['featured', 'sort_order']
    search_fields = ['person_name', 'quote_text']


# --- ServicePackage ---
class ServicePackageAdmin(admin.ModelAdmin):
    list_display = ['title', 'price_range', 'is_active', 'sort_order']
    list_filter = ['is_active']
    list_editable = ['is_active', 'sort_order']
    search_fields = ['title', 'short_description']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['example_projects']


# Register with custom admin site
admin_site.register(TeamMember, TeamMemberAdmin)
admin_site.register(PortfolioProject, PortfolioProjectAdmin)
admin_site.register(CaseStudy, CaseStudyAdmin)
admin_site.register(Testimonial, TestimonialAdmin)
admin_site.register(ServicePackage, ServicePackageAdmin)