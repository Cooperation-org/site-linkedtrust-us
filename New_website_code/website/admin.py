from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html
from django.db.models import Avg, Sum  # Add Sum here
from django.utils import timezone
from datetime import timedelta
from .models import TeamMember

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

# Register with custom admin site
admin_site.register(TeamMember, TeamMemberAdmin)