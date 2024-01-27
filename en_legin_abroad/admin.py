from django.contrib import admin
from ckeditor.widgets import CKEditorWidget
from django import forms

# Register your models here.
from en_legin_abroad.models import EnSection, EnArticle

#@admin.register(Section)
class EnSectionAdmin(admin.ModelAdmin):
    list_display = ('name',  'date_added')
    prepopulated_fields = {'sslug': ('name',)} # autofill of sec. slug
admin.site.register(EnSection, EnSectionAdmin)

#@admin.register(Aricle)

class EnArticleAdmin(admin.ModelAdmin):
    body = forms.CharField(widget=CKEditorWidget())
    list_display = ['topic', 'slug', 'date_added', 'section', 'status']
    list_editable = ['status']
    search_fields = ('topic', 'body', 'slug', 'section')
    ordering = ['-date_added']
    prepopulated_fields = {'slug': ('topic',)} #autofill of art. slug
    list_per_page = 25
    class Meta:
        model = EnArticle
        fields = '__all__'

admin.site.register(EnArticle, EnArticleAdmin)
