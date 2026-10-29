from django.contrib.staticfiles import finders
from django.test import SimpleTestCase
from django.urls import reverse


class PragueBudgetTests(SimpleTestCase):
    def test_public_calculator_renders_without_database(self):
        response = self.client.get(reverse("en_legin_abroad:prague_cost_of_living"), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "en_legin_abroad/prague_cost_of_living.html")
        self.assertContains(response, "Household take-home income")
        self.assertContains(response, 'name="scenario" value="couple"')
        self.assertContains(response, "39,550 Kč")
        self.assertContains(response, "55,100 Kč")
        self.assertContains(response, "planning assumptions")
        self.assertContains(response, "pid.cz/jizdne-a-tarif/")

    def test_assets_are_discoverable_by_collectstatic(self):
        self.assertIsNotNone(finders.find("css/prague-budget.css"))
        self.assertIsNotNone(finders.find("js/prague-budget.js"))
