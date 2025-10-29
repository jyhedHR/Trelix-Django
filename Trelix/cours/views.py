from django.shortcuts import render, get_object_or_404
from .models import Course, ChapterQuizScore
from chapitre.models import Chapter
from django.http import JsonResponse
from huggingface_hub import InferenceClient
from django.contrib.auth.decorators import login_required
from django.conf import settings

import json

def course_list(request):
    courses = Course.objects.filter(is_published=True)
    return render(request, 'Trelix/courses.html', {'courses': courses})

import json

def course_detail(request, course_id):
    course = get_object_or_404(Course, pk=course_id, is_published=True)
    chapters = course.chapters.all().order_by('order')
    selected_chapter = chapters.first() if chapters.exists() else None

    user_scores = ChapterQuizScore.objects.filter(
        user=request.user,
        chapter__in=chapters
    ).values_list('chapter_id', 'score')
    user_scores_dict = {chapter_id: score for chapter_id, score in user_scores}

    return render(request, 'Trelix/chapters.html', {
        'course': course,
        'chapters': chapters,
        'selected_chapter': selected_chapter,
        'user_scores_json': json.dumps(user_scores_dict),  # sérialisé pour JS
    })



# Génération du quiz avec JSON structuré
@login_required
def generate_quiz(request, chapter_id):
    chapter = get_object_or_404(Chapter, pk=chapter_id)
    content = chapter.description or ""

    client = InferenceClient(token=settings.HF_API_TOKEN)
    prompt = f"""
Create a short quiz (3 questions) in English based on the following text:
---
{content}
---
Each question should have 3 options (A, B, C) and indicate which one is correct.
Format it strictly as JSON, like this:
[
  {{
    "question": "...",
    "options": ["A", "B", "C"],
    "answer": "A"
  }},
  ...
]
Do not include any extra text or explanation outside the JSON array.
"""

    completion = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-V3-0324",
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = completion.choices[0].message["content"]

    # Forcer JSON correct et transformer options
    try:
        # Supprimer les ```json ... ``` si présent
        clean_text = raw_text.strip().strip("```").replace("json", "").strip()
        quiz_json = json.loads(clean_text)
        for q in quiz_json:
            q['options'] = [{"label": opt, "value": opt} for opt in q.get('options', [])]
    except json.JSONDecodeError:
        print("HuggingFace returned invalid JSON")
        print("Raw text:", raw_text)
        quiz_json = []

    return JsonResponse({"quiz": quiz_json})

# Stocker le score
@login_required
def submit_quiz_score(request):
    if request.method == "POST":
        data = json.loads(request.body)
        chapter_id = data.get("chapter_id")
        score = data.get("score")

        chapter = get_object_or_404(Chapter, pk=chapter_id)
        ChapterQuizScore.objects.create(user=request.user, chapter=chapter, score=score)
        return JsonResponse({"status": "ok"})
    return JsonResponse({"status": "error"}, status=400)