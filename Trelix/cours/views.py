from django.shortcuts import render, get_object_or_404
from .models import Course
from chapitre.models import Chapter

def course_list(request):
    courses = Course.objects.filter(is_published=True)
    return render(request, 'Trelix/courses.html', {'courses': courses})
def course_detail(request, course_id):
    course = get_object_or_404(Course, pk=course_id, is_published=True)
    chapters = course.chapters.all().order_by('order')  # récupérer les chapitres liés
    selected_chapter = chapters.first() if chapters.exists() else None

    context = {
        'course': course,
        'chapters': chapters,
        'selected_chapter': selected_chapter
    }
    return render(request, 'Trelix/chapters.html', context)