from django.db import models

class Evenement(models.Model):
    TYPE_CHOICES = [
        ('hackathon', 'Hackathon'),
        ('workshop', 'Workshop'),
        ('webinaire', 'Webinaire'),
        ('conference', 'Conférence'),
        ('autre', 'Autre'),
    ]

    titre = models.CharField(max_length=100)
    description = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    date_debut = models.DateField()
    date_fin = models.DateField()
    lieu = models.CharField(max_length=100)
    image = models.ImageField(upload_to='evenements/', blank=True, null=True)
    capacite_max = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.titre} ({self.type})"
