from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from accounts.models import Account
from menu.models import MenuCategory, MenuItem
from orders.models import Order, OrderItem
from reservations.models import Reservation


class DashboardTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = Account.objects.create_superuser(
            email='admin_dash@alkhair.com',
            password='AdminPassword123!',
            full_name='Dash Admin'
        )
        self.customer = Account.objects.create_user(
            email='cust_dash@alkhair.com',
            password='CustomerPassword123!',
            full_name='Dash Customer',
            phone='+60123456789'
        )
        self.category = MenuCategory.objects.create(category_name='Grills')
        self.item = MenuItem.objects.create(
            category=self.category,
            item_name='Mix Barbecue Platter',
            description='Mixed grilled meats',
            price=Decimal('22.00'),
            is_available=True
        )

    def test_unauthenticated_user_redirected_to_login(self):
        """Unauthenticated user accessing dashboard is redirected to login."""
        response = self.client.get(reverse('dashboard:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('accounts:login'), response.url)

    def test_customer_blocked_from_dashboard(self):
        """Customer attempting to access admin dashboard receives 403 Forbidden."""
        self.client.login(email='cust_dash@alkhair.com', password='CustomerPassword123!')
        response = self.client.get(reverse('dashboard:dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_admin_dashboard_metrics_and_sales_rule(self):
        """
        Dashboard displays accurate metrics according to the business rule:
        Sales = sum of total_amount for orders with payment_status = 'paid' and order_status != 'cancelled'.
        """
        self.client.login(email='admin_dash@alkhair.com', password='AdminPassword123!')

        # Order 1: Paid and completed -> Should count (RM 44.00)
        order1 = Order.objects.create(
            account=self.customer,
            order_type='takeaway',
            order_status='completed',
            payment_method='sim_card',
            payment_status='paid',
            total_amount=Decimal('44.00')
        )
        OrderItem.objects.create(order=order1, item=self.item, quantity=2, unit_price=Decimal('22.00'))

        # Order 2: Cash and pending payment -> Should NOT count yet
        order2 = Order.objects.create(
            account=self.customer,
            order_type='takeaway',
            order_status='pending',
            payment_method='cash',
            payment_status='pending',
            total_amount=Decimal('22.00')
        )
        OrderItem.objects.create(order=order2, item=self.item, quantity=1, unit_price=Decimal('22.00'))

        # Order 3: Cancelled order -> Should NOT count even if previously paid
        order3 = Order.objects.create(
            account=self.customer,
            order_type='takeaway',
            order_status='cancelled',
            payment_method='sim_card',
            payment_status='paid',
            total_amount=Decimal('22.00')
        )
        OrderItem.objects.create(order=order3, item=self.item, quantity=1, unit_price=Decimal('22.00'))

        # Create a pending reservation
        Reservation.objects.create(
            account=self.customer,
            reservation_date=timezone.localdate(),
            reservation_time='20:00',
            party_size=4,
            status='pending'
        )

        response = self.client.get(reverse('dashboard:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/dashboard.html')

        # Check calculated metrics in context
        self.assertEqual(response.context['today_sales'], Decimal('44.00'))
        self.assertEqual(response.context['this_month_sales'], Decimal('44.00'))
        self.assertEqual(response.context['total_orders_count'], 3)
        self.assertEqual(response.context['pending_orders_count'], 1)
        self.assertEqual(response.context['pending_reservations_count'], 1)

        # Check page text contains business rule notice and monthly sales subtext
        self.assertContains(response, 'Sales Total Rule')
        self.assertContains(response, 'Best-Selling Menu Items')
        self.assertContains(response, 'This month:')
