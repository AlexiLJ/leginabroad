from django.test import SimpleTestCase


class TestHomePage(SimpleTestCase):
    def test_homepage_use_correct_template(self):
        response = self.client.get("leginabroad.com")
        self.assertTemplateUsed(response, "en_index.html")

    # def test_homepage_contains_welcome_message(self):
    #     response = self.client.get('leginabroad.com')
    #     self.assertContains(response, )
