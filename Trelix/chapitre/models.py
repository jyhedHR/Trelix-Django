from django.db import models
from cours.models import Course
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
import re

def validate_text_start(value, min_length, field_name):
    """Validator pour title et description"""
    if len(value) < min_length:
        raise ValidationError(f"{field_name} must have at least {min_length} characters.")
    if re.match(r'^[^A-Za-z]', value):
        raise ValidationError(f"{field_name} can't start with a symbol or a number.")

class Chapter(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(
        max_length=200,
        help_text="At least  5 characters. Can't start with a symbol or a number."
    )
    description = models.TextField(
        help_text="At least 10 characters. Can't start with a symbol or a number."
    )
    video = models.FileField(
        upload_to='chapters/videos/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['mp4','mov','avi'])],
        help_text="Upload a video (mp4, mov, avi)"
    )
    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.title} ({self.course.title})"

    def clean(self):
        validate_text_start(self.title, 5, "Title")
        if self.description:
            validate_text_start(self.description, 10, "Description")
