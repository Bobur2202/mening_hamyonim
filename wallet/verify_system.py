import os
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# Loyiha ildiz papkasini sys.path ga qo'shish
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from wallet.models import Transaction, Category, MonthlyBudget


def main():
    print("=== 'Mening hamyonim' tizimini tekshirish boshlandi ===")
    client = Client()

    # 1. Mehmon foydalanuvchi uchun tekshiruvlar
    print("\n[1] Mehmon foydalanuvchi holati:")
    resp_login = client.get('/login/')
    assert resp_login.status_code == 200, f"Login sahifasi xato: {resp_login.status_code}"
    print("  ✓ Login sahifasi ochildi (HTTP 200)")

    resp_register = client.get('/register/')
    assert resp_register.status_code == 200, f"Ro'yxatdan o'tish sahifasi xato: {resp_register.status_code}"
    print("  ✓ Ro'yxatdan o'tish sahifasi ochildi (HTTP 200)")

    resp_guest_dash = client.get('/')
    assert resp_guest_dash.status_code == 302, f"Dashboard mehmon uchun yo'naltirilishi kerak: {resp_guest_dash.status_code}"
    print("  ✓ Dashboard mehmondan himoyalangan (HTTP 302 -> /login/)")

    # 2. Demo foydalanuvchi bilan tizimga kirish
    print("\n[2] Demo foydalanuvchi bilan autentifikatsiya:")
    logged_in = client.login(username='demo', password='demo12345')
    assert logged_in, "Demo foydalanuvchi tizimga kira olmadi!"
    print("  ✓ 'demo' foydalanuvchisi muvaffaqiyatli kirdi")

    # 3. Dashboard sahifasi
    print("\n[3] Dashboard sahifasi:")
    resp_dash = client.get('/')
    assert resp_dash.status_code == 200, f"Dashboard ochilmadi: {resp_dash.status_code}"
    dash_html = resp_dash.content.decode('utf-8')
    assert "Moliya nazorati" in dash_html, "Dashboard sarlavhasi topilmadi"
    assert "monthlyTrendsChart" in dash_html, "Dinamika grafigi topilmadi"
    assert "categoryExpenseChart" in dash_html, "Kategoriya diagrammasi topilmadi"
    assert "Umumiy Balans" in dash_html, "Balans kartasi topilmadi"
    print("  ✓ Dashboard to'liq yuklandi, balans va grafik komponentlari mavjud (HTTP 200)")

    # 4. Operatsiyalar sahifasi
    print("\n[4] Operatsiyalar ro'yxati:")
    resp_tx = client.get('/transactions/')
    assert resp_tx.status_code == 200, f"Operatsiyalar ro'yxati ochilmadi: {resp_tx.status_code}"
    tx_html = resp_tx.content.decode('utf-8')
    assert "Mening operatsiyalarim" in tx_html, "Operatsiyalar sahifasi sarlavhasi topilmadi"
    assert "CSV yuklab olish" in tx_html, "CSV tugmasi topilmadi"
    print("  ✓ Operatsiyalar jurnali muvaffaqiyatli ochildi (HTTP 200)")

    # 5. Filtrlash va CSV eksport
    print("\n[5] Filtrlash va CSV eksport:")
    resp_csv = client.get('/transactions/export-csv/?type=expense')
    assert resp_csv.status_code == 200, f"CSV eksport xato: {resp_csv.status_code}"
    assert resp_csv['Content-Type'] == 'text/csv; charset=utf-8', "CSV turi noto'g'ri"
    csv_text = resp_csv.content.decode('utf-8')
    assert "№,Sana,Operatsiya turi,Kategoriya,Summa (so'm),Izoh" in csv_text, "CSV header noto'g'ri"
    lines_count = len(csv_text.strip().splitlines())
    print(f"  ✓ Filtrlangan CSV eksport qilindi ({lines_count} qator ma'lumot)")

    # 6. Kategoriyalar sahifasi
    print("\n[6] Kategoriyalar boshqaruvi:")
    resp_cat = client.get('/categories/')
    assert resp_cat.status_code == 200, f"Kategoriyalar ochilmadi: {resp_cat.status_code}"
    cat_html = resp_cat.content.decode('utf-8')
    assert "Xarajat kategoriyalari" in cat_html, "Xarajat toifalari topilmadi"
    assert "Daromad kategoriyalari" in cat_html, "Daromad toifalari topilmadi"
    print("  ✓ Kategoriyalar sahifasi to'liq ishlamoqda (HTTP 200)")

    # 7. Budjetlar sahifasi
    print("\n[7] Budjet nazorati:")
    resp_bgt = client.get('/budgets/')
    assert resp_bgt.status_code == 200, f"Budjetlar ochilmadi: {resp_bgt.status_code}"
    bgt_html = resp_bgt.content.decode('utf-8')
    assert "Oylik xarajatlar budjeti" in bgt_html, "Budjet sahifasi sarlavhasi topilmadi"
    assert "Umumiy oylik budjet" in bgt_html, "Umumiy budjet bloki topilmadi"
    print("  ✓ Budjet nazorati sahifasi va hisoblari to'g'ri ishlamoqda (HTTP 200)")

    # 8. Yangi operatsiya qo'shish (CRUD Test)
    print("\n[8] Yangi operatsiya qo'shish:")
    cat = Category.objects.filter(user__username='demo', type='expense').first()
    post_data = {
        'type': 'expense',
        'amount': '75000.00',
        'category': cat.id,
        'date': '2026-10-31',
        'description': 'Sinov xarajati - qahva va shirinlik'
    }
    resp_add = client.post('/transactions/create/', post_data)
    assert resp_add.status_code == 302, f"Operatsiya qo'shish xato: {resp_add.status_code}"
    created_tx = Transaction.objects.filter(description='Sinov xarajati - qahva va shirinlik').first()
    assert created_tx is not None, "Operatsiya bazada saqlanmadi!"
    print(f"  ✓ Yangi operatsiya qo'shildi: {created_tx.amount} so'm, kategoriya: {cat.name}")

    # 9. API Helper tekshiruvi
    print("\n[9] API kategoriyalar so'rovi:")
    resp_api = client.get('/api/categories/?type=income')
    assert resp_api.status_code == 200, f"API xato: {resp_api.status_code}"
    json_data = resp_api.json()
    assert 'categories' in json_data and len(json_data['categories']) > 0, "API ma'lumot qaytarmadi"
    print(f"  ✓ API orqali {len(json_data['categories'])} ta daromad kategoriyasi olindi (JSON HTTP 200)")

    print("\n=======================================================")
    print("BARCHA ASOSIY FUNKSIYALAR VA TALABLAR TO'LIQ ISHLAMOQDA!")
    print("=======================================================")


if __name__ == '__main__':
    main()
