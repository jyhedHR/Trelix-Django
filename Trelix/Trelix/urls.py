from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),                  
    path('signup/', views.signup_view, name='signup'),  
    path('signin/', views.signin_view, name='signin'),  
    path('signout/', views.signout_view, name='signout'),
    path('courses/', views.courses_view, name='courses'),      
    path('exams/', views.exams_view, name='exams'),            
    path('profile/', views.profile_view, name='profile'),      
    path('course/<int:course_id>/', views.single_course_view, name='single-course'),
]

urlpatterns += [
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
