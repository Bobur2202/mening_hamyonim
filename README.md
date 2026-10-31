# 💼 Mening Hamyonim — Shaxsiy moliya nazorati veb ilovasi

Zamonaviy, to‘liq o‘zbek tilida yaratilgan, shaxsiy daromad va xarajatlarni nazorat qilish, oylik budjet chegaralarini belgilash hamda moliyaviy tahlillarni grafiklarda ko‘rish imkonini beruvchi qulay veb ilova.

---

## 🚀 Asosiy imkoniyatlar

1. **Foydalanuvchilar tizimi**:
   - Ro‘yxatdan o‘tish (Register), tizimga kirish (Login) va chiqish (Logout).
   - Har bir foydalanuvchi **faqat o‘z ma’lumotlarini** ko‘radi va boshqaradi (ma’lumotlar to‘liq izolatsiya qilingan).
   - Yangi ro‘yxatdan o‘tgan foydalanuvchiga 14 ta standart daromad va xarajat kategoriyalari avtomatik tayyorlab beriladi.

2. **Daromad va xarajatlar boshqaruvi (CRUD)**:
   - Operatsiya turi (Daromad / Xarajat), summa, sana, kategoriya va izoh kiritish.
   - Barcha pul hisob-kitoblarida suzuvchi nuqta (float) xatolarini oldini olish uchun **`Decimal`** ishlatilgan.
   - Summalar O‘zbekiston so‘mida (UZS) chiroyli ajratilgan holda ko‘rsatiladi (masalan: `1 250 000 so'm`).

3. **Shaxsiy kategoriyalar**:
   - Foydalanuvchi o‘ziga xos kategoriyalar (nomi, turi, maxsus rangi va belgisi/ikonkasi) yarata oladi, tahrirlaydi va o‘chiradi.

4. **Dashboard (Bosh sahifa ko‘rsatkichlari)**:
   - Joriy umumiy balans, oylik daromad va oylik xarajat kartalari.
   - **Kategoriyalar bo‘yicha xarajatlar diagrammasi** (Chart.js Doughnut chart).
   - **Oxirgi 6 oylik daromad va xarajat dinamikasi** (Chart.js Bar chart).
   - Oxirgi amalga oshirilgan operatsiyalar ro‘yxati.

5. **Oylik budjet nazorati**:
   - Har bir oy uchun umumiy xarajat limitini belgilash.
   - Alohida kategoriyalar (masalan, faqat Oziq-ovqat yoki Transport) bo‘yicha oylik budjet belgilash.
   - Haqiqiy sarflangan summa, foizli dinamik progress bar, qolgan mablag‘ va limitdan oshib ketganda avtomatik ogohlantirish.

6. **Filtrlash va CSV eksport**:
   - Sana oralig‘i (dan - gacha), operatsiya turi (barchasi, daromad, xarajat), kategoriya va izoh bo‘yicha ko‘p parametrli filtrlash.
   - Filtrlangan operatsiyalarni bir tugma orqali **CSV** formatida yuklab olish (Excel dasturida o‘zbekcha matnlar buzilmasligi uchun UTF-8 BOM bilan saqlanadi).

7. **Moslashuvchan interfeys (Mobile Responsive)**:
   - Bootstrap 5 va zamonaviy UI yordamida telefon va planshet ekranlariga to‘liq moslashtirilgan.
   - Mobil qurilmalarda qulay pastki navigatsiya paneli (Bottom Navigation) va tezkor qo‘shish Floating tugmasi (FAB).

---

## 🛠 Texnologiyalar

- **Backend**: Python 3.13+, Django 6.1+
- **Ma’lumotlar bazasi**: SQLite3
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5.3, Bootstrap Icons, Chart.js
- **Xavfsizlik & Konfiguratsiya**: `python-dotenv` (`.env` faylida maxfiy kalitlarni saqlash)

---

## 📥 O‘rnatish va ishga tushirish yo‘riqnomasi

### 1. Loyiha papkasiga o‘tish
```bash
cd mening_hamyonim
```

### 2. Virtual muhitni yaratish va faollashtirish

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Kutubxonalarni o‘rnatish
```bash
pip install -r requirements.txt
```

### 4. Muhit o‘zgaruvchilarini sozlash (`.env`)
Loyiha papkasida `.env` fayli mavjud bo‘lmasa, `.env.example` dan nusxa olib `.env` faylini yarating:
```bash
cp .env.example .env
```
`.env` fayli ichida quyidagilar bo‘ladi:
```env
SECRET_KEY=django-insecure-m3n1ng-h4my0n1m-s3cr3t-k3y-uzb-2026-f1n4nc3
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 5. Ma’lumotlar bazasi migratsiyalarini qo‘llash
```bash
python manage.py migrate
```

### 6. Namuna ma’lumotlarini yuklash (Demo foydalanuvchi)
Oxirgi 6 oylik to‘liq reallikka yaqin operatsiyalar va budjetlarni yuklash uchun quyidagi buyruqni bajaring:
```bash
python manage.py load_sample_data
```
Ushbu buyruq avtomatik tarzda quyidagi foydalanuvchini yaratadi:
- **Login**: `demo`
- **Parol**: `demo12345`

*(Ixtiyoriy: admin panelga kirish uchun `python manage.py createsuperuser` orqali yangi admin ham yaratishingiz mumkin)*

### 7. Loyihani ishga tushirish
```bash
python manage.py runserver
```

Endi brauzeringizda quyidagi manzilni oching:
👉 **http://127.0.0.1:8000/**

---

## 🧪 Avtomatlashtirilgan testlarni tekshirish

Loyiha uchun Decimal hisob-kitoblari aniqligi, foydalanuvchilar ma’lumotlari to‘liq ajratilganligi (Data Isolation), CSV eksporti va CRUD funksiyalarini tekshiruvchi testlar yozilgan.

Testlarni ishga tushirish uchun:
```bash
python manage.py test wallet
```

Barcha 9 ta test xatoliksiz muvaffaqiyatli bajariladi (`OK`).

Shuningdek, to‘liq tizim tekshiruvi skripti:
```bash
python wallet/verify_system.py
```

---

## 📁 Loyiha kataloglari tuzilishi

```text
mening_hamyonim/
├── config/                 # Django loyihasi asosiy sozlamalari
│   ├── __init__.py
│   ├── settings.py         # .env bilan integratsiyalangan sozlamalar
│   ├── urls.py             # Asosiy URL marshrutlari
│   └── wsgi.py
├── wallet/                 # "Mening hamyonim" asosiy ilovasi
│   ├── migrations/         # Ma'lumotlar bazasi migratsiyalari
│   ├── management/
│   │   └── commands/
│   │       └── load_sample_data.py # Demo ma'lumotlarni yuklovchi maxsus buyruq
│   ├── templatetags/
│   │   └── wallet_tags.py  # So'm formatlash va yordamchi template filtrlar
│   ├── admin.py            # Django Admin konfiguratsiyasi
│   ├── forms.py            # Foydalanuvchi, operatsiya, kategoriya va budjet formalari
│   ├── models.py           # Category, Transaction, MonthlyBudget modellari (Decimal)
│   ├── tests.py            # 9 ta to'liq unit va integratsion testlar
│   ├── urls.py             # Wallet ichki sahifalar marshrutlari
│   ├── utils.py            # Standart kategoriyalar va valyuta formati
│   ├── verify_system.py    # Jonli tizim verifikatsiyasi skripti
│   └── views.py            # Dashboard, CRUD, CSV eksport va API viewlari
├── templates/
│   └── wallet/
│       ├── base.html       # Asosiy shablon (Bootstrap 5, Chart.js, Mobile Nav)
│       ├── login.html      # Tizimga kirish sahifasi
│       ├── register.html   # Ro'yxatdan o'tish sahifasi
│       ├── dashboard.html  # Asosiy ko'rsatkichlar va grafiklar
│       ├── transactions.html # Filtrlash, jadval va CSV yuklab olish
│       ├── transaction_form.html # Operatsiya qo'shish / tahrirlash
│       ├── categories.html # Foydalanuvchi kategoriyalari
│       ├── category_form.html
│       ├── budgets.html    # Oylik budjetlar va progress bar
│       ├── budget_form.html
│       └── confirm_delete.html # O'chirishni tasdiqlash
├── static/
│   └── css/
│       └── custom.css
├── .env                    # Maxfiy kalitlar (git'ga kirmaydi)
├── .env.example            # Muhit namunasi
├── .gitignore
├── db.sqlite3              # SQLite ma'lumotlar bazasi
├── requirements.txt        # Kerakli Python kutubxonalari
└── README.md               # Loyiha qo'llanmasi
```
