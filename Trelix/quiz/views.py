from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files import File
from django.conf import settings
from cloudinary import uploader
from io import BytesIO
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

            # ✅ Génération automatique de l'icône si elle n'existe pas ou si badge vient d'être créé
            # Regenerate if badge was just created OR if icon doesn't exist
            if created:
                print(f"🆕 New badge created: {badge_name}")
            elif not badge.icon:
                print(f"🔄 Badge exists but has no icon: {badge_name}")
            else:
                print(f"ℹ️ Badge already has icon (will not regenerate): {badge_name}")
                
            if created or not badge.icon:
                print(f"🎨 Generating image for badge: {badge_name}")
                pil_image, is_fallback = generate_badge_image(badge_name)
                
                if is_fallback:
                    print(f"⚠️ Generated image is fallback (blue) - API likely failed. Not saving to avoid overwriting.")
                    print(f"⚠️ Will retry on next badge creation. Check STABILITY_API_KEY and API status.")
                    # Don't save fallback images - leave icon empty so it retries next time
                else:
                    # Image is valid (not fallback), upload directly from memory to Cloudinary
                    try:
                        # Convert PIL Image to BytesIO for upload
                        img_buffer = BytesIO()
                        pil_image.save(img_buffer, format='PNG')
                        img_buffer.seek(0)
                        
                        # Upload to Cloudinary from memory
                        upload_result = uploader.upload(
                            img_buffer,
                            folder="badges",
                            resource_type="image",
                            format="png"
                        )
                        
                        if upload_result and 'public_id' in upload_result:
                            badge.icon = upload_result['public_id']
                            # Use update_fields to avoid triggering save() recursively
                            badge.save(update_fields=['icon'])
                            print(f"✅ Badge icon uploaded to Cloudinary: {upload_result['public_id']}")
                        else:
                            print(f"⚠️ Upload result incomplete: {upload_result}")
                    except Exception as e:
                        print(f"❌ Cloudinary upload error: {str(e)}")
                        # If upload fails, try the File.save method as fallback
                        try:
                            if badge.pk:
                                img_buffer = BytesIO()
                                pil_image.save(img_buffer, format='PNG')
                                img_buffer.seek(0)
                                badge.icon.save(f"{badge_name.replace(' ', '_').lower()}.png", File(img_buffer), save=False)
                                badge.save(update_fields=['icon'])
                                print(f"✅ Badge icon saved via fallback method")
                        except Exception as e2:
                            print(f"❌ Fallback save also failed: {str(e2)}")

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
