from django.urls import path
from . import views

urlpatterns = [
    path('', views.course_list, name='courses'),
    path('<int:course_id>/', views.course_detail, name='course-detail'),
    path('quiz/<int:chapter_id>/', views.generate_quiz, name='generate-quiz'),
    path('quiz/score/', views.submit_quiz_score, name='submit_quiz_score'),
]