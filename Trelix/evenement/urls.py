from django.urls import path
from . import views

app_name = 'evenement'

urlpatterns = [
path('', views.liste_evenements, name='liste_evenements'),
path('<int:evenement_id>/', views.detail_evenement, name='detail_evenement'),
]