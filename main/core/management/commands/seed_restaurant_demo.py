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
                'is_staff': False,
                'is_superuser': False,
            }
        )
        if created:
            admin.set_password('Admin1234!')
            admin.save()
            self.stdout.write(self.style.SUCCESS(f'Created admin account: {admin.email}'))
        # This demo account uses the app's role-protected admin portal, not
        # Django Admin, so it needs neither staff nor superuser privileges.
        changed_fields = []
        for field, value in (
            ('role', 'admin'),
            ('is_staff', False),
            ('is_superuser', False),
            ('is_active', True),
        ):
            if getattr(admin, field) != value:
                setattr(admin, field, value)
                changed_fields.append(field)
        if changed_fields:
            admin.save(update_fields=changed_fields)

        # Remove any elevated permissions left by an older version of this seed.
        admin.groups.clear()
        admin.user_permissions.clear()

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

        # 3. Seed the readable entries from the supplied menu photos.
        # Item descriptions are left blank unless the poster lists an add-on.
        menu_catalog = {
            'Yemeni Rice Dishes': [
                ('Mandi lamb', '24.00', 'rice_mandi_lamb.webp'),
                ('Mandi chicken', '12.00', 'rice_mandi_chicken.webp'),
                ('Haneeth lamb', '25.00', 'rice_haneeth_lamb.webp'),
                ('Haneeth chicken', '13.00', 'rice_haneeth_chicken.webp'),
                ('Zurbian lamb', '24.00', 'rice_zurbian_lamb.webp'),
                ('Zurbian chicken', '12.00', 'rice_zurbian_chicken.webp'),
                ('Kabsah lamb', '24.00', 'rice_kabsah_lamb.webp'),
                ('Chicken kahsa', '12.00', 'rice_chicken_kahsa.webp'),
            ],
            'Family Meals': [
                ('Set mix small', '36.00', 'family_set_mix.webp'),
                ('Set mix big', '72.00', 'family_set_mix.webp'),
                ('Set lamb small', '48.00', 'family_set_lamb.webp'),
                ('Set lamb big', '106.00', 'family_set_lamb.webp'),
                ('Set chicken small', '24.00', 'family_set_chicken.webp'),
                ('Set chicken big', '48.00', 'family_set_chicken.webp'),
                ('Chicken only', '7.00', 'family_chicken_only.webp'),
                ('Lamb only', '20.00', 'family_lamb_only.webp'),
                ('Rice only', '5.00', 'family_rice_only.webp'),
            ],
            'Yemeni Specialties': [
                ('Saltah', '20.00', 'special_saltah.webp'),
                ('Fahsa beef', '20.00', 'special_fahsa.webp'),
                ('Fahsa chicken', '15.00', 'special_fahsa.webp'),
                ('Daqa beef', '18.00', 'special_daqa_beef.webp'),
                ('Foul madarah', '13.00', 'special_foul_madarah.webp'),
                ('Beans madarah', '14.00', 'special_beans.webp'),
                ('Beans with egg', '16.00', 'special_beans.webp'),
                ('Shrimp sanonah', '25.00', 'special_shrimp_sanonah.webp'),
                ('Mugalagal beef', '16.00', 'special_mugalagal_beef.webp'),
                ('Akda beef', '17.00', 'special_akda_beef.webp'),
                ('Liver', '15.00', 'special_liver.webp'),
                ('Akda chicken', '15.00', 'special_akda_chicken.webp'),
                ('Shakshouka', '12.00', 'special_shakshouka.webp'),
                ('Hummus only', '7.00', 'special_hummus.webp'),
                ('Hummus & bread', '10.00', 'special_hummus.webp'),
            ],
            'Cold Appetizers': [
                ('Arabic salad', '6.00', 'cold_arabic_salad.webp'),
                ('Fatush salad', '9.00', 'cold_fatush_salad.webp'),
                ('Sahawak cheese', '6.00', 'cold_sahawak_cheese.webp'),
                ('Garlic Sauce', '1.00', 'cold_garlic_sauce.webp'),
                ('Ratib with honey', '6.00', 'cold_ratib_honey.webp'),
                ('Bread malawah', '3.00', 'cold_bread_malawah.webp'),
            ],
            'Fresh Juices and Cold Drinks': [
                ('Apple juice', '6.00', 'juice_apple.webp'),
                ('Orang Juice', '6.00', 'juice_orang.webp'),
                ('Avocado juice', '10.00', 'juice_avocado.webp'),
                ('Carott Juice', '5.00', 'juice_carott.webp'),
                ('Watermelon', '6.00', 'juice_watermelon.webp'),
                ('Pineapple', '6.00', 'juice_pineapple.webp'),
                ('Banana juice', '6.00', 'juice_banana.webp'),
                ('Mango juice', '8.00', 'juice_mango.webp'),
                ('Ice lemon tea', '3.00', 'cold_ice_lemon_tea.webp'),
                ('Tea o ice', '2.00', 'cold_tea_o_ice.webp'),
                ('Sirap ice', '3.00', 'cold_sirap_ice.webp'),
                ('Lemon juice', '5.00', 'juice_lemon_mint.webp'),
                ('Lemon ment', '6.00', 'juice_lemon_mint.webp'),
                ('Milo ice', '4.00', 'cold_milo_ice.webp'),
                ('Sirap bandung', '4.00', 'cold_sirap_bandung.webp'),
            ],
            'Shawarma and Sandwiches': [
                ('Plate beef shawarma', '15.00', 'shawarma_plate_beef.webp'),
                ('Plate chicken shawarma', '12.00', 'shawarma_plate_chicken.webp'),
                ('Zinger plate with bread', '14.00', 'shawarma_plate_zinger.webp'),
                ('Falafel plate with bread', '8.00', 'shawarma_plate_falafel.webp'),
                ('3 pcs sambosa', '5.00', 'shawarma_sambosa.webp'),
                ('French fries', '5.00', 'shawarma_french_fries.webp'),
                ('Beef sandwich kabab', '9.00', 'shawarma_sandwich_beef_kabab.webp'),
                ('Chicken sandwich kabab', '7.00', 'shawarma_sandwich_chicken_kabab.webp'),
                ('Shish Tawook', '18.00', 'shawarma_shish_tawook.webp'),
                ('Beef shawarma (small)', '9.00', 'shawarma_wrap_beef.webp'),
                ('Beef shawarma (large)', '15.00', 'shawarma_wrap_beef.webp'),
                ('Chicken shawarma (small)', '7.00', 'shawarma_wrap_chicken.webp'),
                ('Chicken shawarma (large)', '13.00', 'shawarma_wrap_chicken.webp'),
            ],
            'Drinks': [
                ('Barbican', '7.00', 'drink_barbican.webp'),
                ('Soft drink', '2.00', 'drink_soft_drink.webp'),
                ('Mineral water', '1.00', 'drink_mineral_water.webp'),
            ],
            'Hot Drinks': [
                ('Arabic red tea', '2.00', 'hot_arabic_red_tea.webp'),
                ('Adni tea', '4.00', 'hot_adni_tea.webp'),
                ('Arabic red tea teapot', '6.00', 'hot_arabic_red_tea_teapot.webp'),
                ('Adni tea teapot', '12.00', 'hot_adni_tea_teapot.webp'),
            ],
            'Sweets': [
                ('Basbousa', '4.00', 'sweet_basbousa.webp'),
                ('Kunafa cheese', '15.00', 'sweet_kunafa.webp'),
                ('Kunafa cream', '10.00', 'sweet_kunafa.webp'),
                ('Massoub', '14.00', 'sweet_massoub.webp'),
                ('Fatta dates', '15.00', 'sweet_fatta_dates.webp'),
            ],
        }
        add_on_items = {
            'Beef shawarma (small)', 'Beef shawarma (large)',
            'Chicken shawarma (small)', 'Chicken shawarma (large)',
        }

        for category_name, menu_items in menu_catalog.items():
            category, _ = MenuCategory.objects.get_or_create(category_name=category_name)
            for name, price, image_filename in menu_items:
                description = 'Extra cheese + RM 1' if name in add_on_items else ''
                image_name = f'menu_items/catalog/{image_filename}'
                item = MenuItem.objects.filter(item_name=name).order_by('item_id').first()
                if item is None:
                    MenuItem.objects.create(
                        category=category,
                        item_name=name,
                        description=description,
                        price=Decimal(price),
                        image=image_name,
                        is_available=True,
                    )
                else:
                    item.category = category
                    item.item_name = name
                    item.description = description
                    item.price = Decimal(price)
                    item.image = image_name
                    item.is_available = True
                    item.save(update_fields=['category', 'item_name', 'description', 'price', 'image', 'is_available'])

        # Keep old demo dishes in order history, but remove them from the menu.
        legacy_items = [
            'Plate beef kebab', 'Plate chicken kebab', 'Plate mixed kebab',
            '1/4 chicken barbecue', 'Mix barbecue', '1/4 chicken barbecue with rice',
            'Kebab mix with rice', 'Shawarma beef with rice', 'Shawarma chicken with rice',
            'Lamb shank', 'Moffa fish and bread', 'Moffa fish and rice', 'Plate shish tawook',
            'Chicken kabsa', 'Mugalgal beef', 'Orange juice', 'Carrot juice',
            'Watermelon juice', 'Pineapple juice', 'Rutab with honey', 'Lemon mint',
            'Falafel sandwich', 'Sandwich zinger', 'Sandwich shish tawook',
        ]
        MenuItem.objects.filter(item_name__in=legacy_items).update(is_available=False)

        self.stdout.write(self.style.SUCCESS('\nDemo data seeding complete!'))
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('DEMO LOGINS:'))
        self.stdout.write(f'  Admin:      {admin.email}')
        if created:
            self.stdout.write('  Initial password: Admin1234! (change it after setup)')
        self.stdout.write('=' * 60)
