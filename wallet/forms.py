import decimal
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from .models import Transaction, Category, MonthlyBudget


UZBEK_MONTHS = [
    (1, 'Yanvar'),
    (2, 'Fevral'),
    (3, 'Mart'),
    (4, 'Aprel'),
    (5, 'May'),
    (6, 'Iyun'),
    (7, 'Iyul'),
    (8, 'Avgust'),
    (9, 'Sentyabr'),
    (10, 'Oktyabr'),
    (11, 'Noyabr'),
    (12, 'Dekabr'),
]


class UserRegisterForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=50,
        required=True,
        label="Ismingiz",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ismingizni kiriting'})
    )
    last_name = forms.CharField(
        max_length=50,
        required=False,
        label="Familiyangiz",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Familiyangizni kiriting'})
    )
    email = forms.EmailField(
        required=True,
        label="Elektron pochta (Email)",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'pochta@misol.uz'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = "Foydalanuvchi nomi (login)"
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Masalan: ali_valiyev'
        })
        self.fields['username'].help_text = "Faqat harflar, raqamlar va @/./+/-/_ belgilari ruxsat etiladi."
        if 'password1' in self.fields:
            self.fields['password1'].label = "Parol"
            self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Kuchli parol tanlang'})
        if 'password2' in self.fields:
            self.fields['password2'].label = "Parolni tasdiqlang"
            self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Parolni qayta kiriting'})


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['type', 'amount', 'category', 'date', 'description']
        widgets = {
            'type': forms.Select(attrs={'class': 'form-select', 'id': 'id_type'}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': '0.00',
                'step': '100',
                'min': '0.01'
            }),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Qisqa izoh kiriting (masalan: Bozorlik, Tushlik, Oylik...)'
            }),
        }
        labels = {
            'type': "Operatsiya turi",
            'amount': "Summa (so'mda)",
            'category': "Kategoriya",
            'date': "Sana",
            'description': "Izoh",
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user:
            self.fields['category'].queryset = Category.objects.filter(user=user)
        else:
            self.fields['category'].queryset = Category.objects.none()
        
        self.fields['category'].widget.attrs.update({'class': 'form-select', 'id': 'id_category'})
        self.fields['category'].empty_label = "--- Kategoriyani tanlang ---"
        self.fields['category'].required = True

        if not self.initial.get('date'):
            self.initial['date'] = timezone.localdate()

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= decimal.Decimal('0.00'):
            raise forms.ValidationError("Summa noldan katta bo'lishi kerak.")
        return amount

    def clean(self):
        cleaned_data = super().clean()
        trans_type = cleaned_data.get('type')
        category = cleaned_data.get('category')

        if category and trans_type and category.type != trans_type:
            raise forms.ValidationError(
                f"Tanlangan kategoriya ({category.name}) {category.get_type_display().lower()} toifasiga tegishli. "
                f"Iltimos, mos kategoriyani tanlang."
            )
        return cleaned_data


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'type', 'color', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Masalan: Kitoblar, Internet'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color', 'title': 'Rangni tanlang'}),
            'icon': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('bi-tag', 'Yorliq (Tag)'),
                ('bi-cart4', 'Savatcha / Bozorlik'),
                ('bi-cup-hot', 'Qahva / Tushlik'),
                ('bi-house', 'Uy-joy'),
                ('bi-house-gear', 'Kommunal to\'lovlar'),
                ('bi-car-front', 'Avtomobil / Yoqilg\'i'),
                ('bi-airplane', 'Sayohat / Parvoz'),
                ('bi-heart-pulse', 'Tibbiyot / Salomatlik'),
                ('bi-book', 'Ta\'lim / Kitoblar'),
                ('bi-bag', 'Kiyim-kechak / Xarid'),
                ('bi-phone', 'Telefon / Aloqa'),
                ('bi-laptop', 'IT / Texnika'),
                ('bi-cash-stack', 'Naqd pul / Oylik'),
                ('bi-credit-card', 'Karta / To\'lov'),
                ('bi-gift', 'Sovg\'a / Mukofot'),
                ('bi-graph-up-arrow', 'Investitsiya / O\'sish'),
                ('bi-wallet2', 'Hamyon'),
            ])
        }
        labels = {
            'name': "Kategoriya nomi",
            'type': "Turi",
            'color': "Ajratuvchi rang",
            'icon': "Ikonka belgisi",
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError("Kategoriya nomini kiritish shart.")
        return name

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        cat_type = cleaned_data.get('type')
        if name and cat_type and self.user:
            qs = Category.objects.filter(user=self.user, name__iexact=name, type=cat_type)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(f"Sizda allaqachon '{name}' nomli {cat_type} kategoriyasi mavjud.")
        return cleaned_data


class MonthlyBudgetForm(forms.ModelForm):
    month = forms.ChoiceField(
        choices=UZBEK_MONTHS,
        label="Oy",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = MonthlyBudget
        fields = ['year', 'month', 'category', 'amount']
        widgets = {
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': 2020, 'max': 2040}),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': "Maksimal xarajat summasi (so'm)",
                'step': '1000',
                'min': '100'
            }),
        }
        labels = {
            'year': "Yil",
            'month': "Oy",
            'category': "Kategoriya (bo'sh qoldirilsa: barcha xarajatlar uchun umumiy budjet)",
            'amount': "Rejalashtirilgan budjet (so'm)",
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        now = timezone.localdate()
        if not self.initial.get('year'):
            self.initial['year'] = now.year
        if not self.initial.get('month'):
            self.initial['month'] = now.month

        if user:
            # Faqat xarajat kategoriyalari budjet uchun mantiqiy
            self.fields['category'].queryset = Category.objects.filter(
                user=user,
                type=Category.TYPE_EXPENSE
            )
        else:
            self.fields['category'].queryset = Category.objects.none()
        
        self.fields['category'].widget.attrs.update({'class': 'form-select'})
        self.fields['category'].empty_label = "🌟 Umumiy oylik xarajatlar budjeti"
        self.fields['category'].required = False

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= decimal.Decimal('0.00'):
            raise forms.ValidationError("Budjet summasi noldan katta bo'lishi kerak.")
        return amount

    def clean(self):
        cleaned_data = super().clean()
        year = cleaned_data.get('year')
        month = cleaned_data.get('month')
        category = cleaned_data.get('category')

        if year and month and self.user:
            qs = MonthlyBudget.objects.filter(
                user=self.user,
                year=year,
                month=month,
                category=category
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                cat_label = category.name if category else "Umumiy xarajat"
                raise forms.ValidationError(
                    f"{year}-yil {month}-oy uchun '{cat_label}' budjeti allaqachon mavjud! "
                    f"Mavjud budjetni tahrirlashingiz mumkin."
                )
        return cleaned_data
