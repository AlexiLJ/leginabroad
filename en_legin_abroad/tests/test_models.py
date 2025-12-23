from django.test import TestCase

from en_legin_abroad.models import EnArticle, EnSection


class EnArticleEnSectionTest(TestCase):
    def setUp(self):
        self.first_sections = EnSection(
            name="First section",
            sslug="fist_section",
        )
        self.first_article = EnArticle(
            section=self.first_sections,
            topic="First article",
            slug="first_article",
            date_added=self.first_sections.date_added,
            body="TEST TEST TEST TEST",
        )

    def test_article_integrity(self):
        self.assertTrue(self.first_article.section.name == "First section")
        self.assertTrue(self.first_article.topic == "First article")
        self.assertTrue(self.first_sections.date_added == self.first_article.date_added)
        self.assertIn(" TEST ", str(self.first_article.body))

    def test_absolute_sections_url(self):
        self.assertIn(f"{self.first_sections.sslug}", self.first_sections.get_absolute_url())

    def test_absolute_article_url(self):
        self.assertIn(f"{self.first_sections.sslug}/{self.first_article.slug}", self.first_article.get_absolute_url())
