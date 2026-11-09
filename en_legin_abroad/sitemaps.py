from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import EnArticle, EnSection
from .publishing import CONTENT


class CanonicalSitemap(Sitemap):
    @property
    def protocol(self):
        return urlsplit(settings.SITE_ORIGIN).scheme

    def get_domain(self, site=None):
        return urlsplit(settings.SITE_ORIGIN).netloc


class PageSitemap(CanonicalSitemap):
    def items(self):
        return ("en_index", "en_sections", "en_about", "en_privacy", *(tool["route"] for tool in CONTENT["tools"].values()))

    def location(self, item):
        return reverse(f"en_legin_abroad:{item}")


class SectionSitemap(CanonicalSitemap):
    def items(self):
        return EnSection.objects.filter(enarticle__status="published").distinct().order_by("pk")


class ArticleSitemap(CanonicalSitemap):
    def items(self):
        return EnArticle.published.select_related("section").order_by("pk")
