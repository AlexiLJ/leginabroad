from django.shortcuts import render
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from taggit.models import Tag
from django.http import Http404
from django.conf import settings
from django.views.generic import View, ListView, DetailView
from django.db.models import Count
from .models import EnSection, EnArticle
from .forms import SearchForm
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank


def index(request, tag_slug=None):
	"""Home page"""
	sections = EnSection.objects.all().order_by('date_added')
	section = EnSection.objects.all()
	articles = EnArticle.objects.all().order_by('-date_added').filter(status='published')
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
	return render(request, 'en_legin_abroad/en_index.html', context)


class SectionsListView(ListView):
	
	model = EnSection
	template_name = 'en_legin_abroad/en_sections.html'

	def get_context_data(self, **kwargs):
		# Call the base implementation first to get a context
		context = super().get_context_data(**kwargs)
		# Add in a QuerySet of all sections
		context['sections'] = EnSection.objects.all()
		
		return context


def section(request, sslug):
	sections = EnSection.objects.all()
	section = get_object_or_404(EnSection, sslug=sslug)
	articles = section.enarticle_set.order_by('-date_added').filter(status='published')
	paginator = Paginator(articles, 5)
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

	return render(request, 'en_legin_abroad/en_section.html', context)

class ArticleDetailView(DetailView):
	model = EnArticle
	'''returns html slug'''
	
	def get(self, request, slug, tag_slug=None, *args, **kwargs):
		context = {}
		article =  get_object_or_404(EnArticle, slug=slug, status='published')
		tag = article.tags.all()
		article_tags_ids = article.tags.values_list('id', flat=True)
		similar_articles = EnArticle.objects.all().filter(tags__in=article_tags_ids).exclude(id=article.id)
		similar_articles = similar_articles.annotate(same_tags=Count('tags')).order_by('-same_tags')[:3]
		
		context['article'] = article
		context['tag'] = tag
		context['similar_articles'] = similar_articles
		context['sections'] = EnSection.objects.all()
		
		return render(request, self.template_name, context)
	
	template_name = 'en_legin_abroad/en_article.html'
	

class SearchView(View):
	template_name = 'en_legin_abroad/en_search.html'
	
	def get(self, request, *args, **kwargs):
		context = {}
		form = SearchForm()
		query = None
		results = []
		articles = EnArticle.objects.all().order_by('-date_added').filter(status='published')

		if 'query' in request.GET:
			form = SearchForm(request.GET)

			if form.is_valid():
				query = form.cleaned_data['query']
				search_vector = SearchVector('topic', 'body', 'section')
				search_query = SearchQuery(query)
				results = EnArticle.objects.annotate(
										search=search_vector,
										rank=SearchRank(search_vector, search_query)
									).filter(search=search_query, status='published').order_by('-rank') 
		resultss = results
		resultss = list(dict.fromkeys(resultss))
		
		context['article'] = EnArticle.objects.all().order_by('-date_added').filter(status='published')
		context['articles'] = articles
		context['sections'] = EnSection.objects.all()
		context['resultss'] = resultss
		context['results'] = results
		context['form'] = form
		context['query'] = query
		
		return render(request, self.template_name, context)


def tag_search(request, tag_slug=None):
	form = SearchForm()
	query = None
	results = []
	sections = section = EnSection.objects.all()
	articles = EnArticle.objects.all().order_by('-date_added').filter(status='published')
	tag = get_object_or_404(Tag, slug=tag_slug)

	if 'query' in request.GET:
		form = SearchForm(request.GET)
		
		if form.is_valid():
			query = form.cleaned_data['query']
			search_vector = SearchVector('topic', weight='A') + SearchVector('body', weight='B') + SearchVector('tags', weight='C') + SearchVector('section', weight='A')
			search_query = SearchQuery(query)
			results = EnArticle.objects.annotate(
									search=search_vector,
									rank=SearchRank(search_vector, search_query)
								).filter(search=search_query, status='published').order_by('-rank')
									

	context = {'form': form, 'query': query, 'results': results, 'sections':sections, 'section':section , 'tag':tag }
	
	return render(request, 'en_legin_abroad/en_search.html', context)

def about(request):
	sections = section = EnSection.objects.all()
	articles = EnArticle.objects.all().order_by('-date_added').filter(status='published')
	context = {'sections':sections, 'section':section, 'articles':articles}

	return render(request, 'en_legin_abroad/en_about.html', context)





