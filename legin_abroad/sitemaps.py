from django.contrib.sitemaps import Sitemap
from legin_abroad.models import Article, Section
from taggit.models import Tag
from django.urls import reverse
from django.shortcuts import get_object_or_404

class ArticleSitemap(Sitemap):
    priority = 0.9
    def items(self):
        return Article.objects.all().filter(status='published')

class SectionSitemap(Sitemap):

    def items(self):
        return Section.objects.all()

class TagSitemap(Sitemap):

    def items(self, tag_slug=None):
        articles = Article.objects.all().order_by('-date_added').filter(status='published')
        tag = None
        if tag_slug:
            tag = get_object_or_404(Tag, slug=tag_slug)
            articles = articles.filter(tags__in=[tag])

            return articles

class StaticViewSitemap(Sitemap):

    def items(self):
        return['legin_abroad:about']

    def location(self, item):
        return reverse(item)
