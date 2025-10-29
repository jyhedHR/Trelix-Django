from django.shortcuts import render, redirect ,get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm
import os
import random
import string
from evenement.models import Evenement  # ✅ Import ajouté
from quiz.models import Quiz, Choice, UserBadge
from django.contrib import messages


@login_required(login_url='signin')
def home(request):
    return render(request, "trelix/index.html")

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'trelix/signup.html', {'form': form})

def signin_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'trelix/signin.html', {'form': form})

@login_required(login_url='signin')
def signout_view(request):
    logout(request)
    return redirect('signin')

def courses_view(request):
    # Add logic to display and retrieve list of courses
    return render(request, 'trelix/courses.html')

def exams_view(request):
    # Add logic to display and retrieve list of exams
    return render(request, 'trelix/exams.html')

@login_required(login_url='signin')
def profile_view(request):
    # If you have an extended profile model, fetch it here; otherwise set to None
    user_profile = None
    if hasattr(request.user, 'profile'):
        user_profile = request.user.profile
    return render(request, 'trelix/profile.html', {'user_profile': user_profile})


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
        return redirect('signin')

