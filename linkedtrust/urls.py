"""
URL configuration for linkedtrust project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from website.admin import admin_site
from website.sitemaps import sitemaps, sitemap_index_view, sitemap_xsl
from website import agent_views
from website import indexnow

urlpatterns = [
    path('admin/', admin_site.urls),

    # Agent- & crawler-facing endpoints (must live at the true site root)
    path('sitemap.xml', sitemap_index_view, name='sitemap_index'),
    path('sitemap.xsl', sitemap_xsl, name='sitemap_xsl'),
    path('sitemap-pages.xml', sitemap, {'sitemaps': {'static': sitemaps['static']}, 'template_name': 'sitemap_styled.xml'}, name='sitemap_pages'),
    path('sitemap-work.xml', sitemap, {'sitemaps': {'portfolio': sitemaps['portfolio']}, 'template_name': 'sitemap_styled.xml'}, name='sitemap_work'),
    path('sitemap-services.xml', sitemap, {'sitemaps': {'services': sitemaps['services']}, 'template_name': 'sitemap_styled.xml'}, name='sitemap_services'),
    path('robots.txt', agent_views.robots_txt, name='robots_txt'),
    path('llms.txt', agent_views.llms_txt, name='llms_txt'),
    path('llms-full.txt', agent_views.llms_full_txt, name='llms_full_txt'),
    path('.well-known/api-catalog', agent_views.api_catalog, name='api_catalog'),

    # IndexNow key verification file (must live at the true site root).
    path(f'{settings.INDEXNOW_KEY}.txt', indexnow.key_file, name='indexnow_key'),

    path('', include('website.urls')),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Also serve media at /media/ (without SCRIPT_NAME prefix) for when nginx strips it
    if settings.FORCE_SCRIPT_NAME:
        urlpatterns += static('/media/', document_root=settings.MEDIA_ROOT)