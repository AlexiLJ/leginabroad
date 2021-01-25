from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from . import views

app_name = 'legin_abroad'
urlpatterns = [

	path('', views.index, name='index'),	
	path('search', views.SearchView.as_view(), name='search'),
	path('sections/search', views.SearchView.as_view(), name='search'),
	path('<slug:sslug>/search', views.SearchView.as_view(), name='search'),
	path('tag/<slug:tag_slug>/search', views.tag_search, name='search'),
	path('sections/<slug:sslug>', views.section, name='section'),#Sections url
	path('sections', views.SectionsListView.as_view(), name='sections'),
	path('about', views.about, name='about'),
	path('tag/<slug:tag_slug>/', views.index, name='article_by_tag'),
	path('<slug:sslug>/<slug:slug>', views.ArticleDetailView.as_view(), name='article'),
]

if settings.DEBUG:
	urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
