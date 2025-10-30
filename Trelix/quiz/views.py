from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files import File
from django.conf import settings
from cloudinary import uploader
from .models import Quiz, Choice, UserBadge, Badge
from .utils.badge_image import generate_badge_image
import os

@login_required(login_url='signin')
def quiz_list(request):
    quizzes = Quiz.objects.filter(is_active=True)
    return render(request, "quiz/quiz_list.html", {"quizzes": quizzes})


@login_required(login_url='signin')
def quiz_detail(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)

    if request.method == "POST":
        questions = quiz.questions.all()
        total = sum(q.points for q in questions)
        points = 0

        for q in questions:
            choice_id = request.POST.get(f"question_{q.id}")
            if choice_id:
                try:
                    choice = Choice.objects.get(id=choice_id)
                    if choice.is_correct:
                        points += q.points
                except Choice.DoesNotExist:
                    pass

        score = round((points / total) * 100, 2)
        passed = score >= quiz.pass_mark
        badge = None

        if passed:
            # Attribution selon score
            if score >= 90:
                badge_name = "Gold Badge"
            elif score >= 70:
                badge_name = "Silver Badge"
            else:
                badge_name = "Bronze Badge"

            badge, created = Badge.objects.get_or_create(name=badge_name)

            # ✅ Génération automatique de l'icône si elle n'existe pas
            if not badge.icon:
                image_path = generate_badge_image(badge_name)
                full_path = os.path.join(settings.MEDIA_ROOT, image_path)
                if os.path.exists(full_path):
                    try:
                        # Upload to Cloudinary using uploader - use file path directly
                        upload_result = uploader.upload(full_path, folder="badges", resource_type="image")
                        if upload_result and 'public_id' in upload_result:
                            badge.icon = upload_result['public_id']
                            badge.save()
                    except Exception:
                        # If upload fails, try the File.save method as fallback
                        try:
                            # Ensure badge is saved first (it should be from get_or_create)
                            if badge.pk:
                                with open(full_path, 'rb') as f:
                                    badge.icon.save(os.path.basename(image_path), File(f), save=False)
                                badge.save()
                        except Exception:
                            pass  # Silently fail if both methods fail

            UserBadge.objects.get_or_create(
                user=request.user,
                badge=badge,
                quiz=quiz,
                defaults={'score': score}
            )
            messages.success(request, f"🎉 Tu as gagné un nouveau badge : {badge.name}")

        return render(request, "quiz/quiz_result.html",
                      {"quiz": quiz, "score": score, "passed": passed, "badge": badge})

    return render(request, "quiz/quiz_detail.html", {"quiz": quiz})


@login_required(login_url='signin')
def my_badges(request):
    badges = UserBadge.objects.filter(user=request.user).select_related("badge", "quiz")
    return render(request, "quiz/my_badges.html", {"badges": badges})
