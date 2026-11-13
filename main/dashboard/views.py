import json
from decimal import Decimal
from datetime import timedelta
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum, Count, F
from accounts.decorators import admin_required
from accounts.models import Account
from orders.models import Order, OrderItem
from reservations.models import Reservation


@admin_required
def dashboard(request):
    """
    Admin dashboard calculating metrics via Django ORM aggregation.
    Displays summary cards, 7-day sales Chart.js chart, best-selling items,
    orders by type, recent orders, and pending reservations.
    """
    today = timezone.localdate()

    # 1. Summary Cards
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

    # 2. Sales per day for the last 7 days (Chart.js line chart)
    labels_7_days = []
    sales_7_days = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_sales = Order.objects.filter(
            order_date__date=day,
            payment_status='paid'
        ).exclude(order_status='cancelled').aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        labels_7_days.append(day.strftime('%d %b'))
        sales_7_days.append(float(day_sales))

    # 3. Best-Selling Menu Items (Top 5 by quantity sold)
    # Join 1: order_item -> menu_item -> menu_category
    # Description: Aggregates total units sold and revenue per dish by joining order_item to menu_item and menu_category
    best_selling_items = OrderItem.objects.filter(
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

    # 4. Orders by Type (delivery, takeaway, dine_in)
    type_counts_raw = Order.objects.values('order_type').annotate(count=Count('order_id'))
    type_counts = {item['order_type']: item['count'] for item in type_counts_raw}
    orders_by_type = [
        {'label': 'Dine-in', 'count': type_counts.get('dine_in', 0), 'badge': 'bg-warning text-dark'},
        {'label': 'Delivery', 'count': type_counts.get('delivery', 0), 'badge': 'bg-info text-dark'},
        {'label': 'Takeaway', 'count': type_counts.get('takeaway', 0), 'badge': 'bg-secondary'},
    ]

    # 5. Recent Orders (Last 10)
    # Join 2 (Three-table join): orders -> account (customer) -> restaurant_table
    # Description: Joins orders table with account and restaurant_table to retrieve customer details and table assignments
    recent_orders = Order.objects.select_related('account', 'table').prefetch_related('items__item').order_by('-order_date')[:10]

    # 6. Top Customers by Spending
    # Join 3 (Three-table join): account -> orders -> order_item
    # Description: Joins account table with orders to calculate each customer's lifetime value from paid orders
    top_customers = Account.objects.filter(
        role='customer',
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
        'total_orders_count': total_orders_count,
        'pending_orders_count': pending_orders_count,
        'total_customers_count': total_customers_count,
        'pending_reservations_count': pending_reservations_count,
        'chart_labels_json': json.dumps(labels_7_days),
        'chart_sales_json': json.dumps(sales_7_days),
        'best_selling_items': best_selling_items,
        'orders_by_type': orders_by_type,
        'recent_orders': recent_orders,
        'top_customers': top_customers,
    }
    return render(request, 'dashboard/dashboard.html', context)
