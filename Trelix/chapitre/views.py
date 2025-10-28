from django.shortcuts import render
from .models import Chapter

def chapters_page(request):
    chapters = Chapter.objects.all().order_by('order')  # tu peux filtrer plus tard si besoin
    return render(request, 'Trelix/chapters.html', {
        'chapters': chapters
    })
