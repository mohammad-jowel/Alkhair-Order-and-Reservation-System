from django import forms
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from .models import Account


class RegisterForm(forms.ModelForm):
    """Registration form for new customers with password confirmation."""
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create password', 'autocomplete': 'new-password'}),
        help_text='At least 8 characters, containing letters and numbers.'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password', 'autocomplete': 'new-password'}),
        label='Confirm Password'
    )

    class Meta:
        model = Account
        fields = ['full_name', 'email', 'phone', 'address']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Ahmad bin Ali'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. +60123456789'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Full residential or delivery address'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower().strip()
        if Account.objects.filter(email=email).exists():
            raise ValidationError('This email address is already registered.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password:
            if password != confirm_password:
                self.add_error('confirm_password', 'Passwords do not match.')
            else:
                # Validate against Django password validators
                try:
                    password_validation.validate_password(password)
                except ValidationError as error:
                    self.add_error('password', error)
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'customer'
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    """Email and password login form."""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com', 'autocomplete': 'email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password', 'autocomplete': 'current-password'})
    )


class ProfileEditForm(forms.ModelForm):
    """Form for users to edit their profile details."""
    class Meta:
        model = Account
        fields = ['full_name', 'phone', 'address']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ChangePasswordForm(forms.Form):
    """Form to change account password."""
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Current password'}),
        label='Current Password'
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New password'}),
        label='New Password'
    )
    confirm_new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'}),
        label='Confirm New Password'
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise ValidationError('Current password is incorrect.')
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_new_password = cleaned_data.get('confirm_new_password')

        if new_password and confirm_new_password:
            if new_password != confirm_new_password:
                self.add_error('confirm_new_password', 'New passwords do not match.')
            else:
                try:
                    password_validation.validate_password(new_password, self.user)
                except ValidationError as error:
                    self.add_error('new_password', error)
        return cleaned_data
