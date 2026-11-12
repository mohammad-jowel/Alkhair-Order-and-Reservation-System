"""
URL configuration for main project.
Alkhair Order and Reservation System
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from orders import views as order_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('t/<str:qr_token>/', order_views.qr_table_entry, name='qr_table_entry'),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('menu/', include('menu.urls')),
    path('orders/', include('orders.urls')),
    path('reservations/', include('reservations.urls')),
    path('dashboard/', include('dashboard.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'core.views.custom_404'
handler403 = 'core.views.custom_403'
