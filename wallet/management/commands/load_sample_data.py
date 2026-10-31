import decimal
import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone

from wallet.models import Category, Transaction, MonthlyBudget
from wallet.utils import create_default_categories


class Command(BaseCommand):
    help = "Moliya ilovasi uchun namuna ma'lumotlarini yuklaydi (demo foydalanuvchi va operatsiyalar)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='demo',
            help='Namuna ma\'lumotlari biriktiriladigan login (sukut bo\'yicha: demo)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='demo12345',
            help='Demo foydalanuvchi paroli (sukut bo\'yicha: demo12345)'
        )

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': 'Jasur',
                'last_name': 'Bekmurodov',
                'email': 'demo@hamyonim.uz',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Yangi demo foydalanuvchi yaratildi: {username} (parol: {password})"))
        else:
            self.stdout.write(self.style.NOTICE(f"Mavjud foydalanuvchi tanlandi: {username}"))

        # Kategoriyalarni yaratish
        create_default_categories(user)
        categories = {c.name: c for c in Category.objects.filter(user=user)}

        # Eski operatsiyalarni tozalash (demo uchun yangidan yuklash)
        Transaction.objects.filter(user=user).delete()
        MonthlyBudget.objects.filter(user=user).delete()

        today = timezone.localdate()
        self.stdout.write("Oxirgi 6 oylik ma'lumotlar generatsiya qilinmoqda...")

        # 6 oylik ma'lumotlarni yaratish
        transactions_to_create = []

        for month_offset in range(5, -1, -1):
            # Taxminiy oy sanasi
            m_date = today.replace(day=1) - timedelta(days=month_offset * 30)
            year = m_date.year
            month = m_date.month

            # 1. Oylik maosh (har oyning 5-sanasida)
            salary_cat = categories.get("Oylik maosh")
            if salary_cat:
                transactions_to_create.append(
                    Transaction(
                        user=user,
                        category=salary_cat,
                        type=Transaction.TYPE_INCOME,
                        amount=decimal.Decimal("9500000.00"),
                        date=m_date.replace(day=min(5, 28)),
                        description="Asosiy oylik maosh"
                    )
                )

            # 2. Qo'shimcha daromad / Frilans
            freelance_cat = categories.get("Frilans / Qo'shimcha ish")
            if freelance_cat and month_offset % 2 == 0:
                transactions_to_create.append(
                    Transaction(
                        user=user,
                        category=freelance_cat,
                        type=Transaction.TYPE_INCOME,
                        amount=decimal.Decimal("2200000.00"),
                        date=m_date.replace(day=min(18, 28)),
                        description="Veb-sayt dizayni uchun to'lov"
                    )
                )

            # 3. Keshbek
            invest_cat = categories.get("Investitsiya va keshbek")
            if invest_cat:
                transactions_to_create.append(
                    Transaction(
                        user=user,
                        category=invest_cat,
                        type=Transaction.TYPE_INCOME,
                        amount=decimal.Decimal(str(random.choice([150000, 240000, 310000]))),
                        date=m_date.replace(day=min(25, 28)),
                        description="Bank kartasi keshbeki"
                    )
                )

            # 4. Doimiy xarajatlar: Kommunal va internet
            comm_cat = categories.get("Kommunal va internet")
            if comm_cat:
                transactions_to_create.append(
                    Transaction(
                        user=user,
                        category=comm_cat,
                        type=Transaction.TYPE_EXPENSE,
                        amount=decimal.Decimal("480000.00"),
                        date=m_date.replace(day=min(10, 28)),
                        description="Gaz, elektr va Wi-Fi to'lovi"
                    )
                )

            # 5. Oziq-ovqat va bozor (oy davomida 4-5 marta)
            food_cat = categories.get("Oziq-ovqat va bozor")
            if food_cat:
                for day in [3, 9, 15, 21, 27]:
                    amt = random.choice([350000, 420000, 560000, 290000, 680000])
                    transactions_to_create.append(
                        Transaction(
                            user=user,
                            category=food_cat,
                            type=Transaction.TYPE_EXPENSE,
                            amount=decimal.Decimal(str(amt)),
                            date=m_date.replace(day=day),
                            description="Bozorlik va supermarket xaridi"
                        )
                    )

            # 6. Transport va yoqilg'i
            trans_cat = categories.get("Transport va yoqilg'i")
            if trans_cat:
                for day in [6, 14, 22]:
                    amt = random.choice([150000, 200000, 250000])
                    transactions_to_create.append(
                        Transaction(
                            user=user,
                            category=trans_cat,
                            type=Transaction.TYPE_EXPENSE,
                            amount=decimal.Decimal(str(amt)),
                            date=m_date.replace(day=day),
                            description="Benzin quyish va yo'l kira"
                        )
                    )

            # 7. Kafe va restoranlar
            cafe_cat = categories.get("Kafe va restoranlar")
            if cafe_cat:
                for day in [8, 19]:
                    amt = random.choice([120000, 180000, 260000])
                    transactions_to_create.append(
                        Transaction(
                            user=user,
                            category=cafe_cat,
                            type=Transaction.TYPE_EXPENSE,
                            amount=decimal.Decimal(str(amt)),
                            date=m_date.replace(day=day),
                            description="Do'stlar bilan tushlik"
                        )
                    )

            # 8. Oylik budjet belgilash
            MonthlyBudget.objects.create(
                user=user,
                year=year,
                month=month,
                category=None,
                amount=decimal.Decimal("5500000.00")
            )

            # Oziq-ovqat uchun maxsus budjet
            if food_cat:
                MonthlyBudget.objects.create(
                    user=user,
                    year=year,
                    month=month,
                    category=food_cat,
                    amount=decimal.Decimal("2500000.00")
                )

        Transaction.objects.bulk_create(transactions_to_create)

        self.stdout.write(self.style.SUCCESS(
            f"Muvaffaqiyatli yakunlandi! {len(transactions_to_create)} ta operatsiya va budjetlar yuklandi."
        ))
        self.stdout.write(self.style.SUCCESS(
            f"Saytga kirish uchun: Login: '{username}', Parol: '{password}'"
        ))
