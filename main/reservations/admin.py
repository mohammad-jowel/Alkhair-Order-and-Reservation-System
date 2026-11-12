from django.contrib import admin
from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        'reservation_id',
        'account',
        'reservation_date',
        'reservation_time',
        'party_size',
        'status',
        'created_at'
    )
    list_filter = ('status', 'reservation_date')
    search_fields = ('reservation_id', 'account__email', 'account__full_name')
