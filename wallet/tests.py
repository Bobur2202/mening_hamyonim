import decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from wallet.models import Category, Transaction, MonthlyBudget
from wallet.utils import create_default_categories


class FinanceCalculationTests(TestCase):
    """1. Hisob-kitoblar va Decimal aniqligi bo'yicha testlar."""

    def setUp(self):
        self.user = User.objects.create_user(username='hisobchi', password='testpassword123')
        self.cat_income = Category.objects.create(
            user=self.user, name='Oylik', type=Category.TYPE_INCOME
        )
        self.cat_expense = Category.objects.create(
            user=self.user, name='Bozorlik', type=Category.TYPE_EXPENSE
        )

    def test_decimal_precision_calculations(self):
        """Decimal hisoblashlarda float yaxlitlash xatosi bo'lmasligini tekshirish."""
        t1 = Transaction.objects.create(
            user=self.user,
            category=self.cat_income,
            type=Transaction.TYPE_INCOME,
            amount=decimal.Decimal('10000000.33'),
            date=timezone.localdate()
        )
        t2 = Transaction.objects.create(
            user=self.user,
            category=self.cat_expense,
            type=Transaction.TYPE_EXPENSE,
            amount=decimal.Decimal('3333333.11'),
            date=timezone.localdate()
        )

        expected_balance = decimal.Decimal('10000000.33') - decimal.Decimal('3333333.11')
        self.assertEqual(expected_balance, decimal.Decimal('6666667.22'))

    def test_budget_calculations(self):
        """Budjet sarflanishi, qoldig'i va foiz hisob-kitoblarini tekshirish."""
        today = timezone.localdate()
        budget = MonthlyBudget.objects.create(
            user=self.user,
            year=today.year,
            month=today.month,
            category=self.cat_expense,
            amount=decimal.Decimal('1000000.00')
        )

        # Hali xarajat qilinmagan
        self.assertEqual(budget.spent_amount, decimal.Decimal('0.00'))
        self.assertEqual(budget.remaining_amount, decimal.Decimal('1000000.00'))
        self.assertEqual(budget.percentage, 0)
        self.assertFalse(budget.is_exceeded)

        # 400 000 so'm xarajat qilamiz
        Transaction.objects.create(
            user=self.user,
            category=self.cat_expense,
            type=Transaction.TYPE_EXPENSE,
            amount=decimal.Decimal('400000.00'),
            date=today
        )

        self.assertEqual(budget.spent_amount, decimal.Decimal('400000.00'))
        self.assertEqual(budget.remaining_amount, decimal.Decimal('600000.00'))
        self.assertEqual(budget.percentage, 40.0)
        self.assertFalse(budget.is_exceeded)

        # Yana 700 000 so'm xarajat qilamiz (jami 1 100 000 so'm -> limitdan oshadi)
        Transaction.objects.create(
            user=self.user,
            category=self.cat_expense,
            type=Transaction.TYPE_EXPENSE,
            amount=decimal.Decimal('700000.00'),
            date=today
        )

        self.assertEqual(budget.spent_amount, decimal.Decimal('1100000.00'))
        self.assertEqual(budget.remaining_amount, decimal.Decimal('-100000.00'))
        self.assertTrue(budget.is_exceeded)


class UserDataIsolationTests(TestCase):
    """2. Foydalanuvchilar ma'lumotlarining xavfsiz ajratilishi (Data Isolation) testlari."""

    def setUp(self):
        self.client_a = Client()
        self.client_b = Client()

        self.user_a = User.objects.create_user(username='user_a', password='passA12345')
        self.user_b = User.objects.create_user(username='user_b', password='passB12345')

        self.client_a.login(username='user_a', password='passA12345')
        self.client_b.login(username='user_b', password='passB12345')

        # User A uchun ma'lumotlar
        self.cat_a = Category.objects.create(user=self.user_a, name='A Kategoriyasi', type='expense')
        self.tx_a = Transaction.objects.create(
            user=self.user_a,
            category=self.cat_a,
            type=Transaction.TYPE_EXPENSE,
            amount=decimal.Decimal('500000.00'),
            date=timezone.localdate(),
            description="Maxfiy xarajat A"
        )
        self.budget_a = MonthlyBudget.objects.create(
            user=self.user_a,
            year=2026,
            month=10,
            amount=decimal.Decimal('2000000.00')
        )

        # User B uchun ma'lumotlar
        self.cat_b = Category.objects.create(user=self.user_b, name='B Kategoriyasi', type='expense')
        self.tx_b = Transaction.objects.create(
            user=self.user_b,
            category=self.cat_b,
            type=Transaction.TYPE_EXPENSE,
            amount=decimal.Decimal('100000.00'),
            date=timezone.localdate(),
            description="B ning xarajati"
        )

    def test_user_b_cannot_see_user_a_transactions(self):
        """User B o'z operatsiyalar ro'yxatida User A ning ma'lumotlarini ko'rmasligi kerak."""
        response = self.client_b.get(reverse('transactions'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        self.assertIn("B ning xarajati", content)
        self.assertNotIn("Maxfiy xarajat A", content)

    def test_user_b_cannot_update_or_delete_user_a_transaction(self):
        """User B User A ning tranzaksiyasini tahrirlay yoki o'chira olmasligi kerak (404 Not Found)."""
        update_url = reverse('transaction_update', kwargs={'pk': self.tx_a.pk})
        resp_get = self.client_b.get(update_url)
        self.assertEqual(resp_get.status_code, 404)

        resp_post = self.client_b.post(update_url, {'amount': '999999'})
        self.assertEqual(resp_post.status_code, 404)

        delete_url = reverse('transaction_delete', kwargs={'pk': self.tx_a.pk})
        resp_del = self.client_b.post(delete_url)
        self.assertEqual(resp_del.status_code, 404)

        self.assertTrue(Transaction.objects.filter(pk=self.tx_a.pk).exists())

    def test_user_b_cannot_delete_user_a_category_or_budget(self):
        """User B User A ning kategoriyasi yoki budjetini o'chira olmasligi kerak."""
        cat_del_url = reverse('category_delete', kwargs={'pk': self.cat_a.pk})
        resp_cat = self.client_b.post(cat_del_url)
        self.assertEqual(resp_cat.status_code, 404)

        budget_del_url = reverse('budget_delete', kwargs={'pk': self.budget_a.pk})
        resp_bgt = self.client_b.post(budget_del_url)
        self.assertEqual(resp_bgt.status_code, 404)


class CSVExportTests(TestCase):
    """3. Filtrlash va CSV formatida yuklab olish testlari."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='eksportchi', password='testpass123')
        self.client.login(username='eksportchi', password='testpass123')

        self.cat1 = Category.objects.create(user=self.user, name='Oziq-ovqat', type=Category.TYPE_EXPENSE)
        self.cat2 = Category.objects.create(user=self.user, name='Maosh', type=Category.TYPE_INCOME)

        Transaction.objects.create(
            user=self.user,
            category=self.cat1,
            type=Transaction.TYPE_EXPENSE,
            amount=decimal.Decimal('150000.00'),
            date=timezone.localdate(),
            description="Supermarket xaridi"
        )
        Transaction.objects.create(
            user=self.user,
            category=self.cat2,
            type=Transaction.TYPE_INCOME,
            amount=decimal.Decimal('5000000.00'),
            date=timezone.localdate(),
            description="Avans to'lovi"
        )

    def test_csv_export_response_and_content(self):
        """CSV eksport to'g'ri status, sarlavha va ma'lumotlarni qaytarishini tekshirish."""
        response = self.client.get(reverse('export_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('attachment; filename="hamyonim_operatsiyalar_', response['Content-Disposition'])

        content = response.content.decode('utf-8')
        self.assertTrue(content.startswith('\ufeff'))

        self.assertIn("№,Sana,Operatsiya turi,Kategoriya,Summa (so'm),Izoh", content)
        self.assertIn("Supermarket xaridi", content)
        self.assertIn("150000.00", content)
        self.assertIn("Avans to'lovi", content)
        self.assertIn("5000000.00", content)
        self.assertIn("JAMI DAROMAD:", content)
        self.assertIn("JAMI XARAJAT:", content)
        self.assertIn("SOF QOLDIQ:", content)

    def test_filtered_csv_export(self):
        """CSV eksportida filtrlash to'g'ri ishlashini tekshirish."""
        response = self.client.get(reverse('export_csv') + '?type=expense')
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        self.assertIn("Supermarket xaridi", content)
        self.assertNotIn("Avans to'lovi", content)


class UserWorkflowAndCRUDTests(TestCase):
    """4. Foydalanuvchi ro'yxatdan o'tishi va CRUD funksiyalarini tekshirish."""

    def setUp(self):
        self.client = Client()

    def test_user_registration_creates_default_categories(self):
        """Yangi ro'yxatdan o'tgan foydalanuvchiga standart kategoriyalar avtomatik yaratilishi."""
        response = self.client.post(reverse('register'), {
            'username': 'yangi_foydalanuvchi',
            'first_name': 'Anvar',
            'last_name': 'Qodirov',
            'email': 'anvar@example.com',
            'password1': 'KuchliParol123!',
            'password2': 'KuchliParol123!'
        })
        self.assertEqual(response.status_code, 302)  # dashboardga yo'naltiriladi
        user = User.objects.get(username='yangi_foydalanuvchi')
        self.assertIsNotNone(user)

        # Standart kategoriyalar mavjudligini tekshirish
        cat_count = Category.objects.filter(user=user).count()
        self.assertGreaterEqual(cat_count, 10)
        self.assertTrue(Category.objects.filter(user=user, name="Oylik maosh").exists())
        self.assertTrue(Category.objects.filter(user=user, name="Oziq-ovqat va bozor").exists())

    def test_transaction_crud_workflow(self):
        """Operatsiya qo'shish, tahrirlash va o'chirish jarayoni."""
        user = User.objects.create_user(username='sinovchi', password='Password123!')
        self.client.login(username='sinovchi', password='Password123!')
        cat = Category.objects.create(user=user, name='Transport', type='expense')

        # 1. Qo'shish
        add_resp = self.client.post(reverse('transaction_create'), {
            'type': 'expense',
            'amount': '45000.00',
            'category': cat.pk,
            'date': '2026-10-31',
            'description': 'Taksi yo\'l kira'
        })
        self.assertEqual(add_resp.status_code, 302)
        tx = Transaction.objects.filter(user=user, description='Taksi yo\'l kira').first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.amount, decimal.Decimal('45000.00'))

        # 2. Tahrirlash
        edit_resp = self.client.post(reverse('transaction_update', kwargs={'pk': tx.pk}), {
            'type': 'expense',
            'amount': '55000.00',
            'category': cat.pk,
            'date': '2026-10-31',
            'description': 'Taksi yo\'l kira (tahrirlandi)'
        })
        self.assertEqual(edit_resp.status_code, 302)
        tx.refresh_from_db()
        self.assertEqual(tx.amount, decimal.Decimal('55000.00'))
        self.assertEqual(tx.description, 'Taksi yo\'l kira (tahrirlandi)')

        # 3. O'chirish
        del_resp = self.client.post(reverse('transaction_delete', kwargs={'pk': tx.pk}))
        self.assertEqual(del_resp.status_code, 302)
        self.assertFalse(Transaction.objects.filter(pk=tx.pk).exists())
