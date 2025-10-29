from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from .models import Evenement
from django.http import JsonResponse,HttpResponse
from django.views.decorators.csrf import csrf_exempt
import google.generativeai as genai
import json
import os
import io
import requests
from PIL import Image
from django.core.files import File
from django.http import HttpResponse





def imageGen(payload):
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Hugging Face API Error: {response.status_code}, {response.text}")


@csrf_exempt
def generate_image(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        title = data.get('title', 'événement')

        try:
            image_bytes = imageGen({"inputs": f"Event poster for {title}, professional, modern"})
            image = Image.open(io.BytesIO(image_bytes))

            # ✅ Sauvegarde temporaire dans /media/images/
            image_name = f"temp_{title.replace(' ', '_')}.jpg"
            image_path = os.path.join('media/images', image_name)
            os.makedirs(os.path.dirname(image_path), exist_ok=True)

            image.save(image_path, format='JPEG')

            return JsonResponse({
                'image_url': '/' + image_path,   # ✅ Pour afficher l'image
                'image_path': image_path         # ✅ Pour save_model dans admin
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Méthode non autorisée'}, status=400)





def test_models(request):
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    models = genai.list_models()
    # Utiliser l'attribut 'name' des objets Model
    output = "<br>".join([m.name for m in models])
    return HttpResponse(output)



genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
IMAGEGEN_KEY = os.getenv('IMAGEGEN_KEY')
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
HEADERS = {"Authorization": f"Bearer {IMAGEGEN_KEY}"}

def ai_generate_description(title):
    # Utiliser un modèle existant comme "gemini-2.5-flash"
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"Écris une description professionnelle et détaillée en 3 lignes pour un événement intitulé : {title}"
    response = model.generate_content(prompt)
    return response.text


@csrf_exempt
def generate_description(request):
    if request.method == "POST":
        data = json.loads(request.body)
        title = data.get("title", "")
        description = ai_generate_description(title)
        return JsonResponse({"description": description})
    return JsonResponse({"error": "Méthode non autorisée"}, status=400)



def liste_evenements(request):
    evenements = Evenement.objects.all().order_by('-date_debut')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(evenements, 6)  # 6 événements par page
    
    try:
        evenements = paginator.page(page)
    except PageNotAnInteger:
        evenements = paginator.page(1)
    except EmptyPage:
        evenements = paginator.page(paginator.num_pages)
    
    return render(request, 'evenement/liste_evenements.html', {'evenements': evenements})
    

def detail_evenement(request, evenement_id):
    evenement = get_object_or_404(Evenement, id=evenement_id)
    deja_participe = False
    
    if request.user.is_authenticated:
        from participation.models import Participation
        deja_participe = Participation.objects.filter(
            utilisateur=request.user, 
            evenement=evenement
        ).exists()
    
    context = {
        'evenement': evenement,
        'deja_participe': deja_participe,
        'now': timezone.now(),
    }
    return render(request, 'evenement/detail_evenement.html', context)