import csv
import json
from decimal import Decimal
from datetime import datetime, timedelta
from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum, Count, F
from accounts.decorators import admin_required
from accounts.models import Account
from orders.models import Order, OrderItem
from reservations.models import Reservation


def _parse_date_range(request):
    """Helper to parse and sanitize start_date and end_date query parameters."""
    start_date_str = request.GET.get('start_date', '').strip()
    end_date_str = request.GET.get('end_date', '').strip()

    start_date = None
    end_date = None

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            start_date = None

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            end_date = None

    if start_date and end_date and start_date > end_date:
        start_date, end_date = end_date, start_date

    return start_date, end_date, start_date_str, end_date_str


@admin_required
def dashboard(request):
    """
    Admin dashboard calculating metrics via Django ORM aggregation.
    Displays summary cards, sales Chart.js chart, best-selling items,
    orders by type, recent orders, and pending reservations.
    Supports optional date filtering via ?start_date=YYYY-MM-DD and ?end_date=YYYY-MM-DD.
    """
    today = timezone.localdate()
    start_date, end_date, _, _ = _parse_date_range(request)
    is_filtered = bool(start_date or end_date)

    # 1. Summary Cards (Standard Anchored Metrics)
    # Sales Total Rule: sum of total_amount for orders with payment_status = 'paid' and order_status != 'cancelled'
    today_sales = Order.objects.filter(
        order_date__date=today,
        payment_status='paid'
    ).exclude(order_status='cancelled').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    this_month_sales = Order.objects.filter(
        order_date__year=today.year,
        order_date__month=today.month,
        payment_status='paid'
    ).exclude(order_status='cancelled').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    total_sales_all_time = Order.objects.filter(
        payment_status='paid'
    ).exclude(order_status='cancelled').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    total_orders_count = Order.objects.count()
    pending_orders_count = Order.objects.filter(order_status='pending').count()
    total_customers_count = Account.objects.filter(role='customer').count()
    pending_reservations_count = Reservation.objects.filter(status='pending').count()

    # Filtered Orders Base QuerySet
    filtered_orders = Order.objects.all()
    if start_date:
        filtered_orders = filtered_orders.filter(order_date__date__gte=start_date)
    if end_date:
        filtered_orders = filtered_orders.filter(order_date__date__lte=end_date)

    period_sales = filtered_orders.filter(
        payment_status='paid'
    ).exclude(order_status='cancelled').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    period_orders_count = filtered_orders.count()

    # 2. Sales per day for the Chart.js line chart
    labels_chart = []
    sales_chart = []

    if is_filtered and start_date and end_date and (end_date - start_date).days <= 31:
        curr = start_date
        while curr <= end_date:
            day_sales = Order.objects.filter(
                order_date__date=curr,
                payment_status='paid'
            ).exclude(order_status='cancelled').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            labels_chart.append(curr.strftime('%d %b'))
            sales_chart.append(float(day_sales))
            curr += timedelta(days=1)
        chart_title = f"Daily Sales Trend ({start_date.strftime('%d %b %Y')} – {end_date.strftime('%d %b %Y')})"
    else:
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_sales = Order.objects.filter(
                order_date__date=day,
                payment_status='paid'
            ).exclude(order_status='cancelled').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            labels_chart.append(day.strftime('%d %b'))
            sales_chart.append(float(day_sales))
        chart_title = "Daily Sales Trend (Last 7 Days)"

    # 3. Best-Selling Menu Items (Top 5 by quantity sold in filtered period)
    # Join 1: order_item -> menu_item -> menu_category
    best_selling_items = OrderItem.objects.filter(
        order__in=filtered_orders,
        order__payment_status='paid'
    ).exclude(
        order__order_status='cancelled'
    ).values(
        'item__item_id',
        'item__item_name',
        'item__category__category_name',
        'item__price'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('unit_price'))
    ).order_by('-total_quantity')[:5]

    # 4. Orders by Type (in filtered period)
    type_counts_raw = filtered_orders.values('order_type').annotate(count=Count('order_id'))
    type_counts = {item['order_type']: item['count'] for item in type_counts_raw}
    orders_by_type = [
        {'label': 'Dine-in', 'count': type_counts.get('dine_in', 0), 'badge': 'bg-warning text-dark'},
        {'label': 'Delivery', 'count': type_counts.get('delivery', 0), 'badge': 'bg-info text-dark'},
        {'label': 'Takeaway', 'count': type_counts.get('takeaway', 0), 'badge': 'bg-secondary'},
    ]

    # 5. Recent Orders (matching filtered period, up to 10)
    recent_orders = filtered_orders.select_related('account', 'table').prefetch_related('items__item').order_by('-order_date')[:10]

    # 6. Top Customers by Spending (in filtered period)
    top_customers = Account.objects.filter(
        role='customer',
        orders__in=filtered_orders,
        orders__payment_status='paid'
    ).exclude(
        orders__order_status='cancelled'
    ).annotate(
        total_spent=Sum('orders__total_amount'),
        order_count=Count('orders', distinct=True)
    ).order_by('-total_spent')[:5]

    context = {
        'today_sales': today_sales,
        'this_month_sales': this_month_sales,
        'total_sales_all_time': total_sales_all_time,
        'period_sales': period_sales,
        'period_orders_count': period_orders_count,
        'total_orders_count': total_orders_count,
        'pending_orders_count': pending_orders_count,
        'total_customers_count': total_customers_count,
        'pending_reservations_count': pending_reservations_count,
        'start_date': start_date.strftime('%Y-%m-%d') if start_date else '',
        'end_date': end_date.strftime('%Y-%m-%d') if end_date else '',
        'is_filtered': is_filtered,
        'chart_title': chart_title,
        'chart_labels_json': json.dumps(labels_chart),
        'chart_sales_json': json.dumps(sales_chart),
        'best_selling_items': best_selling_items,
        'orders_by_type': orders_by_type,
        'recent_orders': recent_orders,
        'top_customers': top_customers,
    }
    return render(request, 'dashboard/dashboard.html', context)


@admin_required
def download_report(request):
    """
    Exports a sales & order report as a formatted CSV file.
    Supports ?start_date=YYYY-MM-DD and ?end_date=YYYY-MM-DD filtering.
    """
    today = timezone.localdate()
    start_date, end_date, _, _ = _parse_date_range(request)

    orders = Order.objects.select_related('account', 'table').prefetch_related('items__item').order_by('-order_date')

    if start_date:
        orders = orders.filter(order_date__date__gte=start_date)
    if end_date:
        orders = orders.filter(order_date__date__lte=end_date)

    filename_part = ""
    if start_date and end_date:
        filename_part = f"_{start_date}_to_{end_date}"
    elif start_date:
        filename_part = f"_from_{start_date}"
    elif end_date:
        filename_part = f"_until_{end_date}"
    else:
        filename_part = f"_{today}"

    filename = f"alkhair_sales_report{filename_part}.csv"

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Write UTF-8 BOM so Excel opens special characters correctly
    response.write('\ufeff')

    writer = csv.writer(response)

    # Executive Summary Header
    date_range_label = f"{start_date or 'Earliest'} to {end_date or today}"
    paid_total = orders.filter(
        payment_status='paid'
    ).exclude(order_status='cancelled').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    writer.writerow(['RESTORAN ALKHAIR - SALES & ORDER REPORT'])
    writer.writerow(['Generated At', timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow(['Date Range', date_range_label])
    writer.writerow(['Total Orders in Period', orders.count()])
    writer.writerow(['Total Paid Revenue (RM)', f"{paid_total:.2f}"])
    writer.writerow([])

    # Table Column Headers
    writer.writerow([
        'Order ID',
        'Order Date',
        'Order Time',
        'Customer Name',
        'Customer Email',
        'Customer Phone',
        'Order Type',
        'Table Number',
        'Delivery Address',
        'Items Ordered',
        'Total Amount (RM)',
        'Payment Method',
        'Payment Status',
        'Order Status',
    ])

    for o in orders:
        local_dt = timezone.localtime(o.order_date)
        items_summary = "; ".join([
            f"{oi.item.item_name} x{oi.quantity} (RM {oi.unit_price:.2f})"
            for oi in o.items.all()
        ])
        writer.writerow([
            o.order_id,
            local_dt.strftime('%Y-%m-%d'),
            local_dt.strftime('%H:%M:%S'),
            o.account.full_name if o.account else 'Guest',
            o.account.email if o.account else '',
            o.account.phone if o.account else '',
            o.get_order_type_display(),
            o.table.table_number if o.table else '-',
            o.delivery_address or '-',
            items_summary,
            f"{o.total_amount:.2f}",
            o.get_payment_method_display(),
            o.get_payment_status_display(),
            o.get_order_status_display(),
        ])

    return response
