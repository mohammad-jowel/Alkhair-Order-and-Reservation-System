from django.test import TestCase, Client
from django.urls import reverse


class CorePagesTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_page_status_and_content(self):
        """Home page loads successfully with 200 OK and contains brand and multimedia."""
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/home.html')
        self.assertTemplateUsed(response, 'base.html')
        self.assertContains(response, 'Restoran Alkhair')
        self.assertContains(response, 'Charcoal Hearth Live')

    def test_about_page_status_and_content(self):
        """About & Contact page loads with location and hours."""
        response = self.client.get(reverse('core:about'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/about.html')
        self.assertContains(response, 'Parit Raja')
        self.assertContains(response, 'Operating Hours')

    def test_custom_404_page(self):
        """Non-existent URL triggers custom 404 page."""
        response = self.client.get('/this-url-definitely-does-not-exist/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, '404.html')
        self.assertContains(response, 'Page Not Found', status_code=404)
