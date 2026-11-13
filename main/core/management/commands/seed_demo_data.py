"""
Management command: seed_demo_data
Seeds realistic demo orders, order items, and reservations with dates
relative to the current date. Re-running updates existing demo records
to keep dates fresh for live demonstrations and lecturer presentations.
"""
import random
from decimal import Decimal
from datetime import timedelta, time
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from accounts.models import Account
from menu.models import MenuItem
from orders.models import Order, OrderItem, RestaurantTable
from reservations.models import Reservation


# Tag used to identify demo-seeded orders (stored in delivery_address for non-delivery)
DEMO_TAG = '__DEMO_SEED__'


class Command(BaseCommand):
    help = (
        'Seeds realistic demo orders, order items, and reservations with dates '
        'relative to today. Safe to re-run: updates dates on existing demo data '
        'instead of creating duplicates.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete all demo-seeded orders and reservations before re-seeding.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        now = timezone.now()
        today = timezone.localdate()

        # ── Prerequisite checks ──────────────────────────────────────────
        customers = list(Account.objects.filter(role='customer').order_by('account_id')[:2])
        if len(customers) < 2:
            self.stderr.write(self.style.ERROR(
                'Need at least 2 customer accounts. Run seed_demo first.'
            ))
            return

        items = list(MenuItem.objects.filter(is_available=True).order_by('item_id'))
        if len(items) < 5:
            self.stderr.write(self.style.ERROR(
                'Need at least 5 available menu items. Run seed_demo first.'
            ))
            return

        tables = list(RestaurantTable.objects.filter(is_active=True).order_by('table_number')[:5])

        cust1, cust2 = customers[0], customers[1]

        # ── Optional clear ───────────────────────────────────────────────
        if options['clear']:
            deleted_orders, _ = Order.objects.filter(
                delivery_address__contains=DEMO_TAG
            ).delete()
            deleted_res, _ = Reservation.objects.filter(
                note__contains=DEMO_TAG
            ).delete()
            self.stdout.write(self.style.WARNING(
                f'Cleared {deleted_orders} demo order records and {deleted_res} demo reservations.'
            ))

        # ── Check if demo data already exists ────────────────────────────
        existing_orders = Order.objects.filter(delivery_address__contains=DEMO_TAG)
        is_update = existing_orders.exists()

        if is_update:
            self._update_dates(existing_orders, today, now)
            self._update_reservation_dates(today)
            self.stdout.write(self.style.SUCCESS(
                f'\nUpdated {existing_orders.count()} demo orders and '
                f'{Reservation.objects.filter(note__contains=DEMO_TAG).count()} demo reservations '
                f'to be relative to today ({today}).'
            ))
        else:
            self._create_demo_data(cust1, cust2, items, tables, today, now)
            self.stdout.write(self.style.SUCCESS(
                '\nDemo test data seeded successfully!'
            ))

        # ── Summary ──────────────────────────────────────────────────────
        self._print_summary(today)

    # ═════════════════════════════════════════════════════════════════════
    #  CREATE FRESH DEMO DATA
    # ═════════════════════════════════════════════════════════════════════
    def _create_demo_data(self, cust1, cust2, items, tables, today, now):
        self.stdout.write(self.style.NOTICE('Creating fresh demo orders and reservations...'))

        # ── Define 12 demo orders spread over 7 days ─────────────────────
        order_specs = [
            # (customer, days_ago, order_type, status, payment_method, payment_status, table_index, items_spec)
            # items_spec: list of (item_index, qty)

            # --- 6 days ago: completed delivery ---
            (cust1, 6, 'delivery', 'completed', 'sim_banking', 'paid', None, [(0, 2), (3, 1)]),
            # --- 5 days ago: completed takeaway ---
            (cust2, 5, 'takeaway', 'completed', 'cash', 'paid', None, [(1, 1), (5, 1)]),
            # --- 4 days ago: completed dine-in ---
            (cust1, 4, 'dine_in', 'completed', 'sim_ewallet', 'paid', 0, [(2, 1), (9, 1)]),
            # --- 3 days ago: completed delivery ---
            (cust2, 3, 'delivery', 'completed', 'sim_card', 'paid', None, [(6, 2), (14, 3)]),
            # --- 3 days ago: cancelled order ---
            (cust1, 3, 'takeaway', 'cancelled', 'cash', 'not_required', None, [(7, 1)]),
            # --- 2 days ago: completed dine-in ---
            (cust2, 2, 'dine_in', 'completed', 'cash', 'paid', 1, [(0, 1), (4, 1), (10, 2)]),
            # --- 2 days ago: ready takeaway ---
            (cust1, 2, 'takeaway', 'ready', 'sim_banking', 'paid', None, [(8, 2), (11, 1)]),
            # --- 1 day ago: preparing delivery ---
            (cust2, 1, 'delivery', 'preparing', 'sim_card', 'paid', None, [(3, 3), (13, 2)]),
            # --- 1 day ago: completed dine-in ---
            (cust1, 1, 'dine_in', 'completed', 'sim_ewallet', 'paid', 2, [(9, 1), (1, 2)]),
            # --- Today: pending delivery (cash, not paid yet) ---
            (cust1, 0, 'delivery', 'pending', 'cash', 'pending', None, [(0, 1), (15, 2)]),
            # --- Today: pending takeaway ---
            (cust2, 0, 'takeaway', 'pending', 'sim_banking', 'pending', None, [(4, 1), (6, 1)]),
            # --- Today: preparing dine-in ---
            (cust2, 0, 'dine_in', 'preparing', 'cash', 'pending', 3, [(2, 2), (8, 1), (12, 1)]),
        ]

        hours = [11, 12, 13, 14, 17, 18, 19, 20, 21, 12, 15, 19]

        for idx, spec in enumerate(order_specs):
            customer, days_ago, o_type, o_status, pay_method, pay_status, tbl_idx, items_spec = spec

            # Calculate order datetime
            order_day = today - timedelta(days=days_ago)
            hour = hours[idx % len(hours)]
            minute = random.randint(0, 59)
            order_dt = timezone.make_aware(
                timezone.datetime(order_day.year, order_day.month, order_day.day, hour, minute, 0)
            )

            # Get table reference if dine-in
            table = tables[tbl_idx] if (tbl_idx is not None and tbl_idx < len(tables)) else None

            # Compute total and delivery address
            total = Decimal('0.00')
            for item_idx, qty in items_spec:
                item = items[item_idx % len(items)]
                total += item.price * qty

            delivery_addr = None
            if o_type == 'delivery':
                delivery_addr = f'{customer.address} {DEMO_TAG}'
            else:
                delivery_addr = DEMO_TAG

            # Create order
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
                OrderItem.objects.create(
                    order=order,
                    item=item,
                    quantity=qty,
                    unit_price=item.price,
                )

            status_label = f'{o_status}/{pay_status}'
            self.stdout.write(
                f'  Order #{order.order_id}: {o_type} by {customer.full_name} '
                f'({order_day}, RM {total:.2f}) [{status_label}]'
            )

        # ── Demo reservations ────────────────────────────────────────────
        reservation_specs = [
            # (customer, days_offset, time, party_size, status, note)
            (cust1, -3, time(19, 0), 4, 'confirmed', f'Family dinner {DEMO_TAG}'),
            (cust2, -2, time(20, 30), 2, 'confirmed', f'Date night {DEMO_TAG}'),
            (cust1, -1, time(12, 0), 6, 'completed', f'Birthday lunch {DEMO_TAG}'),
            (cust2, 0, time(19, 30), 3, 'pending', f'Business meeting {DEMO_TAG}'),
            (cust1, 1, time(18, 0), 5, 'pending', f'Group gathering {DEMO_TAG}'),
            (cust2, 2, time(13, 0), 8, 'pending', f'Team celebration {DEMO_TAG}'),
            (cust1, 3, time(20, 0), 2, 'pending', f'Anniversary dinner {DEMO_TAG}'),
        ]

        for customer, days_offset, res_time, party, status, note in reservation_specs:
            res_date = today + timedelta(days=days_offset)
            Reservation.objects.create(
                account=customer,
                reservation_date=res_date,
                reservation_time=res_time,
                party_size=party,
                status=status,
                note=note,
            )
            self.stdout.write(
                f'  Reservation: {customer.full_name} on {res_date} at {res_time} '
                f'(party of {party}) [{status}]'
            )

    # ═════════════════════════════════════════════════════════════════════
    #  UPDATE EXISTING DEMO DATA DATES
    # ═════════════════════════════════════════════════════════════════════
    def _update_dates(self, existing_orders, today, now):
        """Shift all demo order dates so they remain relative to today."""
        self.stdout.write(self.style.NOTICE('Updating demo order dates to be relative to today...'))

        # Find the most recent demo order date to compute the shift
        latest_order = existing_orders.order_by('-order_date').first()
        if not latest_order:
            return

        latest_date = timezone.localdate(latest_order.order_date)
        shift = today - latest_date  # timedelta to add

        if shift.days == 0:
            self.stdout.write('  Orders are already up to date (no shift needed).')
            return

        # Shift all demo orders
        for order in existing_orders:
            new_date = order.order_date + shift
            Order.objects.filter(order_id=order.order_id).update(order_date=new_date)

        self.stdout.write(f'  Shifted {existing_orders.count()} demo orders by {shift.days} day(s).')

    def _update_reservation_dates(self, today):
        """Shift all demo reservation dates to remain relative to today."""
        demo_reservations = Reservation.objects.filter(note__contains=DEMO_TAG)
        if not demo_reservations.exists():
            return

        self.stdout.write(self.style.NOTICE('Updating demo reservation dates to be relative to today...'))

        # Find the latest reservation date to compute the shift
        latest_res = demo_reservations.order_by('-reservation_date').first()
        if not latest_res:
            return

        # The furthest-future reservation should be today + 3
        target_latest = today + timedelta(days=3)
        shift = target_latest - latest_res.reservation_date

        if shift.days == 0:
            self.stdout.write('  Reservations are already up to date (no shift needed).')
            return

        for res in demo_reservations:
            new_date = res.reservation_date + shift
            Reservation.objects.filter(reservation_id=res.reservation_id).update(
                reservation_date=new_date
            )

        self.stdout.write(f'  Shifted {demo_reservations.count()} demo reservations by {shift.days} day(s).')

    # ═════════════════════════════════════════════════════════════════════
    #  SUMMARY OUTPUT
    # ═════════════════════════════════════════════════════════════════════
    def _print_summary(self, today):
        demo_orders = Order.objects.filter(delivery_address__contains=DEMO_TAG)
        demo_reservations = Reservation.objects.filter(note__contains=DEMO_TAG)

        from django.db.models import Sum
        paid_result = demo_orders.filter(
            payment_status='paid'
        ).exclude(
            order_status='cancelled'
        ).aggregate(total=Sum('total_amount'))
        paid_total = paid_result['total'] or Decimal('0.00')

        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('DEMO DATA SUMMARY'))
        self.stdout.write(f'  Today:              {today}')
        self.stdout.write(f'  Demo orders:        {demo_orders.count()}  (paid total: RM {paid_total:.2f})')
        self.stdout.write(f'  Demo reservations:  {demo_reservations.count()}')
        self.stdout.write('')
        self.stdout.write('  Order date range:')

        for order in demo_orders.order_by('order_date'):
            dt = timezone.localdate(order.order_date)
            delta = (today - dt).days
            day_label = 'today' if delta == 0 else f'{delta}d ago'
            self.stdout.write(
                f'    #{order.order_id:3d}  {dt}  ({day_label:>7s})  '
                f'{order.order_type:<10s}  {order.order_status:<12s}  '
                f'RM {order.total_amount:>7.2f}  [{order.payment_status}]'
            )

        self.stdout.write('')
        self.stdout.write('  Reservation dates:')
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
                f'party of {res.party_size}  [{res.status}]'
            )

        self.stdout.write('=' * 60)
        self.stdout.write(self.style.NOTICE(
            'Tip: Run again anytime to refresh dates. Use --clear to wipe and re-seed.'
        ))

