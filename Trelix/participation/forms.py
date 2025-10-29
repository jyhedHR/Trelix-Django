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
            'role': 'Role in the event',
            'niveau_etude': 'study_level',
            'domaine_competence': 'area_of_competence',
            'experience_precedente': 'previous_experience',
            'annee_experience': 'year_of_experience',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['experience_precedente'].widget.attrs.update({'class': 'form-check-input'})