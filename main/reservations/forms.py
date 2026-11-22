from datetime import datetime, time
from django import forms
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Reservation


class ReservationBookingForm(forms.ModelForm):
    """Customer booking form with party size (1-20), date, and opening hours validation."""
    class Meta:
        model = Reservation
        fields = ['reservation_date', 'reservation_time', 'party_size', 'note']
        widgets = {
            'reservation_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'reservation_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
                'step': '900' # 15-minute intervals
            }),
            'party_size': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '20',
                'placeholder': 'Number of guests (1 - 20)'
            }),
            'note': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Special requests, seating preferences, dietary notes (optional)'
            }),
        }

    def clean_party_size(self):
        party_size = self.cleaned_data.get('party_size')
        if party_size is None or party_size < 1 or party_size > 20:
            raise ValidationError('Party size must be between 1 and 20 guests.')
        return party_size

    def clean(self):
        cleaned_data = super().clean()
        res_date = cleaned_data.get('reservation_date')
        res_time = cleaned_data.get('reservation_time')

        if res_date:
            today = timezone.localdate()
            if res_date < today:
                self.add_error('reservation_date', 'Reservation date cannot be in the past.')

        if res_date and res_time:
            # Check operating hours
            opening_str = getattr(settings, 'OPENING_TIME', '11:00')
            closing_str = getattr(settings, 'CLOSING_TIME', '23:00')

            try:
                open_hour, open_min = [int(x) for x in opening_str.split(':')]
                close_hour, close_min = [int(x) for x in closing_str.split(':')]
                open_t = time(open_hour, open_min)
                close_t = time(close_hour, close_min)
            except Exception:
                open_t = time(11, 0)
                close_t = time(23, 0)

            if res_time < open_t or res_time > close_t:
                self.add_error(
                    'reservation_time',
                    f'Reservation time must be within restaurant operating hours ({opening_str} – {closing_str}).'
                )

            # If booking for today, time cannot be in the past
            if res_date == timezone.localdate():
                current_time = timezone.localtime().time()
                if res_time <= current_time:
                    self.add_error('reservation_time', 'Reservation time for today cannot be in the past.')

        return cleaned_data
