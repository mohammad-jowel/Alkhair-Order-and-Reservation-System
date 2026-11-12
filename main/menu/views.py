from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import ProtectedError
from accounts.decorators import admin_required
from .models import MenuCategory, MenuItem
from .forms import CategoryForm, MenuItemForm


def menu_list(request):
    """
    Public menu display page.
    Groups items by category and allows adding items to cart.
    Works seamlessly with or without an active table context in session.
    """
    categories = MenuCategory.objects.prefetch_related('items').all()
    selected_category_id = request.GET.get('category')

    if selected_category_id:
        try:
            selected_category_id = int(selected_category_id)
            filtered_categories = categories.filter(category_id=selected_category_id)
        except ValueError:
            filtered_categories = categories
    else:
        filtered_categories = categories

    context = {
        'all_categories': categories,
        'categories': filtered_categories,
        'selected_category_id': selected_category_id,
        'table_number': request.session.get('table_number'),
    }
    return render(request, 'menu/menu_list.html', context)


@admin_required
def manage_menu(request):
    """Admin management dashboard for menu categories and menu items."""
    categories = MenuCategory.objects.all()
    items = MenuItem.objects.select_related('category').all().order_by('category__category_name', 'item_name')

    context = {
        'categories': categories,
        'items': items,
    }
    return render(request, 'menu/manage_menu.html', context)


@admin_required
def add_category(request):
    """Add a new menu category."""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.category_name}" was created successfully.')
            return redirect('menu:manage_menu')
    else:
        form = CategoryForm()

    return render(request, 'menu/category_form.html', {'form': form, 'title': 'Add Menu Category'})


@admin_required
def edit_category(request, category_id):
    """Edit an existing menu category."""
    category = get_object_or_404(MenuCategory, category_id=category_id)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'Category "{category.category_name}" was updated.')
            return redirect('menu:manage_menu')
    else:
        form = CategoryForm(instance=category)

    return render(request, 'menu/category_form.html', {'form': form, 'title': f'Edit Category: {category.category_name}'})


@admin_required
def delete_category(request, category_id):
    """Delete a menu category if no items reference it."""
    category = get_object_or_404(MenuCategory, category_id=category_id)
    if request.method == 'POST':
        try:
            category_name = category.category_name
            category.delete()
            messages.success(request, f'Category "{category_name}" was deleted.')
        except ProtectedError:
            messages.error(request, f'Cannot delete category "{category.category_name}" because it contains menu items. Delete or reassign items first.')
    return redirect('menu:manage_menu')


@admin_required
def add_item(request):
    """Add a new menu item."""
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save()
            messages.success(request, f'Menu item "{item.item_name}" was created successfully.')
            return redirect('menu:manage_menu')
    else:
        form = MenuItemForm()

    return render(request, 'menu/item_form.html', {'form': form, 'title': 'Add Menu Item'})


@admin_required
def edit_item(request, item_id):
    """Edit an existing menu item."""
    item = get_object_or_404(MenuItem, item_id=item_id)
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f'Menu item "{item.item_name}" was updated.')
            return redirect('menu:manage_menu')
    else:
        form = MenuItemForm(instance=item)

    return render(request, 'menu/item_form.html', {'form': form, 'title': f'Edit Item: {item.item_name}', 'item': item})


@admin_required
def delete_item(request, item_id):
    """
    Delete a menu item.
    Enforces business rule: If the item has been ordered, deletion is blocked
    and a friendly message asks the admin to set it unavailable instead.
    """
    item = get_object_or_404(MenuItem, item_id=item_id)
    if request.method == 'POST':
        item_name = item.item_name
        try:
            item.delete()
            messages.success(request, f'Menu item "{item_name}" was deleted.')
        except ProtectedError:
            messages.error(
                request,
                f'Menu item "{item_name}" cannot be deleted because it has existing customer order records. '
                f'Please toggle its availability to "Unavailable" instead to remove it from the public menu.'
            )
    return redirect('menu:manage_menu')


@admin_required
def toggle_availability(request, item_id):
    """Quickly toggle the availability of a menu item."""
    if request.method == 'POST':
        item = get_object_or_404(MenuItem, item_id=item_id)
        item.is_available = not item.is_available
        item.save()
        status_text = 'available' if item.is_available else 'unavailable'
        messages.info(request, f'"{item.item_name}" is now marked as {status_text}.')
    return redirect('menu:manage_menu')
