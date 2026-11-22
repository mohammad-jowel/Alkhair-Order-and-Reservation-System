from decimal import Decimal
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, Client
from django.urls import reverse
from menu.models import MenuCategory, MenuItem


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

    def test_home_page_uses_the_yemeni_building_photo(self):
        response = self.client.get(reverse('core:home'))

        self.assertContains(response, 'img/alkhair-yemeni-building.webp')
        self.assertContains(response, 'Yemeni architecture')

    def test_restaurant_seed_matches_the_reference_menu(self):
        legacy_category = MenuCategory.objects.create(category_name='BBQ and Kebab')
        legacy_shawarma_category = MenuCategory.objects.create(category_name='Shawarma and Sandwiches')
        MenuItem.objects.create(
            category=legacy_category,
            item_name='Plate beef kebab',
            price=Decimal('20.00'),
            is_available=True,
        )
        MenuItem.objects.create(
            category=legacy_shawarma_category,
            item_name='Zinger plate with bread',
            price=Decimal('14.00'),
            is_available=True,
        )
        for item_name in (
            'Chicken kabsa', 'Mugalgal beef', 'Orange juice', 'Carrot juice',
            'Watermelon juice', 'Pineapple juice', 'Rutab with honey', 'Lemon mint',
            'Falafel sandwich', 'Sandwich zinger', 'Sandwich shish tawook',
        ):
            MenuItem.objects.create(
                category=legacy_category,
                item_name=item_name,
                price=Decimal('1.00'),
                is_available=True,
            )
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
        self.assertFalse(MenuItem.objects.get(item_name='Plate beef kebab').is_available)
        for unavailable_names in (
            ('Chicken kabsa', 'Mugalgal beef', 'Orange juice', 'Carrot juice'),
            ('Watermelon juice', 'Pineapple juice', 'Rutab with honey', 'Lemon mint'),
            ('Falafel sandwich', 'Sandwich zinger', 'Sandwich shish tawook'),
        ):
            self.assertFalse(
                MenuItem.objects.filter(item_name__in=unavailable_names, is_available=True).exists()
            )

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
        self.assertNotContains(response, 'BBQ and Kebab')
        self.assertNotContains(response, 'Plate beef kebab')
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

    def test_restaurant_seed_attaches_a_food_photo_to_each_active_item(self):
        call_command('seed_restaurant_demo', stdout=StringIO())

        items = MenuItem.objects.filter(is_available=True)
        self.assertEqual(items.count(), 78)
        for item in items:
            with self.subTest(item_name=item.item_name):
                self.assertTrue(item.image.name.startswith('menu_items/catalog/'))
                self.assertTrue(Path(settings.MEDIA_ROOT, item.image.name).is_file())

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
