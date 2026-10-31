from .models import Category


DEFAULT_CATEGORIES = [
    # Daromadlar
    {"name": "Oylik maosh", "type": Category.TYPE_INCOME, "color": "#10b981", "icon": "bi-cash-stack"},
    {"name": "Bonus va mukofotlar", "type": Category.TYPE_INCOME, "color": "#06b6d4", "icon": "bi-gift"},
    {"name": "Frilans / Qo'shimcha ish", "type": Category.TYPE_INCOME, "color": "#3b82f6", "icon": "bi-laptop"},
    {"name": "Investitsiya va keshbek", "type": Category.TYPE_INCOME, "color": "#8b5cf6", "icon": "bi-graph-up-arrow"},
    {"name": "Boshqa tushumlar", "type": Category.TYPE_INCOME, "color": "#14b8a6", "icon": "bi-wallet2"},
    
    # Xarajatlar
    {"name": "Oziq-ovqat va bozor", "type": Category.TYPE_EXPENSE, "color": "#ef4444", "icon": "bi-cart4"},
    {"name": "Transport va yoqilg'i", "type": Category.TYPE_EXPENSE, "color": "#f97316", "icon": "bi-car-front"},
    {"name": "Kommunal va internet", "type": Category.TYPE_EXPENSE, "color": "#eab308", "icon": "bi-house-gear"},
    {"name": "Uy-joy / Ijara", "type": Category.TYPE_EXPENSE, "color": "#84cc16", "icon": "bi-house"},
    {"name": "Kafe va restoranlar", "type": Category.TYPE_EXPENSE, "color": "#f43f5e", "icon": "bi-cup-hot"},
    {"name": "Sog'liq va dorixona", "type": Category.TYPE_EXPENSE, "color": "#ec4899", "icon": "bi-heart-pulse"},
    {"name": "Kiyim-kechak", "type": Category.TYPE_EXPENSE, "color": "#a855f7", "icon": "bi-bag"},
    {"name": "Ta'lim va kitoblar", "type": Category.TYPE_EXPENSE, "color": "#6366f1", "icon": "bi-book"},
    {"name": "Boshqa xarajatlar", "type": Category.TYPE_EXPENSE, "color": "#64748b", "icon": "bi-credit-card"},
]


def create_default_categories(user):
    """Foydalanuvchi uchun standart kategoriyalarni yaratish."""
    created_list = []
    for item in DEFAULT_CATEGORIES:
        cat, created = Category.objects.get_or_create(
            user=user,
            name=item["name"],
            type=item["type"],
            defaults={"color": item["color"], "icon": item["icon"]}
        )
        if created:
            created_list.append(cat)
    return created_list


def format_uzs(amount):
    """
    Summani O'zbekiston so'mida formatlash.
    Masalan: 1250000.50 -> "1 250 000,50 so'm"
             1250000.00 -> "1 250 000 so'm"
    """
    if amount is None:
        amount = 0
    try:
        val = float(amount)
        if val == int(val):
            formatted = f"{int(val):,}".replace(",", " ")
        else:
            formatted = f"{val:,.2f}".replace(",", " ").replace(".", ",")
        return f"{formatted} so'm"
    except Exception:
        return f"{amount} so'm"
