from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Quiz, Choice, UserBadge, Badge
from .utils.badge_image import generate_badge_image

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
                badge.icon.name = image_path
                badge.save()

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
