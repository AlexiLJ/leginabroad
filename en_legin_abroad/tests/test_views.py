from django.test import TestCase
from django.urls import reverse


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
