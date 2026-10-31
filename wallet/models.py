import decimal
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Sum


class Category(models.Model):
    TYPE_INCOME = 'income'
    TYPE_EXPENSE = 'expense'
    TYPE_CHOICES = [
        (TYPE_INCOME, 'Daromad'),
        (TYPE_EXPENSE, 'Xarajat'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100, verbose_name="Kategoriya nomi")
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name="Turi")
    color = models.CharField(max_length=20, default='#3b82f6', verbose_name="Rang")
    icon = models.CharField(max_length=50, default='bi-tag', verbose_name="Belgi (ikonka)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"
        unique_together = ('user', 'name', 'type')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Transaction(models.Model):
    TYPE_INCOME = 'income'
    TYPE_EXPENSE = 'expense'
    TYPE_CHOICES = [
        (TYPE_INCOME, 'Daromad'),
        (TYPE_EXPENSE, 'Xarajat'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name="Kategoriya"
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name="Operatsiya turi")
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Summa (so'm)"
    )
    date = models.DateField(default=timezone.localdate, verbose_name="Sana")
    description = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name="Izoh"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Operatsiya"
        verbose_name_plural = "Operatsiyalar"
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.get_type_display()}: {self.amount:,.2f} so'm - {self.date}"


class MonthlyBudget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    year = models.PositiveIntegerField(verbose_name="Yil")
    month = models.PositiveSmallIntegerField(verbose_name="Oy")  # 1-12
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='budgets',
        verbose_name="Kategoriya (bo'sh qolsa umumiy)"
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Budjet summasi (so'm)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Oylik budjet"
        verbose_name_plural = "Oylik budjetlar"
        unique_together = ('user', 'year', 'month', 'category')
        ordering = ['-year', '-month']

    def __str__(self):
        cat_name = self.category.name if self.category else "Umumiy xarajat"
        return f"{self.year}-{self.month:02d} | {cat_name}: {self.amount:,.2f} so'm"

    def get_spent_amount(self):
        """Ushbu oy uchun qilingan xarajatlar summasini Decimal formatda hisoblaydi."""
        qs = Transaction.objects.filter(
            user=self.user,
            type=Transaction.TYPE_EXPENSE,
            date__year=self.year,
            date__month=self.month
        )
        if self.category:
            qs = qs.filter(category=self.category)
        
        total = qs.aggregate(total=Sum('amount'))['total']
        return total if total is not None else decimal.Decimal('0.00')

    @property
    def spent_amount(self):
        return self.get_spent_amount()

    @property
    def remaining_amount(self):
        return self.amount - self.spent_amount

    @property
    def percentage(self):
        if self.amount <= decimal.Decimal('0.00'):
            return 0
        percent = (self.spent_amount / self.amount) * decimal.Decimal('100.0')
        return min(round(float(percent), 1), 100.0)

    @property
    def is_exceeded(self):
        return self.spent_amount > self.amount

    @property
    def exceeded_amount(self):
        if self.is_exceeded:
            return self.spent_amount - self.amount
        return decimal.Decimal('0.00')
