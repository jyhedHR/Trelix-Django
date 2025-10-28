from django.db import models
from django.contrib.auth.models import User
from evenement.models import Evenement

class Participation(models.Model):
    ROLE_CHOICES = [
        ('participant', 'Participant'),
        ('organisateur', 'Organisateur'),
        ('mentor', 'Mentor'),
        ('jury', 'Jury'),
    ]
    
    NIVEAU_ETUDE_CHOICES = [
        ('lyceen', 'Lycéen'),
        ('etudiant', 'Étudiant'),
        ('ingenieur', 'Ingénieur'),
        ('professionnel', 'Professionnel'),
    ]
    
    DOMAINE_COMPETENCE_CHOICES = [
        ('developpement_web', 'Développement web'),
        ('data_science', 'Data Science'),
        ('design', 'Design'),
        ('cybersecurite', 'Cybersécurité'),
        ('ia', 'IA'),
    ]
    
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    evenement = models.ForeignKey(Evenement, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='participant')
    niveau_etude = models.CharField(max_length=20, choices=NIVEAU_ETUDE_CHOICES)
    domaine_competence = models.CharField(max_length=30, choices=DOMAINE_COMPETENCE_CHOICES)
    experience_precedente = models.BooleanField(default=False)
    annee_experience = models.PositiveIntegerField(default=0)
    date_participation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['utilisateur', 'evenement']
        verbose_name = "Participation"
        verbose_name_plural = "Participations"
    
    def __str__(self):
        return f"{self.utilisateur.username} - {self.evenement.titre}"