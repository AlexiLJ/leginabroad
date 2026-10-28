from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from en_legin_abroad.models import EnArticle, EnSection


class PublicPageTests(TestCase):
    def test_homepage_uses_redesigned_template(self):
        response = self.client.get(reverse("en_legin_abroad:en_index"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "en_legin_abroad/en_index.html")
        self.assertContains(response, "Build software that works beyond the tutorial.")
        self.assertContains(response, "Python · Django · Test automation")
        self.assertContains(response, "Travel notes from a life abroad.")
        self.assertContains(response, "Coming later")

    def test_about_page_explains_the_site_and_author(self):
        response = self.client.get(reverse("en_legin_abroad:en_about"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "en_legin_abroad/en_about.html")
        self.assertContains(response, "I turn real development problems into practical guides.")
        self.assertContains(response, "Editorial principles")
        self.assertContains(response, "Travel Notes")

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
