from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.http import url_has_allowed_host_and_scheme
from django.urls import reverse
from .forms import RegisterForm, LoginForm, ProfileEditForm, ChangePasswordForm


def register_view(request):
    """Register a new customer account."""
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to Restoran Alkhair, {user.full_name}! Your account has been created.')
            
            # Check for next URL
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect('core:home')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """Authenticate and log in an existing user with email and password."""
    if request.user.is_authenticated:
        if request.user.is_admin:
            return redirect('dashboard:dashboard')
        return redirect('core:home')

    next_url = request.GET.get('next', '')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        next_url = request.POST.get('next', '')

        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)

            if user is not None and user.is_active:
                login(request, user)
                messages.success(request, f'Welcome back, {user.full_name}!')

                # Validate next URL to prevent open redirect vulnerabilities
                if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                    return redirect(next_url)

                if user.is_admin:
                    return redirect('dashboard:dashboard')
                return redirect('core:home')
            else:
                # Generic error message to prevent account enumeration
                messages.error(request, 'Invalid email or password. Please check your credentials.')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form, 'next': next_url})


def logout_view(request):
    """Log out the currently authenticated user."""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('core:home')


@login_required
def profile_view(request):
    """View and update profile information and change password."""
    profile_form = ProfileEditForm(instance=request.user)
    password_form = ChangePasswordForm(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_profile':
            profile_form = ProfileEditForm(request.POST, instance=request.user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Your profile details have been updated.')
                return redirect('accounts:profile')

        elif action == 'change_password':
            password_form = ChangePasswordForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                new_password = password_form.cleaned_data['new_password']
                request.user.set_password(new_password)
                request.user.save()
                # Maintain active session after password change
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Your password was changed successfully.')
                return redirect('accounts:profile')

    context = {
        'profile_form': profile_form,
        'password_form': password_form,
    }
    return render(request, 'accounts/profile.html', context)
