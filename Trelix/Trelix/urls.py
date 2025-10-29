from django.contrib import admin
from examan.models import Exam 
from examan import views as exam_views 
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),  # Root - home page
    path('accounts/', include('accounts.urls')),  # Accounts URLs
    path('courses/', include('cours.urls')),      
    path('exams/', views.exams_view, name='exams'),            
    path('course/<int:course_id>/', views.single_course_view, name='single-course'),
    path('chapters/', include('chapitre.urls')),
    path('evenements/', include('evenement.urls')),  
   path("quiz/", include("quiz.urls")),

    path('participation/', include('participation.urls')),
]

urlpatterns += [
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
