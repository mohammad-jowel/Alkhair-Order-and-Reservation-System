from django import template
from django.conf import settings


register = template.Library()


def _format_time(value):
    """Return a configured 24-hour HH:MM value in customer-facing 12-hour form."""
    try:
        hour, minute = (int(part) for part in value.split(':', maxsplit=1))
        if not 0 <= hour <= 23 or not 0 <= minute <= 59:
            raise ValueError
    except (AttributeError, TypeError, ValueError):
        return value

    period = 'AM' if hour < 12 else 'PM'
    return f'{hour % 12 or 12}:{minute:02d} {period}'


@register.simple_tag
def restaurant_hours():
    """Render the same configured hours used by reservation validation."""
    opening_time = getattr(settings, 'OPENING_TIME', '11:00')
    closing_time = getattr(settings, 'CLOSING_TIME', '23:00')
    return f'{_format_time(opening_time)} – {_format_time(closing_time)}'
