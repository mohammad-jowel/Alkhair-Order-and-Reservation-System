from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('cart/', views.cart_view, name='cart_view'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('manage/', views.manage_orders, name='manage_orders'),
    path('clear-table/', views.clear_table, name='clear_table'),
]
