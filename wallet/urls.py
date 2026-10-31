from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard
    path('', views.dashboard_view, name='dashboard'),

    # Transactions
    path('transactions/', views.transaction_list_view, name='transactions'),
    path('transactions/create/', views.transaction_create_view, name='transaction_create'),
    path('transactions/<int:pk>/update/', views.transaction_update_view, name='transaction_update'),
    path('transactions/<int:pk>/delete/', views.transaction_delete_view, name='transaction_delete'),
    path('transactions/export-csv/', views.export_transactions_csv_view, name='export_csv'),

    # Categories
    path('categories/', views.category_list_view, name='categories'),
    path('categories/create/', views.category_create_view, name='category_create'),
    path('categories/<int:pk>/update/', views.category_update_view, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete_view, name='category_delete'),

    # Budgets
    path('budgets/', views.budget_list_view, name='budgets'),
    path('budgets/create/', views.budget_create_view, name='budget_create'),
    path('budgets/<int:pk>/update/', views.budget_update_view, name='budget_update'),
    path('budgets/<int:pk>/delete/', views.budget_delete_view, name='budget_delete'),

    # API
    path('api/categories/', views.api_get_categories, name='api_categories'),
]
