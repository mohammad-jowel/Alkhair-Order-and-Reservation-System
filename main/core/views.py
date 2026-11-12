from django.shortcuts import render
from django.conf import settings
from menu.models import MenuItem


def home(request):
    """Public home page with intro, multimedia element, opening hours and featured dishes."""
    # Fetch a few available items to feature on home page
    featured_items = MenuItem.objects.filter(is_available=True)[:3]
    context = {
        'featured_items': featured_items,
        'opening_time': getattr(settings, 'OPENING_TIME', '11:00'),
        'closing_time': getattr(settings, 'CLOSING_TIME', '23:30'),
    }
    return render(request, 'core/home.html', context)


def about(request):
    """About & Contact page with location, hours, and contact details."""
    context = {
        'opening_time': getattr(settings, 'OPENING_TIME', '11:00'),
        'closing_time': getattr(settings, 'CLOSING_TIME', '23:30'),
    }
    return render(request, 'core/about.html', context)


def custom_404(request, exception=None):
    """Friendly custom 404 Page Not Found error view."""
    return render(request, '404.html', status=404)


def custom_403(request, exception=None):
    """Friendly custom 403 Permission Denied error view."""
    return render(request, '403.html', status=403)
