import secrets
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import Account
from core.models import RestaurantDemoSeedRecord
from menu.models import MenuCategory, MenuItem
from orders.models import RestaurantTable


class Command(BaseCommand):
    help = 'Seeds restaurant data (categories, menu items, and tables) plus the demo admin account.'

    SEED_KEY = 'restaurant_demo'
    ACCOUNT_RECORD = 'account'
    CATEGORY_RECORD = 'menu_category'
    MENU_ITEM_RECORD = 'menu_item'
    TABLE_RECORD = 'restaurant_table'

    def add_arguments(self, parser):
        mode_group = parser.add_mutually_exclusive_group()
        mode_group.add_argument(
            '--delete',
            action='store_true',
            help=(
                'Remove unused demo-seed-owned menu rows, tables, and the demo admin account, '
                'then exit. Seeded rows with order or reservation history are retained safely.'
            ),
        )
        mode_group.add_argument(
            '--adopt-existing',
            action='store_true',
            help=(
                'Explicitly record ownership of legacy demo tables 1-10 and the canonical demo admin '
                'after a normal seed run, so a later --delete can clean them safely.'
            ),
        )

    def _mark_seed_owned(self, object_type, obj):
        RestaurantDemoSeedRecord.objects.get_or_create(
            seed_key=self.SEED_KEY,
            object_type=object_type,
            object_id=obj.pk,
        )

    def _is_seed_owned(self, object_type, obj):
        return RestaurantDemoSeedRecord.objects.filter(
            seed_key=self.SEED_KEY,
            object_type=object_type,
            object_id=obj.pk,
        ).exists()

    def _seed_record_ids(self, object_type):
        return RestaurantDemoSeedRecord.objects.filter(
            seed_key=self.SEED_KEY,
            object_type=object_type,
        ).values_list('object_id', flat=True)

    @transaction.atomic
    def handle(self, *args, **options):
        if options['delete']:
            self._delete_seeded_data()
            return
        if options['adopt_existing']:
            self._adopt_existing_seeded_data()
            return

        self.stdout.write(self.style.NOTICE('Seeding demo data...'))

        # 1. Seed Accounts
        admin, admin_created = Account.objects.get_or_create(
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
        if admin_created:
            admin.set_password('Admin1234!')
            admin.save()
            self._mark_seed_owned(self.ACCOUNT_RECORD, admin)
            self.stdout.write(self.style.SUCCESS(f'Created admin account: {admin.email}'))
        elif self._is_seed_owned(self.ACCOUNT_RECORD, admin):
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
        else:
            self.stdout.write(self.style.WARNING(
                f'Skipped existing unowned account: {admin.email}'
            ))

        # 2. Seed Restaurant Tables (10 tables with random qr_token)
        for num in range(1, 11):
            table, table_created = RestaurantTable.objects.get_or_create(
                table_number=num,
                defaults={
                    'qr_token': secrets.token_urlsafe(16),
                    'is_active': True,
                }
            )
            if table_created:
                self._mark_seed_owned(self.TABLE_RECORD, table)
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
            category, _ = MenuCategory.objects.get_or_create(
                category_name=category_name
            )
            # The seed already refreshes these named catalog records, so it can
            # safely claim them on the first run after ownership tracking ships.
            self._mark_seed_owned(self.CATEGORY_RECORD, category)
            for name, price, image_filename in menu_items:
                description = 'Extra cheese + RM 1' if name in add_on_items else ''
                image_name = f'menu_items/catalog/{image_filename}'
                item = MenuItem.objects.filter(item_name=name).order_by('item_id').first()
                if item is None:
                    item = MenuItem.objects.create(
                        category=category,
                        item_name=name,
                        description=description,
                        price=Decimal(price),
                        image=image_name,
                        is_available=True,
                    )
                    self._mark_seed_owned(self.MENU_ITEM_RECORD, item)
                else:
                    item.category = category
                    item.item_name = name
                    item.description = description
                    item.price = Decimal(price)
                    item.image = image_name
                    item.is_available = True
                    item.save(update_fields=['category', 'item_name', 'description', 'price', 'image', 'is_available'])
                self._mark_seed_owned(self.MENU_ITEM_RECORD, item)

        self.stdout.write(self.style.SUCCESS('\nDemo data seeding complete!'))
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('DEMO LOGINS:'))
        self.stdout.write(f'  Admin:      {admin.email}')
        if admin_created:
            self.stdout.write('  Initial password: Admin1234! (change it after setup)')
        self.stdout.write('=' * 60)

    def _adopt_existing_seeded_data(self):
        """Explicitly transfer known legacy demo fixtures to tracked ownership."""
        adopted_table_count = 0
        adopted_admin_count = 0

        # Tables were historically created solely by their numbers. Adoption is
        # opt-in because table numbers may have since been repurposed by a user.
        for table in RestaurantTable.objects.filter(table_number__range=(1, 10)):
            if not self._is_seed_owned(self.TABLE_RECORD, table):
                self._mark_seed_owned(self.TABLE_RECORD, table)
                adopted_table_count += 1

        # Only the original canonical demo account is eligible for adoption.
        demo_admins = Account.objects.filter(
            email='admin@gmail.com',
            full_name='Demo Admin',
            role='admin',
            is_staff=False,
            is_superuser=False,
        )
        for demo_admin in demo_admins:
            if not self._is_seed_owned(self.ACCOUNT_RECORD, demo_admin):
                self._mark_seed_owned(self.ACCOUNT_RECORD, demo_admin)
                adopted_admin_count += 1

        self.stdout.write(self.style.WARNING(
            'Adopted legacy demo ownership for '
            f'{adopted_table_count} table(s) and {adopted_admin_count} canonical admin account(s).'
        ))
        self.stdout.write(self.style.SUCCESS(
            'Run the normal seed command first to claim catalog rows, then use --delete when ready. '
            'Only run --adopt-existing after confirming tables 1-10 are legacy demo tables.'
        ))

    def _delete_seeded_data(self):
        """Delete seed-owned rows without breaking order or reservation history."""
        catalog_items = MenuItem.objects.filter(
            item_id__in=self._seed_record_ids(self.MENU_ITEM_RECORD)
        )
        category_ids = self._seed_record_ids(self.CATEGORY_RECORD)

        historical_items = catalog_items.filter(order_items__isnull=False).distinct()
        historical_item_count = historical_items.count()
        historical_items.update(is_available=False)

        removable_items = catalog_items.filter(order_items__isnull=True)
        removed_item_count = removable_items.count()
        removable_item_ids = list(removable_items.values_list('item_id', flat=True))
        removable_items.delete()
        RestaurantDemoSeedRecord.objects.filter(
            seed_key=self.SEED_KEY,
            object_type=self.MENU_ITEM_RECORD,
            object_id__in=removable_item_ids,
        ).delete()

        removable_categories = MenuCategory.objects.filter(
            category_id__in=category_ids,
            items__isnull=True,
        )
        removed_category_count = removable_categories.count()
        removable_category_ids = list(removable_categories.values_list('category_id', flat=True))
        removable_categories.delete()
        RestaurantDemoSeedRecord.objects.filter(
            seed_key=self.SEED_KEY,
            object_type=self.CATEGORY_RECORD,
            object_id__in=removable_category_ids,
        ).delete()

        seeded_tables = RestaurantTable.objects.filter(
            table_id__in=self._seed_record_ids(self.TABLE_RECORD)
        )
        historical_tables = seeded_tables.filter(orders__isnull=False).distinct()
        historical_table_count = historical_tables.count()
        historical_tables.update(is_active=False)

        removable_tables = seeded_tables.filter(orders__isnull=True)
        removed_table_count = removable_tables.count()
        removable_table_ids = list(removable_tables.values_list('table_id', flat=True))
        removable_tables.delete()
        RestaurantDemoSeedRecord.objects.filter(
            seed_key=self.SEED_KEY,
            object_type=self.TABLE_RECORD,
            object_id__in=removable_table_ids,
        ).delete()

        demo_admins = list(Account.objects.filter(
            account_id__in=self._seed_record_ids(self.ACCOUNT_RECORD)
        ))
        removed_admin_count = 0
        retained_admin_count = 0
        removed_admin_ids = []
        for demo_admin in demo_admins:
            if demo_admin.orders.exists() or demo_admin.reservations.exists():
                demo_admin.is_active = False
                demo_admin.save(update_fields=['is_active'])
                retained_admin_count += 1
            else:
                removed_admin_ids.append(demo_admin.account_id)
                demo_admin.delete()
                removed_admin_count += 1
        RestaurantDemoSeedRecord.objects.filter(
            seed_key=self.SEED_KEY,
            object_type=self.ACCOUNT_RECORD,
            object_id__in=removed_admin_ids,
        ).delete()

        self.stdout.write(self.style.WARNING(
            'Deleted '
            f'{removed_item_count} unused seeded menu items, '
            f'{removed_category_count} empty seeded categories, '
            f'{removed_table_count} unused seeded tables, and '
            f'{removed_admin_count} demo admin account(s).'
        ))
        if historical_item_count or historical_table_count or retained_admin_count:
            self.stdout.write(self.style.WARNING(
                'Retained history-linked data safely: '
                f'{historical_item_count} menu item(s) marked unavailable, '
                f'{historical_table_count} table(s) marked inactive, and '
                f'{retained_admin_count} admin account(s) deactivated.'
            ))
        self.stdout.write(self.style.SUCCESS(
            'Restaurant demo cleanup complete. Catalog image files were not removed.'
        ))
