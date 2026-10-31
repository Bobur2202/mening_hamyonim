from django import template
from wallet.utils import format_uzs

register = template.Library()


@register.filter(name='uzs')
def uzs_filter(value):
    """Summani '1 000 000 so'm' formatida chiqaradi."""
    return format_uzs(value)


@register.filter(name='uzs_number')
def uzs_number_filter(value):
    """Faqat son qismini ajratilgan holda chiqaradi (masalan: 1 500 000)."""
    if value is None:
        return "0"
    try:
        val = float(value)
        if val == int(val):
            return f"{int(val):,}".replace(",", " ")
        return f"{val:,.2f}".replace(",", " ").replace(".", ",")
    except Exception:
        return str(value)


@register.filter(name='abs')
def abs_filter(value):
    """Sonning mutlaq qiymatini qaytaradi."""
    if value is None:
        return 0
    try:
        return abs(value)
    except Exception:
        return value
