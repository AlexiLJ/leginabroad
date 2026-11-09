from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from en_legin_abroad.models import EnArticle, EnSection


class HealthCheckTests(SimpleTestCase):
    def test_health_check(self):
        response = self.client.get(reverse("en_legin_abroad:health_check"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


@override_settings(
    SITE_ORIGIN="https://example.test",
    ADSENSE_PUBLISHER_ID="pub-1234567890123456",
    GOOGLE_ANALYTICS_MEASUREMENT_ID="G-TEST1234",
)
class PublicPageTests(TestCase):
    def test_ads_txt_declares_google_adsense_seller(self):
        response = self.client.get(reverse("en_legin_abroad:ads_txt"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain; charset=utf-8")
        self.assertEqual(response["Cache-Control"], "public, max-age=86400")
        self.assertEqual(
            response.content.decode(),
            "google.com, pub-1234567890123456, DIRECT, f08c47fec0942fa0\n",
        )

    def test_homepage_uses_redesigned_template(self):
        response = self.client.get(reverse("en_legin_abroad:en_index"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "en_legin_abroad/en_index.html")
        self.assertContains(response, "Practical guides for work and everyday life")
        self.assertNotContains(response, "Travel notes from a life abroad.")
        self.assertNotContains(response, "Coming later")
        self.assertContains(response, 'name="google-adsense-account" content="ca-pub-1234567890123456"')
        self.assertNotContains(response, "adsbygoogle.js")
        self.assertContains(response, 'data-measurement-id="G-TEST1234"')
        self.assertContains(response, reverse("en_legin_abroad:prague_cost_of_living"))

    @override_settings(ADSENSE_PUBLISHER_ID="", GOOGLE_ANALYTICS_MEASUREMENT_ID="")
    def test_google_integrations_are_optional(self):
        home = self.client.get(reverse("en_legin_abroad:en_index"), secure=True)
        privacy = self.client.get(reverse("en_legin_abroad:en_privacy"), secure=True)
        ads = self.client.get(reverse("en_legin_abroad:ads_txt"), secure=True)

        self.assertNotContains(home, "google-adsense-account")
        self.assertNotContains(home, "analytics-preference.js")
        self.assertNotContains(privacy, "Enable analytics")
        self.assertEqual(ads.status_code, 404)

    def test_robots_references_canonical_origin(self):
        response = self.client.get(reverse("en_legin_abroad:robots_txt"), secure=True)

        self.assertContains(response, "Sitemap: https://example.test/sitemap.xml")

    def test_homepage_topics_come_from_published_articles(self):
        section = EnSection.objects.create(name="Gardening", sslug="gardening")
        EnSection.objects.create(name="Empty topic", sslug="empty-topic")
        EnArticle.objects.create(
            section=section,
            topic="Growing herbs indoors",
            slug="growing-herbs-indoors",
            date_added=timezone.now(),
            status="published",
        )

        response = self.client.get(reverse("en_legin_abroad:en_index"), secure=True)

        self.assertContains(response, 'class="focus-card"')
        self.assertContains(response, f'<h3><a href="{section.get_absolute_url()}">Gardening</a></h3>')
        self.assertNotContains(response, "Empty topic")

    def test_homepage_excerpt_does_not_render_links_from_article_body(self):
        section = EnSection.objects.create(name="Tech", sslug="tech")
        EnArticle.objects.create(
            section=section,
            topic="Article with an inline link",
            slug="article-with-an-inline-link",
            body=(
                "<p>A safe excerpt containing "
                '<a href="/should-not-appear-in-card">an inline link</a> '
                "and enough surrounding text to exercise card rendering.</p>"
            ),
            date_added=timezone.now(),
            status="published",
        )

        response = self.client.get(reverse("en_legin_abroad:en_index"), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A safe excerpt containing an inline link")
        self.assertNotContains(response, 'href="/should-not-appear-in-card"')

    def test_about_page_explains_the_site_and_author(self):
        response = self.client.get(reverse("en_legin_abroad:en_about"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "en_legin_abroad/en_about.html")
        self.assertContains(response, "Meet Alex, the writer behind Legin’ Abroad")
        self.assertContains(response, "Editorial principles")
        self.assertContains(response, "Adapting to unfamiliar places")
        self.assertNotContains(response, "Travel Notes")
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

    def test_article_alias_redirects_to_published_article(self):
        section = EnSection.objects.create(name="Tech", sslug="tech")
        article = EnArticle.objects.create(
            section=section, topic="A guide", slug="a-guide", date_added=timezone.now(), status="published",
        )

        response = self.client.get("/old-topic/a-guide?source=bookmark", secure=True)

        self.assertRedirects(response, f"{article.get_absolute_url()}?source=bookmark", status_code=301)

    def test_sitemap_lists_published_articles_and_nonempty_topics(self):
        section = EnSection.objects.create(name="Tech", sslug="tech")
        empty = EnSection.objects.create(name="Empty", sslug="empty")
        published = EnArticle.objects.create(
            section=section, topic="Guide", slug="guide", date_added=timezone.now(), status="published",
        )
        draft = EnArticle.objects.create(section=empty, topic="Draft", slug="draft", date_added=timezone.now())

        response = self.client.get(reverse("en_legin_abroad:sitemap"), secure=True)

        self.assertContains(response, f"<loc>https://example.test{published.get_absolute_url()}</loc>")
        self.assertContains(response, f"<loc>https://example.test{section.get_absolute_url()}</loc>")
        self.assertContains(response, "<loc>https://example.test/prague-cost-of-living/</loc>")
        self.assertNotContains(response, empty.get_absolute_url())
        self.assertNotContains(response, draft.get_absolute_url())

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
        self.assertContains(response, 'rel="canonical" href="https://example.test/?page=2"')

    def test_search_page_uses_redesigned_layout(self):
        response = self.client.get(reverse("en_legin_abroad:en_search"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "en_legin_abroad/en_search.html")
        self.assertContains(response, 'class="content-breadcrumb"')
        self.assertContains(response, 'class="search-hero"')
        self.assertContains(response, "Find a practical guide.")
        self.assertContains(response, 'name="robots" content="noindex"')
        self.assertNotContains(response, "adsbygoogle.js")
        self.assertNotContains(response, "analytics-preference.js")
        self.assertContains(response, "Browse by topic")
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
