import os
import requests
from PIL import Image
from io import BytesIO
from django.conf import settings

STABILITY_KEY = os.environ.get("STABILITY_KEY")

def generate_badge_image(badge_name):
    if not STABILITY_KEY:
        print("❌ Clé API Stability manquante")
        return None

    url = "https://api.stability.ai/v2beta/stable-image/generate/core"
    headers = {
        "Authorization": f"Bearer {STABILITY_KEY}",
    }

    prompt = f"A shiny gold video game badge with star, 3D metallic effect, high quality, text: {badge_name}"

    data = {
        "prompt": prompt,
        "aspect_ratio": "1:1",
        "output_format": "png",
    }

    response = requests.post(url, headers=headers, data=data)

    file_name = f"{badge_name.replace(' ', '_').lower()}.png"
    badge_folder = os.path.join(settings.MEDIA_ROOT, "badges")
    os.makedirs(badge_folder, exist_ok=True)
    image_path = os.path.join(badge_folder, file_name)

    if response.status_code == 200:
        image = Image.open(BytesIO(response.content))
        image.save(image_path)
        print(f"✅ Badge IA généré : {file_name}")
    else:
        print("⚠️ Erreur IA → Fallback")
        fallback = Image.new("RGB", (350, 350), (200, 50, 50))
        fallback.save(image_path)

    return f"badges/{file_name}"

import os
from django.conf import settings

def generate_badge_image(badge_name):
    if not settings.STABILITY_API_KEY:
        print("❌ Clé API Stability manquante")
        return None
