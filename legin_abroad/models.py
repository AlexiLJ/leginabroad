from django.db import models
# from django.utils import timezone
# from django.db.models import Q
from django.urls import reverse
from taggit.managers import TaggableManager
from ckeditor_uploader.fields import RichTextUploadingField
from ckeditor.fields import RichTextField
from imagekit.models import ImageSpecField, ProcessedImageField
from imagekit.processors import ResizeToFill
# Create your models here.

class Section(models.Model):
    """Section if the blog"""
    name = models.CharField(max_length=70)
    sslug = models.SlugField(unique=True)
    date_added = models.DateTimeField(auto_now_add=True)
    thumb = ProcessedImageField(upload_to='thumbs_/%Y/%m/',
                                blank=True,
                                null=True,
                                format='PNG',
                                options={'quality': 100}
                                )
    description = RichTextUploadingField(blank=True, null=True,
                                         external_plugin_resources=[(
                                             'youtube',
                                             '/static/youtube/youtube/',
                                             'plugin.js',
                                         )],
                                         )

    def get_absolute_url(self):
        return reverse('legin_abroad:section', kwargs={'sslug': self.sslug})

    def __str__(self):
        '''returns string rev. of the model'''
        return self.name


class PublishedManager(models.Manager):
    def get_queryset(self):
        return super(PublishedManager, self).get_queryset().filter(status='published')


class Article(models.Model):
    """Articles  under section """
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
    )
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=False, blank=False)
    topic = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=False)
    # image_load = models.ImageField(upload_to='uploads/', null=True, blank=True)
    body = RichTextUploadingField(blank=True, null=True,
                                  external_plugin_resources=[(
                                      'youtube',
                                      '/static/youtube/youtube/',
                                      'plugin.js',
                                  )]
                                  )
    date_added = models.DateTimeField()

    thumb = ProcessedImageField(upload_to='thumbs_/%Y/%m/',
                                processors=[ResizeToFill(800, 458)],
                                blank=True,
                                null=True,
                                format='PNG',
                                options={'quality': 100}
                                )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    objects = models.Manager()  # The default manager.
    published = PublishedManager()  # custom manager.
    tags = TaggableManager()

    class Meta:
        verbose_name_plural = 'articles'

    def __str__(self):
        '''returns string rev. of the model'''
        return self.body[:200] + "..."

    def get_absolute_url(self):
        return reverse('legin_abroad:article', kwargs={'sslug': self.section.sslug, 'slug': self.slug})

# class ArticleImage(models.Model):
#     article = models.ForeignKey(Article, on_delete=models.CASCADE, null=True)
#
#     image = models.ImageField(upload_to='uploads/')



