from django.db import models
from cours.models import Course

class Chapter(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='chapters')
    title = models.CharField(max_length=200)
    description = models.TextField()
    video_url = models.URLField(blank=True, null=True)
    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.title} ({self.course.title})"
