from django.urls import path
from . import views

urlpatterns = [
    # ... your existing URLs (keep these) ...
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
    path('delete-registration/<int:admission_id>/', views.delete_registration, name='delete_registration'),
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
    path('api/search-students/', views.search_students, name='search_students'),
    path('api/get-student-details/<int:student_id>/', views.get_student_details_by_id, name='get_student_details_by_id'),
    path('api/get-complete-admission-details/<int:student_id>/', views.get_complete_admission_details, name='get_complete_admission_details'),
    
    # Organization Settings
    path('organization-settings/', views.organization_settings, name='organization_settings'),
    
    # View Registrations
    path('view-registrations/', views.view_registrations, name='view_registrations'),
    path('toggle-admit/<int:admission_id>/', views.toggle_admit, name='toggle_admit'),
    
    # EXAM MANAGEMENT URLS - SIMPLIFIED VERSION
    path('exam-dashboard/', views.exam_dashboard, name='exam_dashboard'),
    path('exams/', views.exam_list, name='exam_list'),
    path('exams/add/', views.add_exam, name='add_exam'),
    path('exams/edit/<int:exam_id>/', views.edit_exam, name='edit_exam'),
    path('exams/delete/<int:exam_id>/', views.delete_exam, name='delete_exam'),
    path('results/entry/<int:exam_id>/', views.result_entry, name='result_entry'),
    path('results/<int:exam_id>/', views.result_list, name='result_list'),
    path('report-card/', views.report_card, name='report_card'),
    path('report-card/<int:exam_id>/<int:student_id>/', views.view_report_card, name='view_report_card'),
    path('api/get-exam-stats/<int:exam_id>/', views.api_get_exam_stats, name='api_get_exam_stats'),
    
    # path('results/edit/<int:exam_id>/<int:student_id>/', views.edit_student_result, name='edit_student_result'),
    # path('results/update/<int:exam_id>/<int:student_id>/', views.update_student_result, name='update_student_result'),
    path('results/bulk-update/<int:exam_id>/', views.bulk_update_results, name='bulk_update_results'),
]