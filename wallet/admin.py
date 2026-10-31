from django.contrib import admin
from .models import Category, Transaction, MonthlyBudget


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'user', 'color', 'icon', 'created_at')
    list_filter = ('type', 'user')
    search_fields = ('name', 'user__username')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'amount', 'category', 'date', 'created_at')
    list_filter = ('type', 'date', 'category', 'user')
    search_fields = ('description', 'user__username', 'category__name')
    date_hierarchy = 'date'


@admin.register(MonthlyBudget)
class MonthlyBudgetAdmin(admin.ModelAdmin):
    list_display = ('user', 'year', 'month', 'category', 'amount', 'created_at')
    list_filter = ('year', 'month', 'user')
    search_fields = ('user__username', 'category__name')
