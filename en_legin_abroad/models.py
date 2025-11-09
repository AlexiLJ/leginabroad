from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.urls import reverse
from imagekit.models import ProcessedImageField
from imagekit.processors import Thumbnail
from taggit.managers import TaggableManager


class EnSection(models.Model):
    """Section of the blog"""
    name = models.CharField(max_length=70)
    sslug = models.SlugField(unique=True)
    date_added = models.DateTimeField(auto_now_add=True)
    thumb = ProcessedImageField(upload_to='thumbs_/%Y/%m/',
                                processors=[Thumbnail(800, 458)],
                                blank=True,
                                null=True,
                                format='PNG',
                                options={'quality': 90},
                                )
    description = RichTextUploadingField(blank=True, null=True,
                                         config_name='default',
                                         external_plugin_resources=[(
                                             'youtube',
                                             '/static/youtube/youtube/',
                                             'plugin.js',
                                            )],
                                         )

    def __str__(self):
        """returns string rev. of the model"""
        return self.name

    def get_absolute_url(self):
        return reverse('en_legin_abroad:en_section', kwargs={'sslug': self.sslug})



class EnPublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status='published')


class EnArticle(models.Model):
    """Articles  under section """
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
    )
    section = models.ForeignKey(EnSection, on_delete=models.CASCADE, null=False, blank=False)
    topic = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=False)
    body = RichTextUploadingField(blank=True, null=True,
                                  config_name='default',
                                  external_plugin_resources=[(
                                      'youtube',
                                      '/static/youtube/youtube/',
                                      'plugin.js',
                                  )],
                                  )
    date_added = models.DateTimeField()

    thumb = ProcessedImageField(upload_to='thumbs_/%Y/%m/',
                                processors=[Thumbnail(800, 458)],
                                blank=True,
                                null=True,
                                format='PNG',
                                options={'quality': 90},
                                )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    objects = models.Manager()  # The default manager.
    published = EnPublishedManager()  # custom manager.
    tags = TaggableManager()

    class Meta:
        verbose_name_plural = 'en_articles'

    def __str__(self):
        """returns string rev. of the model"""
        return self.body[:200] + "..."

    def get_absolute_url(self):
        return reverse('en_legin_abroad:en_article', kwargs={'sslug': self.section.sslug, 'slug': self.slug})
