from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register_user, name='register'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('edit-user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('admission-form/', views.admission_form, name='admission_form'),
    path('search-admission/', views.search_admission, name='search_admission'),
    path('admissions-list/', views.admissions_list, name='admissions_list'),
    # Account Management URLs
    path('account-section/', views.account_section, name='account_section'),
    path('student-account/<int:admission_id>/', views.student_account, name='student_account'),
    path('account-search/', views.account_search_view, name='account_search'),
    path('add-expense/<int:admission_id>/', views.add_expense, name='add_expense'),
    path('add-expense/', views.add_expense_general, name='add_expense_general'),
    path('add-payment/<int:admission_id>/', views.add_payment, name='add_payment'),
    path('add-payment/', views.add_payment_general, name='add_payment_general'),
    path('edit-expense/<int:expense_id>/', views.edit_expense, name='edit_expense'),
    path('edit-payment/<int:payment_id>/', views.edit_payment, name='edit_payment'),
    path('delete-expense/<int:expense_id>/', views.delete_expense, name='delete_expense'),
    path('delete-payment/<int:payment_id>/', views.delete_payment, name='delete_payment'),
    path('generate-receipt/<int:payment_id>/', views.generate_receipt, name='generate_receipt'),
    path('account-report/<int:admission_id>/', views.account_report, name='account_report'),
    # API endpoints
    path('api/get-student-details/', views.get_student_details, name='get_student_details'),
    # Organization Settings URL
    path('organization-settings/', views.organization_settings, name='organization_settings'),
    path('api/search-students/', views.search_students, name='search_students'),
    path('api/get-student-details/<int:student_id>/', views.get_student_details_by_id, name='get_student_details_by_id'),
    # Add this to urls.py
    path('view-registrations/', views.view_registrations, name='view_registrations'),
    # Add to urls.py
    path('api/get-complete-admission-details/<int:student_id>/', views.get_complete_admission_details, name='get_complete_admission_details'),
    path('create-installments/', views.create_installments, name='create_installments'),
]