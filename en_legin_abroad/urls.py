from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static

from . import views

app_name = 'en_legin_abroad'

urlpatterns = [

	path('', views.index, name='en_index'),
	path('search', views.SearchView.as_view(), name='en_search'),
	path('sections/search', views.SearchView.as_view(), name='en_search'),
	path('<slug:sslug>/search', views.SearchView.as_view(), name='en_search'),
	path('tag/<slug:tag_slug>/search', views.tag_search, name='en_search'),
	
	path('sections/<slug:sslug>', views.section, name='en_section'),  #Sections url
	path('sections', views.SectionsListView.as_view(), name='en_sections'),
	

	
	path('tag/<slug:tag_slug>/', views.index, name='en_article_by_tag'),
	path('about', views.about, name='en_about'),
	path('<slug:sslug>/<slug:slug>', views.ArticleDetailView.as_view(), name='en_article'),

]

if settings.DEBUG:
	urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
