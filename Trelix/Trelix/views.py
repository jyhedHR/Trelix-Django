from django.shortcuts import render, redirect ,get_object_or_404
from evenement.models import Evenement
from django.contrib.auth.decorators import login_required
import random
import string


def home(request):
    """Home page - redirect to signin if not authenticated"""
    if request.user.is_authenticated:
        return render(request, 'trelix/index.html')
    else:
        return redirect('accounts:signin')


def courses_view(request):
    # Add logic to display and retrieve list of courses
    return render(request, 'trelix/courses.html')

def exams_view(request):
    # Add logic to display and retrieve list of exams
    return render(request, 'trelix/exams.html')


def single_course_view(request, course_id):
    # Add logic to display single course detail
    return render(request, 'trelix/single_course.html', {'course_id': course_id})


@login_required
def jitsi_meeting(request):
    # Generate a random room name or get from request
    room_name = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    return render(request, 'trelix/meeting.html', {'room_name': room_name})
def evenement(request):
    if request.user.is_authenticated:
        evenements = Evenement.objects.all().order_by('-date_debut')
        return render(request, 'trelix/evenement.html', {'evenements': evenements})
    else:
        return redirect('accounts:signin')

