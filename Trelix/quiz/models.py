from django.db import models
from django.contrib.auth.models import User
from django.core.files import File
from cloudinary.models import CloudinaryField
from .utils import generate_badge_image
from django.utils.text import slugify
import os


class Badge(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True, null=True)  # ✅ null=True pour éviter les erreurs migration
    description = models.TextField(blank=True)  # ✅ Gardé comme tu veux
    icon = CloudinaryField(max_length=255, verbose_name='image', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        if not self.description:
            self.description = f"Badge obtenu : {self.name}"

        super().save(*args, **kwargs)

        # ✅ Génération automatique de l'image si absente
        if not self.icon:
            from django.conf import settings
            image_path = generate_badge_image(self.name)
            full_path = os.path.join(settings.MEDIA_ROOT, image_path)
            if os.path.exists(full_path):
                with open(full_path, 'rb') as f:
                    self.icon.save(os.path.basename(image_path), File(f), save=False)
                super().save(update_fields=["icon"])
            
class Quiz(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    pass_mark = models.PositiveIntegerField(default=70)

    def __str__(self):
        return self.title


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, related_name="questions", on_delete=models.CASCADE)
    text = models.TextField()
    points = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.text


class Choice(models.Model):
    question = models.ForeignKey(Question, related_name="choices", on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

class UserBadge(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    badge = models.ForeignKey('Badge', on_delete=models.CASCADE)
    quiz = models.ForeignKey('Quiz', on_delete=models.CASCADE)
    score = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)  # ✅ Correction ici ✅
