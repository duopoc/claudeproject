"""
Accounts URL Configuration
"""
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # MFA
    path('mfa/verify/', views.mfa_verify_view, name='mfa_verify'),
    path('mfa/setup/', views.mfa_setup_view, name='mfa_setup'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
    
    # Admin Dashboard
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/user/<int:user_id>/manage/', views.user_management_view, name='user_management'),
    path('admin/user/<int:user_id>/delete/', views.user_delete_view, name='user_delete'),
    path('admin/user/create/', views.user_create_view, name='user_create'),
    
    # Password Reset
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         views.CustomPasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'),
         name='password_reset_complete'),
]
