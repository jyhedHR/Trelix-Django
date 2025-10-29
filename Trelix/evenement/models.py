from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import re

def validate_letters_only(value):
    """Valide que le champ ne contient que des lettres, espaces et certains caractères de ponctuation"""
    if not re.match(r'^[A-Za-zÀ-ÿ\s\-,.!?]+$', value):
        raise ValidationError("Ce champ ne doit contenir que des lettres, espaces et caractères de ponctuation basiques.")
    
def validate_start_with_letter(value):
    """Valide que le champ commence par une lettre"""
    if value and not value[0].isalpha():
        raise ValidationError("Le champ doit commencer par une lettre.")

class Evenement(models.Model):
    TYPE_CHOICES = [
        ('hackathon', 'Hackathon'),
        ('workshop', 'Workshop'),
        ('webinaire', 'Webinaire'),
        ('conference', 'Conférence'),
        ('autre', 'Autre'),
    ]

    titre = models.CharField(
        max_length=40,
        validators=[validate_letters_only, validate_start_with_letter],
        help_text="Au moins 5 caractères. Ne doit pas commencer par un symbole ou un chiffre. Lettres uniquement."
    )
    description = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    date_debut = models.DateTimeField(default=timezone.now)
    date_fin = models.DateTimeField()
    lieu = models.CharField(max_length=100)
    image = models.ImageField(upload_to='images/', blank=True, null=True)

    capacite_max = models.PositiveIntegerField()

    def clean(self):
        """Validation supplémentaire pour la longueur minimale"""
        super().clean()
        
        if len(self.titre.strip()) < 5:
            raise ValidationError({'titre': "Le titre doit contenir au moins 5 caractères."})
            
        if len(self.description.strip()) < 5:
            raise ValidationError({'description': "La description doit contenir au moins 5 caractères."})

    def __str__(self):
        return f"{self.titre} ({self.type})"