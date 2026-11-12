from django.contrib import admin
from .models import RestaurantTable, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('item', 'quantity', 'unit_price', 'subtotal')
    readonly_fields = ('subtotal',)


@admin.register(RestaurantTable)
class RestaurantTableAdmin(admin.ModelAdmin):
    list_display = ('table_id', 'table_number', 'qr_token', 'is_active')
    list_editable = ('is_active',)
    search_fields = ('table_number', 'qr_token')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_id',
        'account',
        'order_type',
        'table',
        'order_status',
        'payment_method',
        'payment_status',
        'total_amount',
        'order_date'
    )
    list_filter = ('order_type', 'order_status', 'payment_method', 'payment_status')
    search_fields = ('order_id', 'account__email', 'account__full_name')
    readonly_fields = ('order_date',)
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order_item_id', 'order', 'item', 'quantity', 'unit_price')
    list_filter = ('order__order_status',)
