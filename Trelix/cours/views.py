from django.shortcuts import render, get_object_or_404
from .models import Course, ChapterQuizScore
from chapitre.models import Chapter
from django.http import JsonResponse
from huggingface_hub import InferenceClient
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import requests
import json
from xhtml2pdf import pisa
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from .utils import GeminiFlashcardGenerator, get_course_content_for_flashcards


def course_list(request):
    courses = Course.objects.filter(is_published=True)
    return render(request, 'Trelix/courses.html', {'courses': courses})

@csrf_exempt
@require_POST
def filter_courses(request):
    """
    Filtre les cours par niveau via POST JSON
    """
    try:
        body = json.loads(request.body)
        levels = body.get("levels", [])
    except json.JSONDecodeError:
        levels = []

    if not levels or "all" in levels:
        courses = Course.objects.filter(is_published=True)
    else:
        courses = Course.objects.filter(level__in=levels, is_published=True)

    data = [
        {
            "id": c.id,
            "title": c.title,
            "description": c.description[:120] + "..." if len(c.description) > 120 else c.description,
            "level": c.level.title(),
            "image": c.image.url if c.image else "",
        }
        for c in courses
    ]
    return JsonResponse({"courses": data})

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
def chunk_text(text, max_chars=2000):
    """
    Divise le texte en chunks < max_chars pour éviter de dépasser la limite API.
    """
    chunks = []
    while len(text) > max_chars:
        split_at = text.rfind("\n\n", 0, max_chars)
        if split_at == -1:
            split_at = max_chars
        chunks.append(text[:split_at].strip())
        text = text[split_at:].strip()
    if text:
        chunks.append(text)
    return chunks

@csrf_exempt
def summarize_course(request, course_id):
    try:
        course = Course.objects.get(id=course_id)
        chapters = Chapter.objects.filter(course=course).order_by('id')

        full_text = "\n\n".join([chapter.description for chapter in chapters if chapter.description])
        if not full_text:
            return JsonResponse({"error": "No chapter descriptions to summarize."}, status=400)

        url = f"https://api.nlpcloud.io/v1/{settings.NLP_CLOUD_MODEL}/summarization"
        headers = {
            "Authorization": f"Token {settings.NLP_CLOUD_API_KEY}",
            "Content-Type": "application/json"
        }

        # Découper le texte en chunks pour éviter le 413
        chunks = chunk_text(full_text, max_chars=2000)
        summaries = []

        for i, chunk in enumerate(chunks, start=1):
            payload = {"text": chunk, "min_length": 50, "max_length": 300}
            response = requests.post(url, headers=headers, data=json.dumps(payload))

            # Debug pour voir les réponses
            print(f"Chunk {i}/{len(chunks)} - Status:", response.status_code)
            print("Response text:", response.text)

            if response.status_code == 200:
                try:
                    data = response.json()
                    summaries.append(data.get("summary_text", ""))
                except json.JSONDecodeError:
                    summaries.append("[Error decoding chunk summary]")
            else:
                summaries.append(f"[Error: API returned status {response.status_code}]")

        final_summary = "\n\n".join([s for s in summaries if s])
        return JsonResponse({"summary": final_summary})

    except Course.DoesNotExist:
        return JsonResponse({"error": "Course not found."}, status=404)
    except Exception as e:
        print("Exception in summarize_course:", e)
        return JsonResponse({"error": str(e)}, status=500)
@login_required
def download_summary_pdf(request, course_id):
    course = Course.objects.get(id=course_id)
    chapters = Chapter.objects.filter(course=course).order_by('id')
    full_text = "\n\n".join([c.description for c in chapters if c.description])

    html_string = render_to_string('Trelix/summary_pdf.html', {
        'course': course,
        'summary': full_text.replace("\n", "<br>")
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="course_{course.id}_summary.pdf"'
    pisa_status = pisa.CreatePDF(html_string, dest=response)
    if pisa_status.err:
        return HttpResponse("Error generating PDF", status=500)
    return response


@login_required
@csrf_exempt
def generate_flashcards(request, course_id):
    try:
        # Get course and validate access
        course = get_object_or_404(Course, pk=course_id, is_published=True)
        
        # Get parameters from request (optional, default 10 cards)
        num_cards = 10
        model_name = None
        if request.method == 'POST':
            try:
                body = json.loads(request.body)
                num_cards = int(body.get('num_cards', 10))
                # Limit to reasonable range
                num_cards = max(5, min(num_cards, 50))
                model_name = body.get('model_name')
            except (json.JSONDecodeError, ValueError, TypeError):
                pass  # Use defaults
        
        # Get and structure course content
        course_content = get_course_content_for_flashcards(course)
        
        if not course_content or len(course_content.strip()) < 50:
            return JsonResponse({
                "error": "Course content is too short to generate meaningful flashcards. Please ensure the course has chapters with descriptions."
            }, status=400)
        
        # Initialize flashcard generator
        generator = GeminiFlashcardGenerator(model_name=model_name)
        
        # Generate flashcards
        flashcards = generator.generate_flashcards(course_content, num_cards=num_cards)
        
        return JsonResponse({
            "flashcards": flashcards,
            "course_title": course.title,
            "count": len(flashcards)
        })
        
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        import traceback
        print(f"Error generating flashcards: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            "error": f"Failed to generate flashcards: {str(e)}"
        }, status=500)