from django.test import TestCase
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from en_legin_abroad.models import EnArticle, EnSection


class PublicPageTests(TestCase):
    def test_ads_txt_declares_google_adsense_seller(self):
        response = self.client.get(reverse("en_legin_abroad:ads_txt"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain; charset=utf-8")
        self.assertEqual(response["Cache-Control"], "public, max-age=86400")
        self.assertEqual(
            response.content.decode(),
            "google.com, pub-5630827130172417, DIRECT, f08c47fec0942fa0\n",
        )

    def test_homepage_uses_redesigned_template(self):
        response = self.client.get(reverse("en_legin_abroad:en_index"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "en_legin_abroad/en_index.html")
        self.assertContains(response, "Build software that works beyond the tutorial.")
        self.assertContains(response, "Python · Django · Test automation")
        self.assertContains(response, "Travel notes from a life abroad.")
        self.assertContains(response, "Coming later")
        self.assertContains(response, "ca-pub-5630827130172417")
        self.assertContains(response, "pagead2.googlesyndication.com/pagead/js/adsbygoogle.js")

    def test_about_page_explains_the_site_and_author(self):
        response = self.client.get(reverse("en_legin_abroad:en_about"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "en_legin_abroad/en_about.html")
        self.assertContains(response, "I turn real development problems into practical guides.")
        self.assertContains(response, "Editorial principles")
        self.assertContains(response, "Travel Notes")
        self.assertContains(response, 'class="content-breadcrumb"')
        self.assertContains(response, 'aria-current="page">About</li>')

    def test_article_page_uses_site_breadcrumb(self):
        section = EnSection.objects.create(name="Tech", sslug="tech")
        article = EnArticle.objects.create(
            section=section,
            topic="A practical article",
            slug="a-practical-article",
            body="<p>Useful details.</p>",
            date_added=timezone.now(),
            status="published",
        )

        response = self.client.get(article.get_absolute_url())

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "en_legin_abroad/en_article.html")
        self.assertContains(response, 'class="content-breadcrumb"')
        self.assertContains(response, "Tech")
        self.assertContains(response, 'aria-current="page"')

    def test_homepage_uses_site_pagination(self):
        section = EnSection.objects.create(name="Tech", sslug="tech")
        EnArticle.objects.bulk_create(
            [
                EnArticle(
                    section=section,
                    topic=f"Article {number}",
                    slug=f"article-{number}",
                    body="<p>Useful details.</p>",
                    date_added=timezone.now(),
                    status="published",
                )
                for number in range(11)
            ]
        )

        response = self.client.get(reverse("en_legin_abroad:en_index"), {"page": 2})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="pagination-nav"')
        self.assertContains(response, "Page <strong>2</strong> of 2", html=True)
        self.assertContains(response, 'aria-current="page">2</span>')

    def test_search_page_uses_redesigned_layout(self):
        response = self.client.get(reverse("en_legin_abroad:en_search"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "en_legin_abroad/en_search.html")
        self.assertContains(response, 'class="content-breadcrumb"')
        self.assertContains(response, 'class="search-hero"')
        self.assertContains(response, "Find a practical guide.")
        self.assertContains(response, "Popular paths through the archive.")
        self.assertContains(response, f'action="{reverse("en_legin_abroad:en_search")}"')

    def test_search_results_use_article_cards_and_empty_state(self):
        section = EnSection.objects.create(name="Tech", sslug="tech")
        article = EnArticle.objects.create(
            section=section,
            topic="Deploying Django safely",
            slug="deploying-django-safely",
            body="<p>A practical deployment walkthrough.</p>",
            date_added=timezone.now(),
            status="published",
        )

        results_html = render_to_string(
            "en_legin_abroad/en_search.html",
            {"query": "Django", "resultss": [article], "sections": [section]},
        )
        empty_html = render_to_string(
            "en_legin_abroad/en_search.html",
            {"query": "missing", "resultss": [], "sections": [section]},
        )

        self.assertIn('class="article-card"', results_html)
        self.assertIn("Deploying Django safely", results_html)
        self.assertIn("1 match found", " ".join(results_html.split()))
        self.assertIn('class="empty-state search-empty"', empty_html)
        self.assertIn("No matching articles yet.", empty_html)

    def test_topic_pages_use_consistent_breadcrumbs_and_article_cards(self):
        section = EnSection.objects.create(
            name="Tech",
            sslug="tech",
            description="<p>Practical software guides.</p>",
        )
        article = EnArticle.objects.create(
            section=section,
            topic="A mobile-friendly article",
            slug="a-mobile-friendly-article",
            body="<p>Useful details for the article card.</p>",
            date_added=timezone.now(),
            status="published",
        )

        topics_response = self.client.get(reverse("en_legin_abroad:en_sections"))
        topic_response = self.client.get(section.get_absolute_url())

        self.assertEqual(topics_response.status_code, 200)
        self.assertContains(topics_response, 'class="content-breadcrumb"')
        self.assertContains(topics_response, 'aria-current="page">Topics</li>')
        self.assertContains(topics_response, 'class="topic-card"')

        self.assertEqual(topic_response.status_code, 200)
        self.assertContains(topic_response, 'class="content-breadcrumb"')
        self.assertContains(topic_response, 'aria-current="page">Tech</li>')
        self.assertContains(topic_response, 'class="article-card"')
        self.assertContains(topic_response, article.topic)
        self.assertNotContains(topic_response, 'class="article-container"')
