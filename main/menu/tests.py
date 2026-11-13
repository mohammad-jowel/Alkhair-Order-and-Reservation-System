from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.db.models import ProtectedError
from accounts.models import Account
from menu.models import MenuCategory, MenuItem
from orders.models import Order, OrderItem


class MenuTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = Account.objects.create_superuser(
            email='admin_menu@alkhair.com',
            password='AdminPassword123!',
            full_name='Menu Admin'
        )
        self.customer = Account.objects.create_user(
            email='customer_menu@alkhair.com',
            password='CustomerPassword123!',
            full_name='Menu Customer'
        )
        self.category = MenuCategory.objects.create(category_name='Grills')
        self.item_avail = MenuItem.objects.create(
            category=self.category,
            item_name='Beef Kebab',
            description='Freshly grilled beef',
            price=Decimal('20.00'),
            is_available=True
        )
        self.item_unavail = MenuItem.objects.create(
            category=self.category,
            item_name='Sold Out Dish',
            description='Unavailable right now',
            price=Decimal('15.00'),
            is_available=False
        )

    def test_public_menu_display(self):
        """Public menu displays available items and groups by category."""
        response = self.client.get(reverse('menu:menu_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Beef Kebab')
        self.assertContains(response, 'RM 20.00')

    def test_customer_cannot_access_manage_menu(self):
        """Customer is blocked with 403 from admin menu management."""
        self.client.login(email='customer_menu@alkhair.com', password='CustomerPassword123!')
        response = self.client.get(reverse('menu:manage_menu'))
        self.assertEqual(response.status_code, 403)

    def test_admin_can_access_manage_menu(self):
        """Admin can access manage menu."""
        self.client.login(email='admin_menu@alkhair.com', password='AdminPassword123!')
        response = self.client.get(reverse('menu:manage_menu'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Beef Kebab')
        self.assertContains(response, 'Sold Out Dish')

    def test_admin_filter_manage_menu_by_category(self):
        """Admin can filter menu items by category."""
        other_category = MenuCategory.objects.create(category_name='Drinks')
        other_item = MenuItem.objects.create(
            category=other_category,
            item_name='Arabic Tea',
            price=Decimal('5.00'),
            is_available=True
        )

        self.client.login(email='admin_menu@alkhair.com', password='AdminPassword123!')
        # Filter by Drinks category
        response = self.client.get(reverse('menu:manage_menu') + f'?category={other_category.category_id}')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Arabic Tea')
        self.assertNotContains(response, 'Beef Kebab')

        # Reset / All categories
        response_all = self.client.get(reverse('menu:manage_menu'))
        self.assertEqual(response_all.status_code, 200)
        self.assertContains(response_all, 'Arabic Tea')
        self.assertContains(response_all, 'Beef Kebab')

    def test_admin_add_menu_item(self):
        """Admin can add a new menu item."""
        self.client.login(email='admin_menu@alkhair.com', password='AdminPassword123!')
        response = self.client.post(reverse('menu:add_item'), {
            'category': self.category.category_id,
            'item_name': 'Chicken Mandy',
            'description': 'Tender roasted chicken with rice',
            'price': '16.00',
            'is_available': True,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(MenuItem.objects.filter(item_name='Chicken Mandy').exists())

    def test_toggle_item_availability(self):
        """Admin can toggle item availability."""
        self.client.login(email='admin_menu@alkhair.com', password='AdminPassword123!')
        self.assertTrue(self.item_avail.is_available)
        response = self.client.post(reverse('menu:toggle_availability', args=[self.item_avail.item_id]))
        self.assertEqual(response.status_code, 302)
        self.item_avail.refresh_from_db()
        self.assertFalse(self.item_avail.is_available)

    def test_delete_ordered_menu_item_is_blocked(self):
        """Deleting a menu item that has been ordered is protected and shows friendly error."""
        self.client.login(email='admin_menu@alkhair.com', password='AdminPassword123!')
        # Create an order with this item
        order = Order.objects.create(
            account=self.customer,
            order_type='takeaway',
            order_status='pending',
            payment_method='cash',
            payment_status='pending',
            total_amount=Decimal('20.00')
        )
        OrderItem.objects.create(
            order=order,
            item=self.item_avail,
            quantity=1,
            unit_price=Decimal('20.00')
        )

        response = self.client.post(reverse('menu:delete_item', args=[self.item_avail.item_id]))
        self.assertEqual(response.status_code, 302)
        # Verify item still exists because deletion was prevented
        self.assertTrue(MenuItem.objects.filter(item_id=self.item_avail.item_id).exists())
