from django.contrib import admin
from .models import Participation

@admin.register(Participation)
class ParticipationAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'evenement', 'role', 'niveau_etude', 'date_participation']
    list_filter = ['role', 'niveau_etude', 'domaine_competence', 'date_participation']
    search_fields = ['utilisateur__username', 'evenement__titre']
    readonly_fields = ['date_participation']