from functools import wraps
from django.shortcuts import render, redirect
from django.urls import reverse


def admin_required(view_func):
    """
    Decorator to ensure user is logged in and has role == 'admin'.
    If not authenticated, redirects to login.
    If authenticated but not admin, renders custom 403 Forbidden page.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            login_url = f"{reverse('accounts:login')}?next={request.path}"
            return redirect(login_url)
        if not getattr(request.user, 'is_admin', False) and getattr(request.user, 'role', '') != 'admin':
            return render(request, '403.html', status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def customer_required(view_func):
    """
    Decorator to ensure user is logged in.
    If not authenticated, redirects to login with next parameter.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            login_url = f"{reverse('accounts:login')}?next={request.path}"
            return redirect(login_url)
        return view_func(request, *args, **kwargs)
    return _wrapped_view
