from django import forms
from django.core.exceptions import ValidationError
from .models import MenuCategory, MenuItem


class CategoryForm(forms.ModelForm):
    """Form for adding and editing menu categories."""
    class Meta:
        model = MenuCategory
        fields = ['category_name']
        widgets = {
            'category_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Desserts & Beverages',
                'maxlength': 100
            })
        }


class MenuItemForm(forms.ModelForm):
    """Form for adding and editing menu items with image validation."""
    class Meta:
        model = MenuItem
        fields = ['category', 'item_name', 'description', 'price', 'image', 'is_available']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'item_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Chicken Shawarma (Large)', 'maxlength': 150}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Ingredients, flavor profile, and serving style'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.50', 'min': '0.50'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price <= 0:
            raise ValidationError('Price must be greater than zero.')
        return price

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image and hasattr(image, 'size'):
            # Maximum allowed size: 5MB
            max_size = 5 * 1024 * 1024
            if image.size > max_size:
                raise ValidationError('Image file size cannot exceed 5MB.')
        return image
