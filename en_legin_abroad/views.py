from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView, ListView, View
from taggit.models import Tag

from .forms import SearchForm
from .models import EnArticle, EnSection


def index(request, tag_slug=None):
    """Home page"""
    sections = EnSection.objects.all().order_by('date_added')
    section = EnSection.objects.all()
    articles = EnArticle.objects.all().order_by('-date_added').filter(status='published')
    tag = None

    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        articles = articles.filter(tags__in=[tag])

    paginator = Paginator(articles, 5)  # 5 posts on each page
    page = request.GET.get('page', )

    try:
        articles = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer deliver the first page
        articles = paginator.page(1)
    except EmptyPage:
        # If page is out of range deliver last page of results
        articles = paginator.page(paginator.num_pages)
    context = {'sections': sections, 'section': section, 'articles': articles, 'tag': tag}
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
    page = request.GET.get('page', )
    try:
        articles = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer deliver the first page
        articles = paginator.page(1)
    except EmptyPage:
        # If page is out of range deliver last page of results
        articles = paginator.page(paginator.num_pages)

    context = {'sections': sections, 'section': section, 'articles': articles}

    return render(request, 'en_legin_abroad/en_section.html', context)


class ArticleDetailView(DetailView):
    """
    View for displaying detailed information about a single article.
    Handles article display with related tags and similar articles suggestions.
    """
    model = EnArticle

    def get(self, request, slug, tag_slug=None, *args, **kwargs):
        """
        Handles GET requests for article detail view.

        Args:
            request: The HTTP request
            slug: The article's slug identifier
            tag_slug: Optional tag slug for filtering
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments

        Returns:
            Rendered article detail template with article and related content
        """
        context = {}
        article = get_object_or_404(EnArticle, slug=slug, status='published')
        tag = article.tags.all()
        article_tags_ids = article.tags.values_list('id', flat=True)
        similar_articles = EnArticle.objects.all().filter(status='published',
                                                          tags__in=article_tags_ids).exclude(id=article.id)
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
                    rank=SearchRank(search_vector, search_query),
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
    sections = EnSection.objects.all()
    tag = get_object_or_404(Tag, slug=tag_slug)

    if 'query' in request.GET:
        form = SearchForm(request.GET)

        if form.is_valid():
            query = form.cleaned_data['query']
            search_vector = SearchVector('topic', weight='A') + SearchVector('body', weight='B') + SearchVector('tags',
                                                                                                                weight='C') + SearchVector(
                'section', weight='A')
            search_query = SearchQuery(query)
            results = EnArticle.objects.annotate(
                search=search_vector,
                rank=SearchRank(search_vector, search_query),
            ).filter(search=search_query, status='published').order_by('-rank')

    context = {
               'form': form,
               'query': query,
               'results': results,
               'sections': sections,
               'section': section,
               'tag': tag,
               }

    return render(request, 'en_legin_abroad/en_search.html', context)


def about(request):
    sections = EnSection.objects.all()
    articles = EnArticle.objects.all().order_by('-date_added').filter(status='published')
    context = {'sections': sections, 'section': section, 'articles': articles}

    return render(request, 'en_legin_abroad/en_about.html', context)
