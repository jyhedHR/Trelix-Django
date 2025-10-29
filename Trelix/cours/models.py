from django.db import models
from django.core.exceptions import ValidationError
import re
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField

class Course(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    title = models.CharField(
        max_length=255,
        help_text="At least 5 characters. Don't start with a symbol or a number."
    )
    description = models.TextField(
        blank=True,
        help_text="At least 10 characters. Don't start with a symbol or a number."
    )
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    is_published = models.BooleanField(default=False)
    image = CloudinaryField('image', blank=True, null=True)  

    def __str__(self):
        return self.title

    def clean(self):
        # Title : min 5 caractères, ne pas commencer par chiffre ou symbole
        if len(self.title) < 5:
            raise ValidationError({'title': 'Title must have at least 5 characters.'})
        if re.match(r'^[^A-Za-z]', self.title):
            raise ValidationError({'title': "Title can't start with a number or a symbol."})

        # Description : min 10 caractères, ne pas commencer par chiffre ou symbole
        if self.description:
            if len(self.description) < 10:
                raise ValidationError({'description': 'La description doit avoir au moins 10 caractères.'})
            if re.match(r'^[^A-Za-z]', self.description):
                raise ValidationError({'description': 'La description ne peut pas commencer par un chiffre ou un symbole.'})
class ChapterQuizScore(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    chapter = models.ForeignKey("chapitre.Chapter", on_delete=models.CASCADE)  # <- string reference
    score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.chapter} - {self.score}"