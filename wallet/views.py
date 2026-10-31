import csv
import decimal
import json
from datetime import datetime, date, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Q
from django.core.paginator import Paginator
from django.utils import timezone

from .models import Transaction, Category, MonthlyBudget
from .forms import (
    UserRegisterForm,
    TransactionForm,
    CategoryForm,
    MonthlyBudgetForm,
    UZBEK_MONTHS
)
from .utils import create_default_categories


# ==========================================
# AUTH VIEWS
# ==========================================

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            create_default_categories(user)
            login(request, user)
            messages.success(request, f"Xush kelibsiz, {user.first_name or user.username}! Hisobingiz muvaffaqiyatli yaratildi.")
            return redirect('dashboard')
    else:
        form = UserRegisterForm()
    return render(request, 'wallet/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Xush kelibsiz, {user.first_name or user.username}!")
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
        else:
            messages.error(request, "Login yoki parol noto'g'ri kiritildi.")
    else:
        form = AuthenticationForm()
    return render(request, 'wallet/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "Tizimdan muvaffaqiyatli chiqdingiz.")
    return redirect('login')


# ==========================================
# DASHBOARD
# ==========================================

@login_required
def dashboard_view(request):
    user = request.user
    today = timezone.localdate()

    # Foydalanuvchi tanlagan oy va yil (sukut bo'yicha joriy sana)
    try:
        current_year = int(request.GET.get('year', today.year))
        current_month = int(request.GET.get('month', today.month))
        if current_month < 1 or current_month > 12:
            current_month = today.month
            current_year = today.year
    except (ValueError, TypeError):
        current_year = today.year
        current_month = today.month

    # Oldingi va keyingi oylarni hisoblash (navigatsiya uchun)
    prev_month = current_month - 1
    prev_year = current_year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1

    next_month = current_month + 1
    next_year = current_year
    if next_month == 13:
        next_month = 1
        next_year += 1

    # 1. Umumiy balans (barcha vaqt bo'yicha)
    income_agg = Transaction.objects.filter(
        user=user, type=Transaction.TYPE_INCOME
    ).aggregate(total=Sum('amount'))['total'] or decimal.Decimal('0.00')

    expense_agg = Transaction.objects.filter(
        user=user, type=Transaction.TYPE_EXPENSE
    ).aggregate(total=Sum('amount'))['total'] or decimal.Decimal('0.00')

    total_balance = income_agg - expense_agg

    # 2. Tanlangan oy statistikasi
    monthly_income = Transaction.objects.filter(
        user=user,
        type=Transaction.TYPE_INCOME,
        date__year=current_year,
        date__month=current_month
    ).aggregate(total=Sum('amount'))['total'] or decimal.Decimal('0.00')

    monthly_expense = Transaction.objects.filter(
        user=user,
        type=Transaction.TYPE_EXPENSE,
        date__year=current_year,
        date__month=current_month
    ).aggregate(total=Sum('amount'))['total'] or decimal.Decimal('0.00')

    monthly_balance = monthly_income - monthly_expense

    # 3. Tanlangan oy budjeti
    # Umumiy budjet
    general_budget = MonthlyBudget.objects.filter(
        user=user,
        year=current_year,
        month=current_month,
        category__isnull=True
    ).first()

    # Kategoriyalar bo'yicha budjetlar
    category_budgets = MonthlyBudget.objects.filter(
        user=user,
        year=current_year,
        month=current_month,
        category__isnull=False
    ).select_related('category')

    # 4. Kategoriyalar bo'yicha xarajatlar (Tanlangan oy uchun diagramma ma'lumotlari)
    cat_expenses = (
        Transaction.objects.filter(
            user=user,
            type=Transaction.TYPE_EXPENSE,
            date__year=current_year,
            date__month=current_month
        )
        .values('category__name', 'category__color')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    cat_labels = []
    cat_data = []
    cat_colors = []
    for item in cat_expenses:
        cat_labels.append(item['category__name'] or "Kategoriyasiz")
        cat_data.append(float(item['total']))
        cat_colors.append(item['category__color'] or "#94a3b8")

    # 5. Oxirgi 6 oylik daromad va xarajat grafikasi (matematik aniq orqaga hisoblash)
    def _get_last_6_months(y, m):
        res = []
        cur_y, cur_m = y, m
        for _ in range(6):
            res.append((cur_y, cur_m))
            cur_m -= 1
            if cur_m == 0:
                cur_m = 12
                cur_y -= 1
        return list(reversed(res))

    monthly_trends = []
    for y, m in _get_last_6_months(current_year, current_month):
        month_name = dict(UZBEK_MONTHS).get(m, str(m))

        inc = Transaction.objects.filter(
            user=user, type=Transaction.TYPE_INCOME, date__year=y, date__month=m
        ).aggregate(total=Sum('amount'))['total'] or decimal.Decimal('0.00')

        exp = Transaction.objects.filter(
            user=user, type=Transaction.TYPE_EXPENSE, date__year=y, date__month=m
        ).aggregate(total=Sum('amount'))['total'] or decimal.Decimal('0.00')

        monthly_trends.append({
            'label': f"{month_name[:3]} {y}",
            'income': float(inc),
            'expense': float(exp),
        })

    # 6. Oxirgi 6 ta operatsiya
    recent_transactions = Transaction.objects.filter(user=user).select_related('category')[:6]

    context = {
        'total_balance': total_balance,
        'total_income': income_agg,
        'total_expense': expense_agg,
        'monthly_income': monthly_income,
        'monthly_expense': monthly_expense,
        'monthly_balance': monthly_balance,
        'general_budget': general_budget,
        'category_budgets': category_budgets,
        'recent_transactions': recent_transactions,
        'current_year': current_year,
        'current_month': current_month,
        'current_month_name': dict(UZBEK_MONTHS).get(current_month, ''),
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'is_current_actual_month': (current_year == today.year and current_month == today.month),
        'chart_categories_labels': json.dumps(cat_labels),
        'chart_categories_data': json.dumps(cat_data),
        'chart_categories_colors': json.dumps(cat_colors),
        'chart_trends_labels': json.dumps([t['label'] for t in monthly_trends]),
        'chart_trends_income': json.dumps([t['income'] for t in monthly_trends]),
        'chart_trends_expense': json.dumps([t['expense'] for t in monthly_trends]),
    }
    return render(request, 'wallet/dashboard.html', context)


# ==========================================
# TRANSACTIONS CRUD & FILTERS
# ==========================================

def _get_filtered_transactions(user, get_params):
    """Filtrlangan tranzaksiyalar querysetini qaytaruvchi yordamchi funksiya."""
    qs = Transaction.objects.filter(user=user).select_related('category')

    start_date = get_params.get('start_date')
    end_date = get_params.get('end_date')
    op_type = get_params.get('type')
    category_id = get_params.get('category')
    q = get_params.get('q')

    if start_date:
        qs = qs.filter(date__gte=start_date)
    if end_date:
        qs = qs.filter(date__lte=end_date)
    if op_type in [Transaction.TYPE_INCOME, Transaction.TYPE_EXPENSE]:
        qs = qs.filter(type=op_type)
    if category_id:
        qs = qs.filter(category_id=category_id)
    if q:
        qs = qs.filter(Q(description__icontains=q) | Q(category__name__icontains=q))

    return qs


@login_required
def transaction_list_view(request):
    user = request.user
    transactions = _get_filtered_transactions(user, request.GET)

    # Filtrlangan natijalar uchun umumiy summa
    filtered_income = transactions.filter(
        type=Transaction.TYPE_INCOME
    ).aggregate(total=Sum('amount'))['total'] or decimal.Decimal('0.00')

    filtered_expense = transactions.filter(
        type=Transaction.TYPE_EXPENSE
    ).aggregate(total=Sum('amount'))['total'] or decimal.Decimal('0.00')

    filtered_net = filtered_income - filtered_expense

    # Sahifalash (Pagination)
    paginator = Paginator(transactions, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Foydalanuvchining kategoriyalari (filtr select uchun)
    user_categories = Category.objects.filter(user=user).order_by('type', 'name')

    # Filtr parametrlarini saqlab qolish
    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')
    querystring = query_params.urlencode()

    context = {
        'page_obj': page_obj,
        'transactions': page_obj,
        'filtered_income': filtered_income,
        'filtered_expense': filtered_expense,
        'filtered_net': filtered_net,
        'user_categories': user_categories,
        'querystring': querystring,
        'filter_start_date': request.GET.get('start_date', ''),
        'filter_end_date': request.GET.get('end_date', ''),
        'filter_type': request.GET.get('type', ''),
        'filter_category': request.GET.get('category', ''),
        'filter_q': request.GET.get('q', ''),
    }
    return render(request, 'wallet/transactions.html', context)


@login_required
def export_transactions_csv_view(request):
    user = request.user
    transactions = _get_filtered_transactions(user, request.GET).order_by('date', 'created_at')

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    today_str = timezone.localdate().strftime('%Y-%m-%d')
    response['Content-Disposition'] = f'attachment; filename="hamyonim_operatsiyalar_{today_str}.csv"'

    # UTF-8 BOM qo'shish (Excel dasturida kirill/lotin harflar to'g'ri chiqishi uchun)
    response.write('\ufeff')

    writer = csv.writer(response)
    writer.writerow(['№', 'Sana', 'Operatsiya turi', 'Kategoriya', 'Summa (so\'m)', 'Izoh'])

    for idx, tx in enumerate(transactions, start=1):
        cat_name = tx.category.name if tx.category else "Kategoriyasiz"
        writer.writerow([
            idx,
            tx.date.strftime('%d.%m.%Y'),
            tx.get_type_display(),
            cat_name,
            f"{tx.amount:.2f}",
            tx.description or "-"
        ])

    # Yakuniy hisob-kitoblar qatori
    total_income = transactions.filter(type=Transaction.TYPE_INCOME).aggregate(total=Sum('amount'))['total'] or decimal.Decimal('0.00')
    total_expense = transactions.filter(type=Transaction.TYPE_EXPENSE).aggregate(total=Sum('amount'))['total'] or decimal.Decimal('0.00')
    net_total = total_income - total_expense

    writer.writerow([])
    writer.writerow(['', '', '', 'JAMI DAROMAD:', f"{total_income:.2f}", 'so\'m'])
    writer.writerow(['', '', '', 'JAMI XARAJAT:', f"{total_expense:.2f}", 'so\'m'])
    writer.writerow(['', '', '', 'SOF QOLDIQ:', f"{net_total:.2f}", 'so\'m'])

    return response


@login_required
def transaction_create_view(request):
    user = request.user
    if request.method == 'POST':
        form = TransactionForm(request.POST, user=user)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = user
            transaction.save()
            messages.success(request, f"{transaction.get_type_display()} muvaffaqiyatli qo'shildi.")
            return redirect('transactions')
    else:
        # Default tur (agar url parametrida bo'lsa)
        initial_type = request.GET.get('type', Transaction.TYPE_EXPENSE)
        form = TransactionForm(user=user, initial={'type': initial_type})

    return render(request, 'wallet/transaction_form.html', {
        'form': form,
        'title': "Yangi operatsiya qo'shish",
        'btn_text': "Saqlash"
    })


@login_required
def transaction_update_view(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Operatsiya ma'lumotlari yangilandi.")
            return redirect('transactions')
    else:
        form = TransactionForm(instance=transaction, user=request.user)

    return render(request, 'wallet/transaction_form.html', {
        'form': form,
        'title': "Operatsiyani tahrirlash",
        'btn_text': "Yangilash",
        'is_edit': True,
        'transaction': transaction
    })


@login_required
def transaction_delete_view(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, "Operatsiya muvaffaqiyatli o'chirildi.")
        return redirect('transactions')
    return render(request, 'wallet/confirm_delete.html', {
        'object': transaction,
        'title': "Operatsiyani o'chirish",
        'message': f"Haqiqatan ham '{transaction}' operatsiyasini o'chirmoqchimisiz?",
        'cancel_url': 'transactions'
    })


# ==========================================
# CATEGORIES CRUD
# ==========================================

@login_required
def category_list_view(request):
    user = request.user
    income_categories = Category.objects.filter(user=user, type=Category.TYPE_INCOME)
    expense_categories = Category.objects.filter(user=user, type=Category.TYPE_EXPENSE)

    return render(request, 'wallet/categories.html', {
        'income_categories': income_categories,
        'expense_categories': expense_categories,
    })


@login_required
def category_create_view(request):
    user = request.user
    if request.method == 'POST':
        form = CategoryForm(request.POST, user=user)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = user
            category.save()
            messages.success(request, f"'{category.name}' kategoriyasi yaratildi.")
            return redirect('categories')
    else:
        cat_type = request.GET.get('type', Category.TYPE_EXPENSE)
        form = CategoryForm(user=user, initial={'type': cat_type})

    return render(request, 'wallet/category_form.html', {
        'form': form,
        'title': "Yangi kategoriya yaratish",
        'btn_text': "Yaratish"
    })


@login_required
def category_update_view(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"'{category.name}' kategoriyasi tahrirlandi.")
            return redirect('categories')
    else:
        form = CategoryForm(instance=category, user=request.user)

    return render(request, 'wallet/category_form.html', {
        'form': form,
        'title': "Kategoriyani tahrirlash",
        'btn_text': "Saqlash",
        'is_edit': True,
        'category': category
    })


@login_required
def category_delete_view(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f"'{name}' kategoriyasi o'chirildi.")
        return redirect('categories')
    return render(request, 'wallet/confirm_delete.html', {
        'object': category,
        'title': "Kategoriyani o'chirish",
        'message': f"Haqiqatan ham '{category.name}' kategoriyasini o'chirmoqchimisiz? (Unga biriktirilgan operatsiyalar saqlanib qoladi)",
        'cancel_url': 'categories'
    })


# ==========================================
# BUDGETS CRUD
# ==========================================

@login_required
def budget_list_view(request):
    user = request.user
    today = timezone.localdate()

    selected_year = int(request.GET.get('year', today.year))
    selected_month = int(request.GET.get('month', today.month))

    budgets = MonthlyBudget.objects.filter(
        user=user,
        year=selected_year,
        month=selected_month
    ).select_related('category')

    # Umumiy budjet va kategoriya budjetlari
    general_budget = budgets.filter(category__isnull=True).first()
    category_budgets = budgets.filter(category__isnull=False)

    # Shu oyning jami haqiqiy xarajatlari
    total_spent = Transaction.objects.filter(
        user=user,
        type=Transaction.TYPE_EXPENSE,
        date__year=selected_year,
        date__month=selected_month
    ).aggregate(total=Sum('amount'))['total'] or decimal.Decimal('0.00')

    context = {
        'selected_year': selected_year,
        'selected_month': selected_month,
        'selected_month_name': dict(UZBEK_MONTHS).get(selected_month, ''),
        'months': UZBEK_MONTHS,
        'years': range(today.year - 2, today.year + 3),
        'general_budget': general_budget,
        'category_budgets': category_budgets,
        'total_spent': total_spent,
    }
    return render(request, 'wallet/budgets.html', context)


@login_required
def budget_create_view(request):
    user = request.user
    today = timezone.localdate()
    if request.method == 'POST':
        form = MonthlyBudgetForm(request.POST, user=user)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = user
            budget.save()
            messages.success(request, "Budjet muvaffaqiyatli belgilandi.")
            return redirect(f"/budgets/?year={budget.year}&month={budget.month}")
    else:
        init_year = request.GET.get('year', today.year)
        init_month = request.GET.get('month', today.month)
        form = MonthlyBudgetForm(user=user, initial={'year': init_year, 'month': init_month})

    return render(request, 'wallet/budget_form.html', {
        'form': form,
        'title': "Oylik budjet belgilash",
        'btn_text': "Saqlash"
    })


@login_required
def budget_update_view(request, pk):
    budget = get_object_or_404(MonthlyBudget, pk=pk, user=request.user)
    if request.method == 'POST':
        form = MonthlyBudgetForm(request.POST, instance=budget, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Budjet muvaffaqiyatli yangilandi.")
            return redirect(f"/budgets/?year={budget.year}&month={budget.month}")
    else:
        form = MonthlyBudgetForm(instance=budget, user=request.user)

    return render(request, 'wallet/budget_form.html', {
        'form': form,
        'title': "Budjetni tahrirlash",
        'btn_text': "Yangilash",
        'is_edit': True,
        'budget': budget
    })


@login_required
def budget_delete_view(request, pk):
    budget = get_object_or_404(MonthlyBudget, pk=pk, user=request.user)
    year = budget.year
    month = budget.month
    if request.method == 'POST':
        budget.delete()
        messages.success(request, "Budjet o'chirildi.")
        return redirect(f"/budgets/?year={year}&month={month}")
    return render(request, 'wallet/confirm_delete.html', {
        'object': budget,
        'title': "Budjetni o'chirish",
        'message': f"Haqiqatan ham ushbu budjetni o'chirmoqchimisiz?",
        'cancel_url': 'budgets'
    })


# ==========================================
# API HELPER (Kategoriyalarni turlar bo'yicha olish)
# ==========================================

@login_required
def api_get_categories(request):
    """Tranzaksiya formasida operatsiya turi o'zgarganda kategoriyalarni dinamik yangilash uchun."""
    cat_type = request.GET.get('type')
    qs = Category.objects.filter(user=request.user)
    if cat_type in [Category.TYPE_INCOME, Category.TYPE_EXPENSE]:
        qs = qs.filter(type=cat_type)
    data = [{'id': c.id, 'name': c.name, 'icon': c.icon, 'color': c.color} for c in qs]
    return JsonResponse({'categories': data})
