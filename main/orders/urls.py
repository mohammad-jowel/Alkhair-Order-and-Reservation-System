from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('cart/', views.cart_view, name='cart_view'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment-simulation/<int:order_id>/', views.payment_simulation, name='payment_simulation'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('order/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('manage/', views.manage_orders, name='manage_orders'),
    path('clear-table/', views.clear_table, name='clear_table'),
    path('t/<str:qr_token>/', views.qr_table_entry, name='qr_table_entry'),
]
