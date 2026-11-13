import io
import base64
import secrets
from pathlib import Path
from decimal import Decimal
import qrcode
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Max
from django.http import Http404
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from accounts.decorators import admin_required
from menu.models import MenuItem
from .models import Order, OrderItem, RestaurantTable
from .forms import CheckoutForm, OrderUpdateStatusForm, RestaurantTableForm
from .cart import (
    get_cart,
    add_to_cart,
    update_cart_item,
    remove_from_cart,
    clear_cart,
    get_cart_details
)


def qr_table_entry(request, qr_token):
    """
    Validate table QR token from scan.
    Stores table_id and table_number in session, and redirects to Menu.
    Unknown or inactive tokens show a friendly error.
    """
    try:
        table = RestaurantTable.objects.get(qr_token=qr_token, is_active=True)
        request.session['table_id'] = table.table_id
        request.session['table_number'] = table.table_number
        request.session.modified = True
        messages.success(request, f'Welcome! You are seated at Table #{table.table_number}. Please choose your dishes.')
        return redirect('menu:menu_list')
    except RestaurantTable.DoesNotExist:
        messages.error(request, 'This table QR code is invalid, unassigned, or inactive. Please contact restaurant staff.')
        return redirect('menu:menu_list')


def cart_view(request):
    """
    Shopping cart view: supports adding, updating, removing items,
    and rendering the cart alongside the checkout form.
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        item_id = request.POST.get('item_id')

        if action == 'add' and item_id:
            try:
                quantity = int(request.POST.get('quantity', 1))
            except ValueError:
                quantity = 1
            success, msg = add_to_cart(request, int(item_id), quantity)
            if success:
                messages.success(request, msg)
            else:
                messages.error(request, msg)

            # Redirect back to where the item was added from (e.g. menu page)
            next_url = request.POST.get('next')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)

            referer = request.META.get('HTTP_REFERER')
            if referer and url_has_allowed_host_and_scheme(referer, allowed_hosts={request.get_host()}):
                return redirect(referer)

            return redirect('menu:menu_list')

        elif action == 'update' and item_id:
            try:
                quantity = int(request.POST.get('quantity', 1))
            except ValueError:
                quantity = 1
            update_cart_item(request, int(item_id), quantity)
            messages.info(request, 'Cart updated.')
            return redirect('orders:cart_view')

        elif action == 'remove' and item_id:
            remove_from_cart(request, int(item_id))
            messages.info(request, 'Item removed from cart.')
            return redirect('orders:cart_view')

        elif action == 'clear':
            clear_cart(request)
            messages.info(request, 'Your cart has been cleared.')
            return redirect('orders:cart_view')

    cart_items, total_amount = get_cart_details(request)
    has_table = bool(request.session.get('table_id'))
    initial_address = request.user.address if request.user.is_authenticated else ''

    checkout_form = CheckoutForm(has_table=has_table, initial_address=initial_address)

    context = {
        'cart_items': cart_items,
        'total_amount': total_amount,
        'checkout_form': checkout_form,
        'table_number': request.session.get('table_number'),
    }
    return render(request, 'orders/cart.html', context)


@login_required
def checkout(request):
    """
    Process order checkout.
    Calculates total on server from current database prices inside transaction.atomic().
    """
    if request.method != 'POST':
        return redirect('orders:cart_view')

    cart_items, total_amount = get_cart_details(request)
    if not cart_items:
        messages.error(request, 'Your cart is empty. Please add items before checking out.')
        return redirect('menu:menu_list')

    has_table = bool(request.session.get('table_id'))
    form = CheckoutForm(request.POST, has_table=has_table)

    if form.is_valid():
        order_type = form.cleaned_data['order_type']
        delivery_address = form.cleaned_data['delivery_address']
        payment_method = form.cleaned_data['payment_method']

        table = None
        if order_type == 'dine_in':
            table_id = request.session.get('table_id')
            if not table_id:
                messages.error(request, 'Dine-in requires an active table scan. Please scan your table QR code.')
                return redirect('menu:menu_list')
            try:
                table = RestaurantTable.objects.get(table_id=table_id, is_active=True)
            except RestaurantTable.DoesNotExist:
                messages.error(request, 'Assigned table is invalid or inactive.')
                return redirect('menu:menu_list')

        # Atomic transaction: verify prices from database, calculate true server-side total
        with transaction.atomic():
            # Refresh items directly from DB
            item_ids = [ci['item'].item_id for ci in cart_items]
            db_items = {item.item_id: item for item in MenuItem.objects.filter(item_id__in=item_ids, is_available=True)}

            server_total = Decimal('0.00')
            order_items_data = []

            for ci in cart_items:
                item_id = ci['item'].item_id
                if item_id not in db_items:
                    messages.error(request, f'Item "{ci["item"].item_name}" is no longer available.')
                    return redirect('orders:cart_view')
                
                db_item = db_items[item_id]
                qty = ci['quantity']
                unit_price = db_item.price
                line_total = unit_price * qty
                server_total += line_total
                order_items_data.append((db_item, qty, unit_price))

            # Create Order record
            order = Order.objects.create(
                account=request.user,
                table=table,
                order_type=order_type,
                delivery_address=delivery_address if order_type == 'delivery' else None,
                order_status='pending',
                payment_method=payment_method,
                payment_status='pending',
                total_amount=server_total
            )

            # Create OrderItem records copying current unit_price
            for item, qty, unit_price in order_items_data:
                OrderItem.objects.create(
                    order=order,
                    item=item,
                    quantity=qty,
                    unit_price=unit_price
                )

        # Clear cart upon order creation
        clear_cart(request)

        # Handle Payment Method
        if payment_method == 'cash':
            messages.success(
                request,
                f'Order #{order.order_id} placed successfully! Please pay RM {order.total_amount:.2f} in cash upon receiving your order.'
            )
            return redirect('orders:order_detail', order_id=order.order_id)
        else:
            # Simulated payment step
            return redirect('orders:payment_simulation', order_id=order.order_id)
    else:
        # Form error
        for error in form.errors.values():
            messages.error(request, error.as_text())
        return redirect('orders:cart_view')


@login_required
def payment_simulation(request, order_id):
    """
    Demonstration payment simulation step for online banking, card, and e-wallet.
    Strictly simulated; no real payment credentials accepted or processed.
    """
    order = get_object_or_404(Order, order_id=order_id)
    if not request.user.is_admin and order.account != request.user:
        raise Http404("Order not found.")

    if request.method == 'POST':
        action = request.POST.get('simulation_result')
        if action == 'success':
            order.payment_status = 'paid'
            order.save()
            messages.success(request, f'Simulated payment of RM {order.total_amount:.2f} was successful! Your order is being prepared.')
            return redirect('orders:order_detail', order_id=order.order_id)
        elif action == 'fail':
            order.payment_status = 'failed'
            order.save()
            messages.error(request, 'Simulated payment failed. You can retry or switch to cash.')
        elif action == 'switch_to_cash':
            order.payment_method = 'cash'
            order.payment_status = 'pending'
            order.save()
            messages.info(request, 'Payment method switched to Cash. Please pay upon delivery or collection.')
            return redirect('orders:order_detail', order_id=order.order_id)

    return render(request, 'orders/payment_simulation.html', {'order': order})


@login_required
def my_orders(request):
    """List all orders belonging to the logged-in customer."""
    orders = Order.objects.filter(account=request.user).select_related('table').prefetch_related('items__item')
    return render(request, 'orders/my_orders.html', {'orders': orders})


@login_required
def order_detail(request, order_id):
    """
    View detailed information for a specific order.
    Enforces ownership: customer can only view their own order; other records return 404.
    """
    order = get_object_or_404(Order.objects.select_related('account', 'table'), order_id=order_id)
    if not request.user.is_admin and order.account != request.user:
        raise Http404("Order not found.")

    order_items = order.items.select_related('item').all()
    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'orders/order_detail.html', context)


@login_required
def cancel_order(request, order_id):
    """
    Cancel an order while still 'pending'.
    Rule: A customer may cancel only their own order while it is still pending.
    A cancelled order that was never paid gets payment_status = 'not_required'.
    """
    if request.method != 'POST':
        return redirect('orders:my_orders')

    order = get_object_or_404(Order, order_id=order_id)
    if not request.user.is_admin and order.account != request.user:
        raise Http404("Order not found.")

    if order.order_status == 'pending':
        order.order_status = 'cancelled'
        if order.payment_status != 'paid':
            order.payment_status = 'not_required'
        order.save()
        messages.success(request, f'Order #{order.order_id} has been cancelled.')
    else:
        messages.error(request, f'Order #{order.order_id} cannot be cancelled because it is already {order.get_order_status_display().lower()}.')

    if request.user.is_admin:
        return redirect('orders:manage_orders')
    return redirect('orders:order_detail', order_id=order.order_id)


@admin_required
def manage_orders(request):
    """
    Admin management view for orders with status and type filters.
    Allows advancing order status and marking cash orders as paid.
    """
    orders = Order.objects.select_related('account', 'table').prefetch_related('items__item').all()

    # Filter by order status
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(order_status=status_filter)

    # Filter by order type
    type_filter = request.GET.get('type')
    if type_filter:
        orders = orders.filter(order_type=type_filter)

    # Status update handler
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        order = get_object_or_404(Order, order_id=order_id)
        new_status = request.POST.get('order_status')
        new_payment = request.POST.get('payment_status')

        if new_status and new_status in dict(Order.ORDER_STATUS_CHOICES):
            order.order_status = new_status
            if new_status == 'cancelled' and order.payment_status != 'paid':
                order.payment_status = 'not_required'

        if new_payment and new_payment in dict(Order.PAYMENT_STATUS_CHOICES):
            order.payment_status = new_payment

        order.save()
        messages.success(request, f'Order #{order.order_id} updated: {order.get_order_status_display()}, Payment: {order.get_payment_status_display()}.')
        return redirect('orders:manage_orders')

    context = {
        'orders': orders,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'status_choices': Order.ORDER_STATUS_CHOICES,
        'type_choices': Order.ORDER_TYPE_CHOICES,
        'payment_choices': Order.PAYMENT_STATUS_CHOICES,
    }
    return render(request, 'orders/manage_orders.html', context)


def clear_table(request):
    """Clear active dine-in table context from session."""
    if 'table_id' in request.session:
        del request.session['table_id']
    if 'table_number' in request.session:
        del request.session['table_number']
    request.session.modified = True
    messages.info(request, 'Dine-in table cleared.')
    return redirect('menu:menu_list')


def _generate_qr_base64(url):
    """Generate in-memory base64 encoded PNG data URI for a QR code."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('ascii')


@admin_required
def manage_tables(request):
    """
    Admin management view to display all dining tables, their QR codes,
    and generate/remove table QR codes for dine-in ordering.
    """
    tables = list(RestaurantTable.objects.all().order_by('table_number'))
    max_table = RestaurantTable.objects.aggregate(Max('table_number'))['table_number__max']
    next_table_number = (max_table + 1) if max_table else 1

    # Attach QR code base64 and target URL to each table instance
    for table in tables:
        target_url = request.build_absolute_uri(reverse('orders:qr_table_entry', args=[table.qr_token]))
        table.target_url = target_url
        table.qr_base64 = _generate_qr_base64(target_url)

    total_tables = len(tables)
    active_tables = sum(1 for t in tables if t.is_active)
    inactive_tables = total_tables - active_tables

    form = RestaurantTableForm(initial={'table_number': next_table_number})

    context = {
        'tables': tables,
        'total_tables': total_tables,
        'active_tables': active_tables,
        'inactive_tables': inactive_tables,
        'next_table_number': next_table_number,
        'form': form,
    }
    return render(request, 'orders/manage_tables.html', context)


@admin_required
def create_table(request):
    """Create a new restaurant dining table with an automatically generated QR token."""
    if request.method == 'POST':
        form = RestaurantTableForm(request.POST)
        if form.is_valid():
            table = form.save(commit=False)
            table.qr_token = secrets.token_urlsafe(16)
            table.is_active = True
            table.save()

            # Optionally save QR PNG to media/qr directory
            try:
                qr_dir = Path(settings.MEDIA_ROOT) / 'qr'
                qr_dir.mkdir(parents=True, exist_ok=True)
                target_url = request.build_absolute_uri(reverse('orders:qr_table_entry', args=[table.qr_token]))
                img = qrcode.make(target_url)
                img.save(str(qr_dir / f"table_{table.table_number}.png"))
            except Exception:
                pass

            messages.success(request, f'Table #{table.table_number} and QR code created successfully!')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    return redirect('orders:manage_tables')


@admin_required
def toggle_table_active(request, table_id):
    """Toggle dining table active status."""
    if request.method == 'POST':
        table = get_object_or_404(RestaurantTable, table_id=table_id)
        table.is_active = not table.is_active
        table.save()
        status = 'Active' if table.is_active else 'Inactive'
        messages.success(request, f'Table #{table.table_number} is now marked as {status}.')
    return redirect('orders:manage_tables')


@admin_required
def delete_table(request, table_id):
    """Delete a dining table and its QR code."""
    if request.method == 'POST':
        table = get_object_or_404(RestaurantTable, table_id=table_id)
        num = table.table_number
        table.delete()

        # Clean up file if present
        try:
            file_path = Path(settings.MEDIA_ROOT) / 'qr' / f"table_{num}.png"
            if file_path.exists():
                file_path.unlink()
        except Exception:
            pass

        messages.success(request, f'Table #{num} and its QR code have been removed.')
    return redirect('orders:manage_tables')


@admin_required
def regenerate_table_qr(request, table_id):
    """Regenerate a table's QR token (e.g. if code was compromised)."""
    if request.method == 'POST':
        table = get_object_or_404(RestaurantTable, table_id=table_id)
        table.qr_token = secrets.token_urlsafe(16)
        table.save()

        # Update media file if present
        try:
            qr_dir = Path(settings.MEDIA_ROOT) / 'qr'
            qr_dir.mkdir(parents=True, exist_ok=True)
            target_url = request.build_absolute_uri(reverse('orders:qr_table_entry', args=[table.qr_token]))
            img = qrcode.make(target_url)
            img.save(str(qr_dir / f"table_{table.table_number}.png"))
        except Exception:
            pass

        messages.success(request, f'New QR token generated for Table #{table.table_number}.')
    return redirect('orders:manage_tables')
