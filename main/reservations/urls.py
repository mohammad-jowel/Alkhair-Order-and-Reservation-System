from django.urls import path
from . import views

app_name = 'reservations'

urlpatterns = [
    path('', views.reservation_list, name='reservation_list'),
    path('manage/', views.manage_reservations, name='manage_reservations'),
]
