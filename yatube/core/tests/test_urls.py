from django.test import TestCase, Client


class CoreURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_template_404(self):
        response = self.guest_client.get('/unexisting_page/')
        self.assertTemplateUsed(response, 'core/404.html')
