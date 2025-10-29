from django.urls import path
from . import views

app_name = 'participation'

urlpatterns = [
    path('mes-participations/', views.mes_participations, name='mes_participations'),
    path('participer/<int:evenement_id>/', views.participer_evenement, name='participer_evenement'),
    path('annuler/<int:evenement_id>/', views.annuler_participation, name='annuler_participation'),
]