from django.urls import path, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views

app_name = 'accounts'

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('signin/', views.signin_view, name='signin'),
    path('signout/', views.signout_view, name='signout'),
    path('profile/', views.profile_view, name='profile'),
    path('verify-2fa/', views.verify_2fa_view, name='verify_2fa'),
    path('setup-2fa/', views.setup_2fa_view, name='setup_2fa'),
    path('show-qr-code/', views.show_qr_code, name='show_qr_code'),
    path('google/login/', views.google_login, name='google_login'),
    path('google/login/callback/', views.google_callback, name='google_callback'),
    path('google/role-selection/', views.google_role_selection, name='google_role_selection'),
    path('google/create-account/', views.google_create_account, name='google_create_account'),
    path('profile-completion/', views.profile_completion, name='profile_completion'),
    path('toggle-2fa/', views.toggle_2fa, name='toggle_2fa'),
    path('disable-2fa/', views.disable_2fa_view, name='disable_2fa'),
    path('get-backup-codes/', views.get_backup_codes, name='get_backup_codes'),
    path('reset-backup-codes/', views.reset_backup_codes_view, name='reset_backup_codes'),
    path('download-backup-codes/', views.download_backup_codes_view, name='download_backup_codes'),
    path('set-password/', views.set_password, name='set_password'),
    path('delete-trusted-device/<int:device_id>/', views.delete_trusted_device_view, name='delete_trusted_device'),
]

urlpatterns += [
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html',
        email_template_name='accounts/password_reset_email.txt',
        html_email_template_name='accounts/password_reset_email.html',
        subject_template_name='accounts/password_reset_subject.txt',
        success_url=reverse_lazy('accounts:password_reset_done')
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url=reverse_lazy('accounts:password_reset_complete')
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),
]