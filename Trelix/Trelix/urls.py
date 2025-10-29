from django.contrib import admin
from django.urls import path
from examan.models import Exam 
from examan import views as exam_views 
from django.contrib.auth import views as auth_views
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),                  
    path('signup/', views.signup_view, name='signup'),  
    path('signin/', views.signin_view, name='signin'),  
    path('signout/', views.signout_view, name='signout'),
    path('courses/', views.courses_view, name='courses'),                
    path('profile/', views.profile_view, name='profile'),      
    path('course/<int:course_id>/', views.single_course_view, name='single-course'),
]

urlpatterns += [
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    # trelix/urls.py
    path('exam/<int:exam_id>/', exam_views.single_exam_view, name='exam-detail'), 
    path('exams/', exam_views.exams_view, name='exams'),
path('exam/<int:exam_id>/submit/', exam_views.submit_exam_view, name='submit_exam'),
# examapp/urls.py
path('exam/<int:exam_id>/submitted/', exam_views.exam_submitted_view, name='exam_submitted'),
path('exam/result/<int:student_exam_id>/', exam_views.exam_result_view, name='exam-result'),
 path('meeting/', views.jitsi_meeting, name='jitsi_meeting'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
