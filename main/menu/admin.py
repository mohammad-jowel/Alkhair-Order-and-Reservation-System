from django.contrib import admin
from .models import MenuCategory, MenuItem


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ('category_id', 'category_name')
    search_fields = ('category_name',)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('item_id', 'item_name', 'category', 'price', 'is_available')
    list_filter = ('category', 'is_available')
    search_fields = ('item_name', 'description')
    list_editable = ('price', 'is_available')
