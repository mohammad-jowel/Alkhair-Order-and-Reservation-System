from decimal import Decimal
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from PIL import Image
from accounts.models import Account
from core.models import RestaurantDemoSeedRecord
from menu.models import MenuCategory, MenuItem
from orders.models import Order, OrderItem, RestaurantTable


class CorePagesTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_home_page_status_and_content(self):
        """Home page loads successfully with 200 OK and contains brand and key content."""
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/home.html')
        self.assertTemplateUsed(response, 'base.html')
        self.assertContains(response, 'Restoran Alkhair')
        self.assertContains(response, 'Yemeni Flavors')

    def test_home_page_uses_the_supplied_yemeni_building_photo(self):
        response = self.client.get(reverse('core:home'))

        self.assertContains(response, 'img/alkhair-yemeni-building.webp')
        self.assertContains(response, 'Yemeni architecture')
        with Image.open(settings.BASE_DIR / 'static/img/alkhair-yemeni-building.webp') as hero_image:
            self.assertEqual(hero_image.size, (1800, 600))

    @override_settings(OPENING_TIME='10:15', CLOSING_TIME='22:00')
    def test_public_operating_hours_follow_the_configured_booking_hours(self):
        expected_hours = '10:15 AM – 10:00 PM'

        for page_name in ('core:home', 'core:about'):
            with self.subTest(page_name=page_name):
                response = self.client.get(reverse(page_name))
                self.assertContains(response, expected_hours)

    def test_restaurant_seed_matches_the_reference_menu(self):
        call_command('seed_restaurant_demo', stdout=StringIO())

        expected_prices = {
            'Mandi lamb': Decimal('24.00'),
            'Chicken kahsa': Decimal('12.00'),
            'Haneeth chicken': Decimal('13.00'),
            'Set lamb big': Decimal('106.00'),
            'Saltah': Decimal('20.00'),
            'Mugalagal beef': Decimal('16.00'),
            'Garlic Sauce': Decimal('1.00'),
            'Avocado juice': Decimal('10.00'),
            'Orang Juice': Decimal('6.00'),
            'Carott Juice': Decimal('5.00'),
            'Milo ice': Decimal('4.00'),
            'Sirap bandung': Decimal('4.00'),
            'Arabic red tea teapot': Decimal('6.00'),
            'Kunafa cream': Decimal('10.00'),
            'Beef shawarma (large)': Decimal('15.00'),
        }
        for item_name, price in expected_prices.items():
            with self.subTest(item_name=item_name):
                item = MenuItem.objects.get(item_name=item_name)
                self.assertEqual(item.price, price)
                self.assertTrue(item.is_available)

        self.assertIn(
            'Extra cheese + RM 1',
            MenuItem.objects.get(item_name='Beef shawarma (small)').description,
        )
        self.assertEqual(MenuItem.objects.get(item_name='Mandi lamb').description, '')
        self.assertEqual(MenuItem.objects.filter(is_available=True).count(), 78)

        expected_category_counts = {
            'Yemeni Rice Dishes': 8,
            'Family Meals': 9,
            'Yemeni Specialties': 15,
            'Cold Appetizers': 6,
            'Fresh Juices and Cold Drinks': 15,
            'Shawarma and Sandwiches': 13,
            'Drinks': 3,
            'Hot Drinks': 4,
            'Sweets': 5,
        }
        for category_name, item_count in expected_category_counts.items():
            with self.subTest(category=category_name):
                category = MenuCategory.objects.get(category_name=category_name)
                self.assertEqual(category.items.filter(is_available=True).count(), item_count)

        response = self.client.get(reverse('menu:menu_list'))
        self.assertContains(response, 'Yemeni Rice Dishes')
        self.assertContains(response, 'Mandi lamb')
        self.assertContains(response, '/media/menu_items/catalog/')
        self.assertContains(
            response,
            "Menu images are AI-enhanced restorations and illustrations based on the restaurant's original menu artwork",
        )
        self.assertContains(response, 'alt="Menu artwork image for Mandi lamb"')
        self.assertNotContains(response, 'Prepared fresh daily with authentic regional spices.')
        self.assertEqual(
            [category.category_name for category in response.context['categories']],
            [
                'Yemeni Rice Dishes',
                'Family Meals',
                'Yemeni Specialties',
                'Cold Appetizers',
                'Fresh Juices and Cold Drinks',
                'Shawarma and Sandwiches',
                'Drinks',
                'Hot Drinks',
                'Sweets',
            ],
        )
        home_response = self.client.get(reverse('core:home'))
        self.assertContains(
            home_response,
            "Menu images are AI-enhanced restorations and illustrations based on the restaurant's original menu artwork",
        )
        self.assertContains(home_response, 'alt="Menu artwork image for Mandi lamb"')
        self.assertNotContains(home_response, 'Freshly prepared in our kitchen.')

    def test_restaurant_seed_does_not_manage_removed_legacy_items(self):
        legacy_category = MenuCategory.objects.create(category_name='BBQ and Kebab')
        legacy_item = MenuItem.objects.create(
            category=legacy_category,
            item_name='Plate beef kebab',
            price=Decimal('20.00'),
            is_available=True,
        )

        call_command('seed_restaurant_demo', stdout=StringIO())

        legacy_item.refresh_from_db()
        self.assertTrue(legacy_item.is_available)

    def test_restaurant_seed_refreshes_existing_menu_items(self):
        call_command('seed_restaurant_demo', stdout=StringIO())
        item = MenuItem.objects.get(item_name='Mandi lamb')
        item.price = Decimal('99.00')
        item.is_available = False
        item.save(update_fields=['price', 'is_available'])

        call_command('seed_restaurant_demo', stdout=StringIO())

        item.refresh_from_db()
        self.assertEqual(item.price, Decimal('24.00'))
        self.assertTrue(item.is_available)
        self.assertEqual(MenuItem.objects.filter(item_name='Mandi lamb').count(), 1)

    def test_restaurant_seed_delete_removes_unused_seeded_data(self):
        call_command('seed_restaurant_demo', stdout=StringIO())

        call_command('seed_restaurant_demo', '--delete', stdout=StringIO())

        self.assertFalse(Account.objects.filter(email='admin@gmail.com').exists())
        self.assertFalse(MenuItem.objects.filter(item_name='Mandi lamb').exists())
        self.assertFalse(MenuCategory.objects.filter(category_name='Yemeni Rice Dishes').exists())
        self.assertFalse(RestaurantTable.objects.filter(table_number__range=(1, 10)).exists())

    def test_restaurant_seed_can_explicitly_adopt_legacy_demo_data_before_cleanup(self):
        call_command('seed_restaurant_demo', stdout=StringIO())
        RestaurantDemoSeedRecord.objects.all().delete()

        # A normal rerun safely reclaims only catalog rows it already refreshes.
        call_command('seed_restaurant_demo', stdout=StringIO())
        self.assertFalse(
            RestaurantDemoSeedRecord.objects.filter(
                object_type='restaurant_table'
            ).exists()
        )
        self.assertFalse(
            RestaurantDemoSeedRecord.objects.filter(object_type='account').exists()
        )

        call_command('seed_restaurant_demo', '--adopt-existing', stdout=StringIO())
        call_command('seed_restaurant_demo', '--delete', stdout=StringIO())

        self.assertFalse(Account.objects.filter(email='admin@gmail.com').exists())
        self.assertFalse(MenuItem.objects.filter(item_name='Mandi lamb').exists())
        self.assertFalse(RestaurantTable.objects.filter(table_number__range=(1, 10)).exists())

    def test_restaurant_seed_delete_cleans_every_seed_owned_account(self):
        call_command('seed_restaurant_demo', stdout=StringIO())
        supplemental_admin = Account.objects.create_user(
            email='supplemental-demo-admin@example.com',
            password='Customer1234!',
            full_name='Supplemental Demo Admin',
            role='admin',
        )
        RestaurantDemoSeedRecord.objects.create(
            seed_key='restaurant_demo',
            object_type='account',
            object_id=supplemental_admin.account_id,
        )

        call_command('seed_restaurant_demo', '--delete', stdout=StringIO())

        self.assertFalse(Account.objects.filter(email='admin@gmail.com').exists())
        self.assertFalse(Account.objects.filter(pk=supplemental_admin.pk).exists())

    def test_restaurant_seed_delete_preserves_unowned_lookalike_records(self):
        custom_category = MenuCategory.objects.create(category_name='Custom Catalog')
        custom_item = MenuItem.objects.create(
            category=custom_category,
            item_name='Custom catalog item',
            price=Decimal('9.00'),
            image='menu_items/catalog/custom-item.webp',
        )
        custom_table = RestaurantTable.objects.create(
            table_number=10,
            qr_token='custom-unowned-table-token',
        )
        custom_admin = Account.objects.create_user(
            email='admin@gmail.com',
            password='Customer1234!',
            full_name='Unowned Admin',
            role='admin',
        )

        call_command('seed_restaurant_demo', '--delete', stdout=StringIO())

        self.assertTrue(MenuItem.objects.filter(pk=custom_item.pk).exists())
        self.assertTrue(RestaurantTable.objects.filter(pk=custom_table.pk).exists())
        self.assertTrue(Account.objects.filter(pk=custom_admin.pk).exists())

    def test_restaurant_seed_delete_retains_rows_linked_to_order_history(self):
        call_command('seed_restaurant_demo', stdout=StringIO())
        item = MenuItem.objects.get(item_name='Mandi lamb')
        table = RestaurantTable.objects.get(table_number=1)
        customer = Account.objects.create_user(
            email='history-customer@example.com',
            password='Customer1234!',
            full_name='History Customer',
        )
        order = Order.objects.create(
            account=customer,
            table=table,
            order_type='dine_in',
            payment_method='cash',
            total_amount=item.price,
        )
        order_item = OrderItem.objects.create(
            order=order,
            item=item,
            quantity=1,
            unit_price=item.price,
        )

        call_command('seed_restaurant_demo', '--delete', stdout=StringIO())

        item.refresh_from_db()
        table.refresh_from_db()
        order_item.refresh_from_db()
        self.assertFalse(item.is_available)
        self.assertFalse(table.is_active)
        self.assertEqual(order_item.item_id, item.item_id)
        self.assertEqual(order_item.order.table_id, table.table_id)
        self.assertTrue(MenuCategory.objects.filter(category_name='Yemeni Rice Dishes').exists())
        self.assertFalse(MenuItem.objects.filter(item_name='Mandi chicken').exists())

    def test_restaurant_seed_attaches_a_food_photo_to_each_active_item(self):
        call_command('seed_restaurant_demo', stdout=StringIO())

        items = MenuItem.objects.filter(is_available=True)
        self.assertEqual(items.count(), 78)
        for item in items:
            with self.subTest(item_name=item.item_name):
                self.assertTrue(item.image.name.startswith('menu_items/catalog/'))
                self.assertTrue(Path(settings.MEDIA_ROOT, item.image.name).is_file())

    def test_about_page_shows_confirmed_restaurant_information_and_hero_photo(self):
        response = self.client.get(reverse('core:about'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/about.html')
        self.assertContains(response, '8, Jalan Universiti 3, Bandar Universiti')
        self.assertContains(response, 'Parit Raja, Johor Bahru 85400')
        self.assertContains(response, '+60 11-6830 9514')
        self.assertContains(response, '011-6830 9514')
        self.assertContains(response, 'Daily from 11:00 AM – 11:00 PM')
        self.assertContains(response, 'img/alkhair-yemeni-building.webp')
        self.assertNotContains(response, 'contact@alkhair-restaurant.com')
        self.assertNotContains(response, 'placeholder-icon')

    def test_custom_404_page(self):
        """Non-existent URL triggers custom 404 page."""
        response = self.client.get('/this-url-definitely-does-not-exist/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, '404.html')
        self.assertContains(response, 'Page Not Found', status_code=404)
