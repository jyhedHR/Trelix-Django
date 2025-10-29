from django import forms
from .models import Participation

class ParticipationForm(forms.ModelForm):
    class Meta:
        model = Participation
        fields = ['role', 'niveau_etude', 'domaine_competence', 'experience_precedente', 'annee_experience']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
            'niveau_etude': forms.Select(attrs={'class': 'form-control'}),
            'domaine_competence': forms.Select(attrs={'class': 'form-control'}),
            'annee_experience': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }
        labels = {
            'role': 'Rôle dans l\'événement',
            'niveau_etude': 'Niveau d\'étude',
            'domaine_competence': 'Domaine de compétence',
            'experience_precedente': 'Expérience précédente dans ce domaine',
            'annee_experience': 'Années d\'expérience',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['experience_precedente'].widget.attrs.update({'class': 'form-check-input'})