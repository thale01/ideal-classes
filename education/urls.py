from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin-dashboard/manage-content/', views.manage_content, name='manage_content'),
    path('admin-dashboard/delete-content/<int:pk>/', views.delete_content, name='delete_content'),
    path('category/<int:pk>/', views.category_branches, name='category_branches'),
    path('category/<int:category_pk>/year/<int:year_pk>/', views.year_subjects, name='year_subjects'),
    path('category/<int:category_pk>/branch/<int:branch_pk>/', views.branch_subjects, name='branch_subjects'),
    path('subject/<int:pk>/', views.subject_detail, name='subject_detail'),
    path('search/', views.search, name='search'),
    path('admission/', views.admission_apply, name='admission_apply'),
    path('login-selection/', views.login_selection, name='login_selection'),
    path('student/login/', views.student_login, name='student_login'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/logout/', views.student_logout, name='student_logout'),
    path('admin-dashboard/admissions/', views.admin_admissions, name='admin_admissions'),
    path('admin-dashboard/status/<int:pk>/<str:status>/', views.update_admission_status, name='update_status'),
    path('content/<str:class_name>/', views.content_view, name='content_view'),
    path('contact-us/', views.contact_us, name='contact_us'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-of-use/', views.terms_of_use, name='terms_of_use'),
    path('curriculum/', views.curriculum, name='curriculum'),
    path('faculty/login/', views.faculty_login, name='faculty_login'),
    path('save-content/<int:pk>/', views.toggle_save_content, name='toggle_save_content'),
    path('my-saved-notes/', views.saved_notes_page, name='saved_notes'),
]
