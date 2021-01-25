from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, re_path, include
from django.contrib.sitemaps.views import sitemap
from legin_abroad.sitemaps import ArticleSitemap, StaticViewSitemap, SectionSitemap #, TagSitemap
from legin_abroad import views as la_views
from django.views.static import serve


#from . import views

sitemaps = {
	'static': StaticViewSitemap,
	'article': ArticleSitemap,
	'section': SectionSitemap,
}

urlpatterns = [
    path('admin_LA/', admin.site.urls),
    path('en/', include('en_legin_abroad.urls')),
    path('', include('legin_abroad.urls')),
    
    path('sitemap.xml', sitemap, {'sitemaps':sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('ckeditor/', include('ckeditor_uploader.urls')),

]



urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
