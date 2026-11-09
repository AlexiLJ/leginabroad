from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.urls import path
from django.views.generic import TemplateView

from . import views
from .prague_budget import prague_cost_of_living
from .sitemaps import ArticleSitemap, PageSitemap, SectionSitemap

app_name = "en_legin_abroad"

urlpatterns = [
    path("healthz/", views.health_check, name="health_check"),
    path("", views.index, name="en_index"),
    path("ads.txt", views.ads_txt, name="ads_txt"),
    path("robots.txt", views.robots_txt, name="robots_txt"),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": {"pages": PageSitemap, "sections": SectionSitemap, "articles": ArticleSitemap}},
        name="sitemap",
    ),
    path("search", views.SearchView.as_view(), name="en_search"),
    path("sections/search", views.SearchView.as_view(), name="en_search"),
    path("<slug:sslug>/search", views.SearchView.as_view(), name="en_search"),
    path("tag/<slug:tag_slug>/search", views.tag_search, name="en_search"),
    path("sections/<slug:sslug>", views.section, name="en_section"),  # Sections url
    path("sections", views.SectionsListView.as_view(), name="en_sections"),
    path("tag/<slug:tag_slug>/", views.index, name="en_article_by_tag"),
    path("about", views.about, name="en_about"),
    path("privacy/", TemplateView.as_view(template_name="en_legin_abroad/en_privacy.html"), name="en_privacy"),
    path("prague-cost-of-living/", prague_cost_of_living, name="prague_cost_of_living"),
    path("<slug:sslug>/<slug:slug>", views.ArticleDetailView.as_view(), name="en_article"),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
