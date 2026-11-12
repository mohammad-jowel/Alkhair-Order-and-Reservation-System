from django.db import models
from django.conf import settings
from menu.models import MenuItem


class RestaurantTable(models.Model):
    """
    Physical dining table model matching table 'restaurant_table'.
    Primary key: table_id.
    """
    table_id = models.AutoField(primary_key=True)
    table_number = models.IntegerField(unique=True)
    qr_token = models.CharField(max_length=64, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'restaurant_table'
        verbose_name = 'Restaurant Table'
        verbose_name_plural = 'Restaurant Tables'
        ordering = ['table_number']

    def __str__(self):
        return f"Table {self.table_number}"


class Order(models.Model):
    """
    Customer order model matching table 'orders'.
    Primary key: order_id.
    """
    ORDER_TYPE_CHOICES = [
        ('delivery', 'Delivery'),
        ('takeaway', 'Takeaway'),
        ('dine_in', 'Dine-in'),
    ]

    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('sim_banking', 'Online Banking (Simulated)'),
        ('sim_card', 'Credit/Debit Card (Simulated)'),
        ('sim_ewallet', 'E-Wallet (Simulated)'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('not_required', 'Not Required'),
    ]

    order_id = models.AutoField(primary_key=True)
    account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        db_column='account_id',
        related_name='orders'
    )
    table = models.ForeignKey(
        RestaurantTable,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='table_id',
        related_name='orders'
    )
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES)
    delivery_address = models.TextField(null=True, blank=True)
    order_status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default='pending'
    )
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    order_date = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'orders'
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-order_date']
        indexes = [
            models.Index(fields=['account']),
            models.Index(fields=['table']),
            models.Index(fields=['order_date']),
        ]

    def __str__(self):
        return f"Order #{self.order_id} - {self.get_order_type_display()} (RM {self.total_amount:.2f})"


class OrderItem(models.Model):
    """
    Join table between 'orders' and 'menu_item' matching table 'order_item'.
    Enforces one row per dish per order using UniqueConstraint.
    """
    order_item_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        db_column='order_id',
        related_name='items'
    )
    item = models.ForeignKey(
        MenuItem,
        on_delete=models.PROTECT,
        db_column='item_id',
        related_name='order_items'
    )
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'order_item'
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
        constraints = [
            models.UniqueConstraint(
                fields=['order', 'item'],
                name='unique_order_item'
            )
        ]
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['item']),
        ]

    def __str__(self):
        return f"{self.quantity}x {self.item.item_name} @ RM {self.unit_price:.2f}"

    @property
    def subtotal(self):
        """Calculate line item subtotal."""
        return self.quantity * self.unit_price
