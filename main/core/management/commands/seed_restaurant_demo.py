import secrets
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import Account
from menu.models import MenuCategory, MenuItem
from orders.models import RestaurantTable


class Command(BaseCommand):
    help = 'Seeds restaurant data (categories, menu items, and tables) plus the demo admin account.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Seeding demo data...'))

        # 1. Seed Accounts
        admin, created = Account.objects.get_or_create(
            email='admin@gmail.com',
            defaults={
                'full_name': 'Demo Admin',
                'phone': '',
                'address': 'Restoran Alkhair, Parit Raja, Batu Pahat, Johor',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin.set_password('Admin1234!')
            admin.save()
            self.stdout.write(self.style.SUCCESS(f'Created admin account: {admin.email}'))
        # Ensure the dedicated demo account can use Django Admin without
        # changing the password if the account already exists.
        changed_fields = []
        for field, value in (
            ('role', 'admin'),
            ('is_staff', True),
            ('is_superuser', True),
            ('is_active', True),
        ):
            if getattr(admin, field) != value:
                setattr(admin, field, value)
                changed_fields.append(field)
        if changed_fields:
            admin.save(update_fields=changed_fields)

        # 2. Seed Restaurant Tables (10 tables with random qr_token)
        for num in range(1, 11):
            table, created = RestaurantTable.objects.get_or_create(
                table_number=num,
                defaults={
                    'qr_token': secrets.token_urlsafe(16),
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(f'Created Table {num} (Token: {table.qr_token})')

        # 3. Seed Menu Categories
        cat_bbq, _ = MenuCategory.objects.get_or_create(category_name='BBQ and Kebab')
        cat_shawarma, _ = MenuCategory.objects.get_or_create(category_name='Shawarma and Sandwiches')

        # 4. Seed Menu Items
        bbq_items = [
            ('Plate beef kebab', 'Grilled beef kebab skewers served fresh', Decimal('20.00')),
            ('Plate chicken kebab', 'Grilled seasoned chicken kebab skewers', Decimal('18.00')),
            ('Plate mixed kebab', 'Combination of beef and chicken skewers', Decimal('18.00')),
            ('1/4 chicken barbecue', 'Quarter roasted chicken with middle-eastern spices', Decimal('9.00')),
            ('Mix barbecue', 'Assorted grilled meats barbecue platter', Decimal('22.00')),
            ('1/4 chicken barbecue with rice', 'Quarter barbecue chicken served with spiced mandy rice', Decimal('14.00')),
            ('Kebab mix with rice', 'Mixed beef and chicken kebabs served with aromatic rice', Decimal('18.00')),
            ('Shawarma beef with rice', 'Sliced beef shawarma served on a bed of flavored rice', Decimal('15.00')),
            ('Shawarma chicken with rice', 'Sliced chicken shawarma served on a bed of flavored rice', Decimal('12.00')),
            ('Lamb shank', 'Slow-cooked tender lamb shank seasoned with house spices', Decimal('35.00')),
            ('Moffa fish and bread', 'Traditional Moffa style fish oven-baked and served with freshly baked bread', Decimal('25.00')),
            ('Moffa fish and rice', 'Traditional Moffa style fish served with seasoned rice', Decimal('25.00')),
        ]

        shawarma_items = [
            ('Zinger plate with bread', 'Crispy spicy chicken zinger cutlets served with fresh bread', Decimal('14.00')),
            ('Falafel plate with bread', 'Deep-fried golden chickpea falafel patties with fresh bread and tahini', Decimal('8.00')),
            ('3 pcs sambosa', 'Crispy fried pastry triangles filled with spiced savory filling', Decimal('5.00')),
            ('French fries', 'Golden crispy potato french fries with garlic sauce', Decimal('5.00')),
            ('Beef sandwich kabab', 'Grilled beef kebab rolled in flatbread with sauce and salad', Decimal('9.00')),
            ('Chicken sandwich kabab', 'Grilled chicken kebab rolled in flatbread with sauce and salad', Decimal('7.00')),
            ('Plate shish tawook', 'Marinated chicken breast skewers grilled to perfection', Decimal('18.00')),
            ('Beef shawarma (small)', 'Classic wrapped beef shawarma in pita bread (small size)', Decimal('9.00')),
            ('Beef shawarma (large)', 'Classic wrapped beef shawarma in pita bread (large size)', Decimal('15.00')),
            ('Chicken shawarma (small)', 'Marinated chicken shawarma roll with garlic sauce (small size)', Decimal('7.00')),
            ('Chicken shawarma (large)', 'Marinated chicken shawarma roll with garlic sauce (large size)', Decimal('13.00')),
            ('Falafel sandwich', 'Vegetarian fried falafel wrap with pickles and tahini', Decimal('5.00')),
            ('Sandwich zinger', 'Crispy spicy fried chicken sandwich wrap', Decimal('8.00')),
            ('Sandwich shish tawook', 'Tender shish tawook grilled chicken wrap', Decimal('7.00')),
        ]

        for name, desc, price in bbq_items:
            MenuItem.objects.get_or_create(
                item_name=name,
                defaults={
                    'category': cat_bbq,
                    'description': desc,
                    'price': price,
                    'is_available': True,
                }
            )

        for name, desc, price in shawarma_items:
            MenuItem.objects.get_or_create(
                item_name=name,
                defaults={
                    'category': cat_shawarma,
                    'description': desc,
                    'price': price,
                    'is_available': True,
                }
            )

        self.stdout.write(self.style.SUCCESS('\nDemo data seeding complete!'))
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('DEMO LOGINS:'))
        self.stdout.write(f'  Admin:      {admin.email}')
        if created:
            self.stdout.write('  Initial password: Admin1234! (change it after setup)')
        self.stdout.write('=' * 60)
