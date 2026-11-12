from decimal import Decimal
from menu.models import MenuItem


def get_cart(request):
    """Retrieve the cart dictionary from session."""
    return request.session.get('cart', {})


def save_cart(request, cart):
    """Save the cart dictionary to session and update total item count."""
    request.session['cart'] = cart
    request.session['cart_count'] = sum(cart.values())
    request.session.modified = True


def add_to_cart(request, item_id, quantity=1):
    """Add a menu item to the session cart."""
    try:
        item = MenuItem.objects.get(item_id=item_id, is_available=True)
    except MenuItem.DoesNotExist:
        return False, "This menu item is currently unavailable."

    cart = get_cart(request)
    item_key = str(item_id)
    current_qty = cart.get(item_key, 0)
    cart[item_key] = current_qty + max(1, quantity)
    save_cart(request, cart)
    return True, f"Added {item.item_name} to your cart."


def update_cart_item(request, item_id, quantity):
    """Update quantity for a cart item or remove if quantity <= 0."""
    cart = get_cart(request)
    item_key = str(item_id)
    if quantity <= 0:
        if item_key in cart:
            del cart[item_key]
    else:
        cart[item_key] = quantity
    save_cart(request, cart)


def remove_from_cart(request, item_id):
    """Remove an item completely from the session cart."""
    cart = get_cart(request)
    item_key = str(item_id)
    if item_key in cart:
        del cart[item_key]
        save_cart(request, cart)


def clear_cart(request):
    """Empty the session cart."""
    request.session['cart'] = {}
    request.session['cart_count'] = 0
    request.session.modified = True


def get_cart_details(request):
    """
    Fetch all items in the cart from the database to compute accurate server-side prices and totals.
    Stale or unavailable items are cleaned up.
    """
    cart = get_cart(request)
    if not cart:
        return [], Decimal('0.00')

    item_ids = [int(k) for k in cart.keys() if k.isdigit()]
    items = MenuItem.objects.filter(item_id__in=item_ids, is_available=True).select_related('category')
    
    cart_items = []
    total_amount = Decimal('0.00')
    active_ids = set()

    for item in items:
        item_key = str(item.item_id)
        qty = cart.get(item_key, 1)
        subtotal = item.price * qty
        total_amount += subtotal
        active_ids.add(item_key)
        cart_items.append({
            'item': item,
            'quantity': qty,
            'unit_price': item.price,
            'subtotal': subtotal,
        })

    # Clean up any removed/unavailable items from session
    if len(active_ids) != len(cart):
        clean_cart = {k: v for k, v in cart.items() if k in active_ids}
        save_cart(request, clean_cart)

    return cart_items, total_amount
