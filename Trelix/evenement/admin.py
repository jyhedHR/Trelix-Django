from django.contrib import admin
from .models import Evenement

@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    list_display = ['titre', 'type', 'date_debut', 'date_fin', 'lieu', 'capacite_max', 'nombre_participants']
    list_filter = ['type', 'date_debut', 'date_fin']
    search_fields = ['titre', 'description', 'lieu']
    
    def nombre_participants(self, obj):
        return obj.participation_set.count()
    nombre_participants.short_description = 'Participants'