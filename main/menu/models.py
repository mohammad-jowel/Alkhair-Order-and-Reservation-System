from django.db import models


class MenuCategory(models.Model):
    """
    Menu category model matching table 'menu_category'.
    Primary key: category_id.
    """
    category_id = models.AutoField(primary_key=True)
    category_name = models.CharField(max_length=100)

    class Meta:
        db_table = 'menu_category'
        verbose_name = 'Menu Category'
        verbose_name_plural = 'Menu Categories'

    def __str__(self):
        return self.category_name


class MenuItem(models.Model):
    """
    Menu item model matching table 'menu_item'.
    Primary key: item_id.
    """
    item_id = models.AutoField(primary_key=True)
    category = models.ForeignKey(
        MenuCategory,
        on_delete=models.PROTECT,
        db_column='category_id',
        related_name='items'
    )
    item_name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True)
    is_available = models.BooleanField(default=True)

    class Meta:
        db_table = 'menu_item'
        verbose_name = 'Menu Item'
        verbose_name_plural = 'Menu Items'
        indexes = [
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.item_name} (RM {self.price:.2f})"
