from django.contrib import admin
from ckeditor.widgets import CKEditorWidget
from django import forms
from legin_abroad.models import Section, Article
# Register your models here.

#@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name',  'date_added')
    prepopulated_fields = {'sslug': ('name',)} # autofill of sec. slug
admin.site.register(Section, SectionAdmin)

#@admin.register(Aricle)
class ArticleAdmin(admin.ModelAdmin):
    body = forms.CharField(widget=CKEditorWidget())
    list_display = ['topic', 'slug', 'date_added', 'section', 'status']
    list_editable = ['status']
    search_fields = ('topic', 'body', 'slug', 'section')
    ordering = ['-date_added']
    prepopulated_fields = {'slug': ('topic',)}

    list_per_page = 25
    class Meta:
        model = Article
        fields = '__all__'

admin.site.register(Article, ArticleAdmin)
