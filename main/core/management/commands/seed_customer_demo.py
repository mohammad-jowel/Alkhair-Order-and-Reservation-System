"""
Management command: seed_customer_demo
Creates 5 demo customer accounts, then seeds realistic orders, order items,
and reservations with dates relative to the current date.
Re-running updates existing demo records to keep dates fresh.
"""
from decimal import Decimal
from datetime import timedelta, time
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from accounts.models import Account
from menu.models import MenuItem
from orders.models import Order, OrderItem, RestaurantTable
from reservations.models import Reservation


# Tag to identify demo-seeded records
DEMO_TAG = '__DEMO_SEED__'
DEMO_PASSWORD = 'Customer1234!'
EXPECTED_DEMO_ORDERS = 15
EXPECTED_DEMO_ORDER_ITEMS = 30
EXPECTED_DEMO_RESERVATIONS = 8

# 5 demo customers with realistic Malaysian details
DEMO_CUSTOMERS = [
    {
        'email': 'customer1@demo.com',
        'full_name': 'Customer 1',
        'phone': '+60191000001',
        'address': 'No. 1, Jalan Demo, Parit Raja, 86400 Batu Pahat, Johor',
    },
    {
        'email': 'customer2@demo.com',
        'full_name': 'Customer 2',
        'phone': '+60191000002',
        'address': 'No. 2, Jalan Demo, Parit Raja, 86400 Batu Pahat, Johor',
    },
    {
        'email': 'customer3@demo.com',
        'full_name': 'Customer 3',
        'phone': '+60191000003',
        'address': 'No. 3, Jalan Demo, Parit Raja, 86400 Batu Pahat, Johor',
    },
    {
        'email': 'customer4@demo.com',
        'full_name': 'Customer 4',
        'phone': '+60191000004',
        'address': 'No. 4, Jalan Demo, Parit Raja, 86400 Batu Pahat, Johor',
    },
    {
        'email': 'customer5@demo.com',
        'full_name': 'Customer 5',
        'phone': '+60191000005',
        'address': 'No. 5, Jalan Demo, Parit Raja, 86400 Batu Pahat, Johor',
    },
]
DEMO_EMAILS = tuple(customer['email'] for customer in DEMO_CUSTOMERS)


class Command(BaseCommand):
    help = (
        'Creates 5 demo customers and seeds orders, order items, and '
        'reservations with dates relative to today. Safe to re-run.'
    )

    def add_arguments(self, parser):
        seed_action = parser.add_mutually_exclusive_group()
        seed_action.add_argument(
            '--clear',
            action='store_true',
            help='Delete activity for the five demo customers and re-seed it.',
        )
        seed_action.add_argument(
            '--delete',
            action='store_true',
            help=(
                'Delete orders/reservations for the five demo customers and their accounts, then exit.'
            ),
        )

    @transaction.atomic
    def handle(self, *args, **options):
        # Use Django's configured local timezone so each run anchors records
        # to the restaurant's current calendar date.
        today = timezone.localdate()

        # ── Delete seeded activity and safe-to-remove demo accounts ──────
        if options['delete']:
            # Match by marker and by dedicated demo account. The account match
            # also cleans records from older seed versions if a marker was lost.
            demo_orders = self._demo_orders(include_customer_activity=True)
            demo_reservations = self._demo_reservations(include_customer_activity=True)
            order_count = demo_orders.count()
            reservation_count = demo_reservations.count()
            account_count = Account.objects.filter(email__in=DEMO_EMAILS).count()
            demo_orders.delete()
            demo_reservations.delete()
            Account.objects.filter(email__in=DEMO_EMAILS).delete()
            self.stdout.write(self.style.WARNING(
                f'Deleted {order_count} demo orders, {reservation_count} demo reservations, '
                f'and {account_count} demo customer accounts.'
            ))
            self.stdout.write(self.style.SUCCESS('Demo customer cleanup complete.'))
            return

        # ── 1. Create demo customer accounts ─────────────────────────────
        customers = self._ensure_demo_customers()

        # ── 2. Ensure the restaurant seed has supplied enough menu items and tables.
        items = list(MenuItem.objects.filter(is_available=True).order_by('item_id'))
        tables = list(RestaurantTable.objects.filter(is_active=True).order_by('table_number')[:5])
        if len(items) < 16 or len(tables) < 4:
            self.stdout.write(self.style.WARNING(
                'Restaurant menu or tables are incomplete. Running seed_restaurant_demo...'
            ))
            call_command('seed_restaurant_demo', stdout=self.stdout, stderr=self.stderr)
            items = list(MenuItem.objects.filter(is_available=True).order_by('item_id'))
            tables = list(RestaurantTable.objects.filter(is_active=True).order_by('table_number')[:5])
        if len(items) < 16:
            raise CommandError('At least 16 available menu items are required to seed demo orders.')
        if len(tables) < 4:
            raise CommandError('At least 4 active restaurant tables are required to seed demo orders.')

        # ── 4. Optional clear ────────────────────────────────────────────
        if options['clear']:
            demo_orders = self._demo_orders(include_customer_activity=True)
            demo_reservations = self._demo_reservations(include_customer_activity=True)
            order_count = demo_orders.count()
            reservation_count = demo_reservations.count()
            demo_orders.delete()
            demo_reservations.delete()
            self.stdout.write(self.style.WARNING(
                f'Cleared {order_count} demo orders and {reservation_count} demo reservations.'
            ))

        # ── 5. Create or update demo data ────────────────────────────────
        existing_orders = self._demo_orders()
        existing_reservations = self._demo_reservations()
        orders_count = existing_orders.count()
        order_items_count = OrderItem.objects.filter(
            order__delivery_address__contains=DEMO_TAG
        ).count()
        reservations_count = existing_reservations.count()

        if (orders_count == EXPECTED_DEMO_ORDERS
                and order_items_count == EXPECTED_DEMO_ORDER_ITEMS
                and reservations_count == EXPECTED_DEMO_RESERVATIONS):
            self._update_dates(existing_orders, today)
            self._update_reservation_dates(today)
            self.stdout.write(self.style.SUCCESS(
                f'\nUpdated {orders_count} demo orders and {reservations_count} demo reservations '
                f'to be relative to today ({today}).'
            ))
        else:
            if orders_count or reservations_count:
                self.stdout.write(self.style.WARNING(
                    'Existing demo activity is incomplete; rebuilding it to avoid duplicates.'
                ))
                existing_orders.delete()
                existing_reservations.delete()
            self._create_demo_data(customers, items, tables, today)
            self.stdout.write(self.style.SUCCESS(
                '\nDemo test data seeded successfully!'
            ))

        # ── 6. Summary ──────────────────────────────────────────────────
        self._print_summary(today, customers)

    def _demo_orders(self, include_customer_activity=False):
        query = Q(delivery_address__contains=DEMO_TAG)
        if include_customer_activity:
            query |= Q(account__email__in=DEMO_EMAILS)
        return Order.objects.filter(query)

    def _demo_reservations(self, include_customer_activity=False):
        query = Q(note__contains=DEMO_TAG)
        if include_customer_activity:
            query |= Q(account__email__in=DEMO_EMAILS)
        return Reservation.objects.filter(query)

    # ═════════════════════════════════════════════════════════════════════
    #  CREATE / ENSURE DEMO CUSTOMERS
    # ═════════════════════════════════════════════════════════════════════
    def _ensure_demo_customers(self):
        """Create 5 demo customer accounts if they don't exist."""
        customers = []
        for info in DEMO_CUSTOMERS:
            account, created = Account.objects.get_or_create(
                email=info['email'],
                defaults={
                    'full_name': info['full_name'],
                    'phone': info['phone'],
                    'address': info['address'],
                    'role': 'customer',
                }
            )
            if created:
                account.set_password(DEMO_PASSWORD)
                account.save()
                self.stdout.write(self.style.SUCCESS(
                    f'  Created demo customer: {info["email"]} ({info["full_name"]})'
                ))
            changed_fields = []
            for field, value in (
                ('full_name', info['full_name']),
                ('role', 'customer'),
                ('is_active', True),
                ('is_staff', False),
                ('is_superuser', False),
            ):
                if getattr(account, field) != value:
                    setattr(account, field, value)
                    changed_fields.append(field)
            if changed_fields:
                account.save(update_fields=changed_fields)
            account.groups.clear()
            account.user_permissions.clear()
            customers.append(account)
        return customers

    # ═════════════════════════════════════════════════════════════════════
    #  CREATE FRESH DEMO DATA
    # ═════════════════════════════════════════════════════════════════════
    def _create_demo_data(self, customers, items, tables, today):
        self.stdout.write(self.style.NOTICE('Creating demo orders and reservations...'))

        c1, c2, c3, c4, c5 = customers

        # 15 demo orders spread over the past 7 days (this week)
        # (customer, days_ago, order_type, status, payment, pay_status, table_idx, items_spec)
        order_specs = [
            # 6 days ago
            (c1, 6, 'delivery',  'completed', 'sim_banking', 'paid',         None, [(0, 2), (3, 1)]),
            (c3, 6, 'takeaway',  'completed', 'cash',        'paid',         None, [(5, 1), (7, 1)]),
            # 5 days ago
            (c2, 5, 'takeaway',  'completed', 'cash',        'paid',         None, [(1, 1), (5, 1)]),
            # 4 days ago
            (c4, 4, 'dine_in',   'completed', 'sim_ewallet', 'paid',         0,    [(2, 1), (9, 1)]),
            # 3 days ago
            (c5, 3, 'delivery',  'completed', 'sim_card',    'paid',         None, [(6, 2), (14, 3)]),
            (c1, 3, 'takeaway',  'cancelled', 'cash',        'not_required', None, [(7, 1)]),
            # 2 days ago
            (c2, 2, 'dine_in',   'completed', 'cash',        'paid',         1,    [(0, 1), (4, 1), (10, 2)]),
            (c3, 2, 'takeaway',  'ready',     'sim_banking', 'paid',         None, [(8, 2), (11, 1)]),
            # 1 day ago
            (c4, 1, 'delivery',  'preparing', 'sim_card',    'paid',         None, [(3, 3), (13, 2)]),
            (c5, 1, 'dine_in',   'completed', 'sim_ewallet', 'paid',         2,    [(9, 1), (1, 2)]),
            (c1, 1, 'takeaway',  'completed', 'cash',        'paid',         None, [(4, 1)]),
            # Today
            (c2, 0, 'delivery',  'completed', 'sim_banking', 'paid',         None, [(0, 1), (15, 2)]),
            (c3, 0, 'takeaway',  'ready',     'sim_ewallet', 'paid',         None, [(4, 1), (6, 1)]),
            (c4, 0, 'dine_in',   'preparing', 'cash',        'pending',      3,    [(2, 2), (8, 1), (12, 1)]),
            (c5, 0, 'delivery',  'pending',   'sim_banking', 'pending',      None, [(1, 1), (3, 1)]),
        ]

        hours = [11, 12, 13, 14, 17, 18, 19, 20, 21, 12, 15, 19, 11, 13, 18]

        demo_order_items = []
        for idx, spec in enumerate(order_specs):
            customer, days_ago, o_type, o_status, pay_method, pay_status, tbl_idx, items_spec = spec

            order_day = today - timedelta(days=days_ago)
            hour = hours[idx % len(hours)]
            minute = (idx * 7) % 60
            order_dt = timezone.make_aware(
                timezone.datetime(order_day.year, order_day.month, order_day.day, hour, minute, 0)
            )

            table = tables[tbl_idx] if (tbl_idx is not None and tbl_idx < len(tables)) else None

            # Compute total
            total = Decimal('0.00')
            for item_idx, qty in items_spec:
                item = items[item_idx % len(items)]
                total += item.price * qty

            # Delivery address with demo tag
            if o_type == 'delivery':
                delivery_addr = f'{customer.address} {DEMO_TAG}'
            else:
                delivery_addr = DEMO_TAG

            order = Order.objects.create(
                account=customer,
                table=table,
                order_type=o_type,
                delivery_address=delivery_addr,
                order_status=o_status,
                payment_method=pay_method,
                payment_status=pay_status,
                total_amount=total,
            )

            # Override auto_now_add date
            Order.objects.filter(order_id=order.order_id).update(order_date=order_dt)

            # Create order items
            for item_idx, qty in items_spec:
                item = items[item_idx % len(items)]
                demo_order_items.append(OrderItem(
                    order=order, item=item, quantity=qty, unit_price=item.price,
                ))

            self.stdout.write(
                f'  Order #{order.order_id}: {o_type} by {customer.full_name} '
                f'({order_day}, RM {total:.2f}) [{o_status}/{pay_status}]'
            )

        OrderItem.objects.bulk_create(demo_order_items)

        # ── Demo reservations (spread across all 5 customers) ────────────
        reservation_specs = [
            # (customer, days_offset, time, party_size, status, note)
            (c1, -3, time(19, 0),  4, 'confirmed', f'Family dinner {DEMO_TAG}'),
            (c3, -2, time(20, 30), 2, 'confirmed', f'Friends meetup {DEMO_TAG}'),
            (c2, -1, time(12, 0),  6, 'cancelled', f'Birthday lunch {DEMO_TAG}'),
            (c4,  0, time(19, 30), 3, 'pending',   f'Business meeting {DEMO_TAG}'),
            (c5,  1, time(18, 0),  5, 'pending',   f'Group gathering {DEMO_TAG}'),
            (c1,  2, time(13, 0),  8, 'pending',   f'Team celebration {DEMO_TAG}'),
            (c2,  3, time(20, 0),  2, 'pending',   f'Anniversary dinner {DEMO_TAG}'),
            (c3,  4, time(12, 30), 4, 'pending',   f'Weekend brunch {DEMO_TAG}'),
        ]

        demo_reservations = []
        for customer, days_offset, res_time, party, status, note in reservation_specs:
            res_date = today + timedelta(days=days_offset)
            reservation = Reservation.objects.create(
                account=customer,
                reservation_date=res_date,
                reservation_time=res_time,
                party_size=party,
                status=status,
                note=note,
            )
            created_day = min(today, res_date - timedelta(days=1))
            reservation.created_at = timezone.make_aware(
                timezone.datetime(
                    created_day.year, created_day.month, created_day.day, 10, 0, 0
                )
            )
            demo_reservations.append(reservation)
            self.stdout.write(
                f'  Reservation: {customer.full_name} on {res_date} at {res_time} '
                f'(party of {party}) [{status}]'
            )
        Reservation.objects.bulk_update(demo_reservations, ['created_at'])

    # ═════════════════════════════════════════════════════════════════════
    #  UPDATE EXISTING DEMO DATA DATES
    # ═════════════════════════════════════════════════════════════════════
    def _update_dates(self, existing_orders, today):
        """Shift all demo order dates so they remain relative to today."""
        self.stdout.write(self.style.NOTICE('Updating demo order dates...'))

        latest_order = existing_orders.order_by('-order_date').first()
        if not latest_order:
            return

        latest_date = timezone.localdate(latest_order.order_date)
        shift = today - latest_date

        if shift.days == 0:
            self.stdout.write('  Orders are already up to date (no shift needed).')
            return

        orders = list(existing_orders)
        for order in orders:
            order.order_date += shift
        Order.objects.bulk_update(orders, ['order_date'])

        self.stdout.write(f'  Shifted {len(orders)} demo orders by {shift.days} day(s).')

    def _update_reservation_dates(self, today):
        """Shift all demo reservation dates to remain relative to today."""
        demo_res = Reservation.objects.filter(note__contains=DEMO_TAG)
        if not demo_res.exists():
            return

        self.stdout.write(self.style.NOTICE('Updating demo reservation dates...'))

        latest = demo_res.order_by('-reservation_date').first()
        if not latest:
            return

        # Furthest-future reservation anchored to today + 4
        target_latest = today + timedelta(days=4)
        shift = target_latest - latest.reservation_date

        if shift.days == 0:
            self.stdout.write('  Reservations are already up to date (no shift needed).')
            return

        reservations = list(demo_res)
        for res in reservations:
            res.reservation_date += shift
            res.created_at += shift
        Reservation.objects.bulk_update(reservations, ['reservation_date', 'created_at'])

        self.stdout.write(f'  Shifted {len(reservations)} demo reservations by {shift.days} day(s).')

    # ═════════════════════════════════════════════════════════════════════
    #  SUMMARY OUTPUT
    # ═════════════════════════════════════════════════════════════════════
    def _print_summary(self, today, customers):
        demo_orders = Order.objects.filter(delivery_address__contains=DEMO_TAG)
        demo_reservations = Reservation.objects.filter(note__contains=DEMO_TAG)

        from django.db.models import Sum
        paid_total = demo_orders.filter(
            payment_status='paid'
        ).exclude(
            order_status='cancelled'
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('DEMO DATA SUMMARY'))
        self.stdout.write(f'  Today:              {today}')
        self.stdout.write(f'  Demo customers:     {len(customers)}')
        self.stdout.write(f'  Demo orders:        {demo_orders.count()}  (paid: RM {paid_total:.2f})')
        self.stdout.write(f'  Demo reservations:  {demo_reservations.count()}')

        # Customer login list
        self.stdout.write('')
        self.stdout.write('  Demo logins (password: Customer1234!):')
        for c in customers:
            self.stdout.write(f'    {c.email:<22s}  {c.full_name}')

        # Orders table
        self.stdout.write('')
        self.stdout.write('  Orders:')
        for order in demo_orders.order_by('order_date'):
            dt = timezone.localdate(order.order_date)
            delta = (today - dt).days
            day_label = 'today' if delta == 0 else f'{delta}d ago'
            name = order.account.full_name[:15]
            self.stdout.write(
                f'    #{order.order_id:3d}  {dt}  ({day_label:>7s})  '
                f'{name:<15s}  {order.order_type:<10s}  {order.order_status:<12s}  '
                f'RM {order.total_amount:>7.2f}  [{order.payment_status}]'
            )

        # Reservations table
        self.stdout.write('')
        self.stdout.write('  Reservations:')
        for res in demo_reservations.order_by('reservation_date'):
            delta = (res.reservation_date - today).days
            if delta == 0:
                day_label = 'today'
            elif delta > 0:
                day_label = f'in {delta}d'
            else:
                day_label = f'{abs(delta)}d ago'
            self.stdout.write(
                f'    #{res.reservation_id:3d}  {res.reservation_date}  ({day_label:>7s})  '
                f'{res.account.full_name:<15s}  party of {res.party_size}  [{res.status}]'
            )

        self.stdout.write('=' * 60)
        self.stdout.write(self.style.NOTICE(
            'Tip: Run again to refresh dates. Use --clear to wipe and re-seed.'
        ))
