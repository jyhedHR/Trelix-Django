from django.db import models

class Course(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    is_published = models.BooleanField(default=False)
    duration = models.PositiveIntegerField(help_text="Estimated total duration in minutes", default=0)

    def __str__(self):
        return self.title
