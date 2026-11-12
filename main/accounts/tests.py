from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import Account


class AccountsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = Account.objects.create_superuser(
            email='admin_test@alkhair.com',
            password='AdminPassword123!',
            full_name='Test Admin'
        )
        self.customer = Account.objects.create_user(
            email='customer_test@alkhair.com',
            password='CustomerPassword123!',
            full_name='Test Customer',
            phone='+60123456789',
            address='123 Test Street'
        )

    def test_customer_registration(self):
        """New customer can register successfully and gets role 'customer'."""
        response = self.client.post(reverse('accounts:register'), {
            'full_name': 'New User',
            'email': 'newuser@example.com',
            'phone': '+60111111111',
            'address': 'Parit Raja Johor',
            'password': 'SecurePassword123!',
            'confirm_password': 'SecurePassword123!',
        })
        self.assertEqual(response.status_code, 302)
        new_account = Account.objects.filter(email='newuser@example.com').first()
        self.assertIsNotNone(new_account)
        self.assertEqual(new_account.role, 'customer')
        self.assertFalse(new_account.is_staff)

    def test_registration_password_mismatch(self):
        """Registration fails if passwords do not match."""
        response = self.client.post(reverse('accounts:register'), {
            'full_name': 'Mismatch User',
            'email': 'mismatch@example.com',
            'phone': '+60111111111',
            'address': 'Parit Raja Johor',
            'password': 'SecurePassword123!',
            'confirm_password': 'DifferentPassword123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Account.objects.filter(email='mismatch@example.com').exists())

    def test_login_successful(self):
        """User can log in with valid credentials."""
        response = self.client.post(reverse('accounts:login'), {
            'email': 'customer_test@alkhair.com',
            'password': 'CustomerPassword123!',
        })
        self.assertEqual(response.status_code, 302)

    def test_login_invalid_credentials_generic_error(self):
        """Invalid login returns generic error without revealing account existence."""
        response = self.client.post(reverse('accounts:login'), {
            'email': 'customer_test@alkhair.com',
            'password': 'WrongPassword!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid email or password')

    def test_profile_update(self):
        """Logged-in user can update their personal details."""
        self.client.login(email='customer_test@alkhair.com', password='CustomerPassword123!')
        response = self.client.post(reverse('accounts:profile'), {
            'action': 'update_profile',
            'full_name': 'Updated Customer Name',
            'phone': '+60199999999',
            'address': 'Updated Address',
        })
        self.assertEqual(response.status_code, 302)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.full_name, 'Updated Customer Name')
        self.assertEqual(self.customer.phone, '+60199999999')

    def test_admin_required_blocks_customer(self):
        """Admin views block normal customers with 403 Forbidden."""
        self.client.login(email='customer_test@alkhair.com', password='CustomerPassword123!')
        response = self.client.get(reverse('menu:manage_menu'))
        # If manage_menu is protected with admin_required, customer gets 403
        # We will test admin_required directly:
        from accounts.decorators import admin_required
        from django.http import HttpResponse

        @admin_required
        def dummy_admin_view(request):
            return HttpResponse("Admin Secret")

        req = self.client.get('/dummy/').wsgi_request
        req.user = self.customer
        view_res = dummy_admin_view(req)
        self.assertEqual(view_res.status_code, 403)

    def test_open_redirect_prevented(self):
        """Malicious external next parameter is blocked to prevent open redirect."""
        response = self.client.post(f"{reverse('accounts:login')}?next=https://malicious-phishing-site.com", {
            'email': 'customer_test@alkhair.com',
            'password': 'CustomerPassword123!',
        })
        self.assertEqual(response.status_code, 302)
        # Must redirect internally, never to the external host
        self.assertNotIn('malicious-phishing-site.com', response.url)
        self.assertEqual(response.url, reverse('core:home'))

    def test_admin_login_redirects_to_dashboard(self):
        """Logging in as admin redirects to dashboard."""
        response = self.client.post(reverse('accounts:login'), {
            'email': 'admin_test@alkhair.com',
            'password': 'AdminPassword123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard:dashboard'))
