from django.contrib import admin
from .models import Course

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'level', 'is_published', 'duration')
    list_filter = ('level', 'is_published')
    search_fields = ('title', 'description')
