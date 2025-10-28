from django.urls import path
from . import views

urlpatterns = [
    path('', views.chapters_page, name='chapters-page'), 
]
