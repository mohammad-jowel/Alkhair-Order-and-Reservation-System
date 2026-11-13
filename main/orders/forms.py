from django import forms
from django.core.exceptions import ValidationError
from .models import Order, RestaurantTable


class CheckoutForm(forms.Form):
    """
    Checkout form capturing order type, delivery address, and payment method.
    Dynamic order types based on active dine-in table context.
    """
    ORDER_TYPE_DEFAULT_CHOICES = [
        ('delivery', 'Delivery (to your address)'),
        ('takeaway', 'Takeaway (self-pickup)'),
    ]

    ORDER_TYPE_TABLE_CHOICES = [
        ('dine_in', 'Dine-in (Served to your table)'),
        ('delivery', 'Delivery (to your address)'),
        ('takeaway', 'Takeaway (self-pickup)'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash (Pay on Delivery / Pickup / Counter)'),
        ('sim_banking', 'Online Banking FPX (Simulated)'),
        ('sim_card', 'Credit / Debit Card (Simulated)'),
        ('sim_ewallet', 'E-Wallet Touch \'n Go / GrabPay (Simulated)'),
    ]

    order_type = forms.ChoiceField(
        choices=ORDER_TYPE_DEFAULT_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    delivery_address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter street address, building/unit number, and landmark in Parit Raja'
        })
    )
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )

    def __init__(self, *args, has_table=False, initial_address='', **kwargs):
        super().__init__(*args, **kwargs)
        if has_table:
            self.fields['order_type'].choices = self.ORDER_TYPE_TABLE_CHOICES
            self.fields['order_type'].initial = 'dine_in'
        else:
            self.fields['order_type'].choices = self.ORDER_TYPE_DEFAULT_CHOICES
            self.fields['order_type'].initial = 'delivery'

        if initial_address and not self.is_bound:
            self.fields['delivery_address'].initial = initial_address

    def clean(self):
        cleaned_data = super().clean()
        order_type = cleaned_data.get('order_type')
        delivery_address = cleaned_data.get('delivery_address', '').strip()

        if order_type == 'delivery':
            if not delivery_address:
                self.add_error('delivery_address', 'Delivery address is required for delivery orders.')
        else:
            cleaned_data['delivery_address'] = ''

        return cleaned_data


class OrderUpdateStatusForm(forms.ModelForm):
    """Admin form to update order and payment statuses."""
    class Meta:
        model = Order
        fields = ['order_status', 'payment_status']
        widgets = {
            'order_status': forms.Select(attrs={'class': 'form-select form-select-sm'}),
            'payment_status': forms.Select(attrs={'class': 'form-select form-select-sm'}),
        }


class RestaurantTableForm(forms.ModelForm):
    """Admin form to create or configure dining tables."""
    class Meta:
        model = RestaurantTable
        fields = ['table_number']
        widgets = {
            'table_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'e.g. 11',
                'required': 'required',
            }),
        }

    def clean_table_number(self):
        num = self.cleaned_data.get('table_number')
        if not num or num < 1:
            raise ValidationError("Table number must be at least 1.")
        qs = RestaurantTable.objects.filter(table_number=num)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError(f"Table #{num} already exists. Please choose a different number.")
        return num
