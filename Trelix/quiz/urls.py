from django.urls import path
from . import views

urlpatterns = [
    path("", views.quiz_list, name="quiz_list"),
    path("<int:quiz_id>/", views.quiz_detail, name="quiz_detail"),
    path("badges/", views.my_badges, name="my_badges"),
]
