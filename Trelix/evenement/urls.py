from django.urls import path
from . import views

app_name = 'evenement'

urlpatterns = [
path('', views.liste_evenements, name='liste_evenements'),
path('<int:evenement_id>/', views.detail_evenement, name='detail_evenement'),
path('generate-description/', views.generate_description, name='generate_description'),
path('test-models/', views.test_models, name='test_models'),
path('generate-image/', views.generate_image, name='generate_image'),


]