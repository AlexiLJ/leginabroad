from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from taggit.models import Tag
from django.http import Http404
from django.conf import settings
from django.views.generic import View, ListView, DetailView
from django.db.models import Count
from .models import Section, Article
from .forms import SearchForm
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank


def index(request, tag_slug=None):
	"""Home page"""
	sections = Section.objects.all().order_by('date_added')
	section = Section.objects.all()
	articles = Article.objects.all().order_by('-date_added').filter(status='published')
	tag = None

	if tag_slug:
		tag = get_object_or_404(Tag, slug=tag_slug)
		articles = articles.filter(tags__in=[tag])

	paginator = Paginator(articles, 5) # 5 posts on each page
	page = request.GET.get('page')
	
	try:
		articles = paginator.page(page)
	except PageNotAnInteger:
		# If page is not an integer deliver the first page
		articles = paginator.page(1)
	except EmptyPage:
		# If page is out of range deliver last page of results
		articles = paginator.page(paginator.num_pages)

	context = {'sections':sections, 'section':section, 'articles':articles, 'tag':tag}
	
	return render(request, 'legin_abroad/index.html', context)


class SectionsListView(ListView):
	
	model = Section

	def get_context_data(self, **kwargs):
		# Call the base implementation first to get a context
		context = super().get_context_data(**kwargs)
		
		# Add in a QuerySet of all sections
		context['sections'] = Section.objects.all()
		
		return context

	template_name = 'legin_abroad/sections.html'


def section(request, sslug):
	sections = Section.objects.all()
	section = get_object_or_404(Section, sslug=sslug)
	articles = section.article_set.order_by('-date_added').filter(status='published')
	#_set.all() - returns all Article objects related to Section
	paginator = Paginator(articles, 5) # 5 posts in each page
	page = request.GET.get('page')
	try:
		articles = paginator.page(page)
	except PageNotAnInteger:
		# If page is not an integer deliver the first page
		articles = paginator.page(1)
	except EmptyPage:
		# If page is out of range deliver last page of results
		articles = paginator.page(paginator.num_pages)
		
	context = {'sections':sections, 'section':section, 'articles':articles}

	return render(request, 'legin_abroad/section.html', context)

class ArticleDetailView(DetailView):
	model = Article
	'''returns html slug'''
	
	def get(self, request, slug, tag_slug=None, *args, **kwargs):
		# GET method
		context = {}
		article =  get_object_or_404(Article, slug=slug, status='published')
		tag = article.tags.all()
		# List of similar posts
		article_tags_ids = article.tags.values_list('id', flat=True)
		#similar_articles = article.tags.similar_objects()
		similar_articles = Article.objects.all().filter(tags__in=article_tags_ids).exclude(id=article.id)
		similar_articles = similar_articles.annotate(same_tags=Count('tags')).order_by('-same_tags')[:3]
		
		context['article'] = article
		context['tag'] = tag
		context['similar_articles'] = similar_articles
		context['sections'] = Section.objects.all()
		
		return render(request, self.template_name, context)

	template_name = 'legin_abroad/article.html'

class SearchView(View):
	template_name = 'legin_abroad/search.html'
	
	def get(self, request, *args, **kwargs):
		context = {}
		form = SearchForm()
		query = None
		results = []
		articles = Article.objects.all().order_by('-date_added').filter(status='published')

		if 'query' in request.GET:
			form = SearchForm(request.GET)

			if form.is_valid():
				query = form.cleaned_data['query']
				search_vector = SearchVector('topic', 'body', 'section')
				#search_vector = SearchVector('topic', weight='A') + SearchVector('body', weight='B') + SearchVector('tags', weight='C') + SearchVector('section', weight='A')
				search_query = SearchQuery(query)
				results = Article.objects.annotate(
										search=search_vector,
										rank=SearchRank(search_vector, search_query)
									).filter(search=search_query, status='published').order_by('-rank') 
		resultss = results
		resultss = list(dict.fromkeys(resultss))
		
		context['article'] = Article.objects.all().order_by('-date_added').filter(status='published')
		context['articles'] = articles
		context['sections'] = Section.objects.all()
		context['resultss'] = resultss
		context['results'] = results
		context['form'] = form
		context['query'] = query
		
		return render(request, self.template_name, context)


def tag_search(request, tag_slug=None):
	form = SearchForm()
	query = None
	results = []
	sections = section = Section.objects.all()
	articles = Article.objects.all().order_by('-date_added').filter(status='published')
	tag = get_object_or_404(Tag, slug=tag_slug)

	if 'query' in request.GET:
		form = SearchForm(request.GET)
		
		if form.is_valid():
			query = form.cleaned_data['query']
			search_vector = SearchVector('topic', weight='A') + SearchVector('body', weight='B') + SearchVector('tags', weight='C') + SearchVector('section', weight='A')
			search_query = SearchQuery(query)
			results = Article.objects.annotate(
									search=search_vector,
									rank=SearchRank(search_vector, search_query)
								).filter(search=search_query, status='published').order_by('-rank')
									#rank=SearchRank(search_vector, search_query).filter(rank__gte=0.3).order_by('-rank')

	context = {'form': form, 'query': query, 'results': results, 'sections':sections, 'section':section , 'tag':tag }
	
	return render(request, 'legin_abroad/search.html', context)

def about(request):
	sections = section = Section.objects.all()
	articles = Article.objects.all().order_by('-date_added').filter(status='published')

	context = {'sections':sections, 'section':section, 'articles':articles}

	return render(request, 'legin_abroad/about.html', context)





