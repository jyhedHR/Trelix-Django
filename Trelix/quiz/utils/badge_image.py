import os
import requests
import base64
from PIL import Image
from io import BytesIO
from django.conf import settings

STABILITY_KEY = settings.STABILITY_API_KEY

def generate_badge_image(badge_name):

    if not STABILITY_KEY:
        print("❌ API key missing")
        return None

    url = "https://api.stability.ai/v2beta/stable-image/generate/sd3"

    headers = {
        "Authorization": f"Bearer {STABILITY_KEY}",
        "Accept": "application/json"
        # ❌ NE PAS mettre Content-Type ici !
    }

    form_data = {
        "prompt": f"{badge_name} medal, round badge, shiny metallic texture, star in center, videogame style, glowing rim, high detail, award emblem",
        "output_format": "png",
        "size": "512x512"
    }

    # ✅ multipart/form-data = utiliser 'files'
    response = requests.post(url, headers=headers, files=form_data)

    print("DEBUG Status:", response.status_code)
    print("DEBUG Resp:", response.text[:300])

    file_name = f"{badge_name.replace(' ', '_').lower()}.png"
    badge_folder = os.path.join(settings.MEDIA_ROOT, "badges")
    os.makedirs(badge_folder, exist_ok=True)
    image_path = os.path.join(badge_folder, file_name)

    if response.status_code == 200:
        data = response.json()
        img_base64 = data["artifacts"][0]["base64"]

        img_bytes = base64.b64decode(img_base64)
        image = Image.open(BytesIO(img_bytes))
        image.save(image_path)
        print("✅ Image OK !")

    else:
        print("⚠️ FALLBACK —", response.text)
        Image.new("RGB", (350, 350), (50, 100, 200)).save(image_path)

    return f"badges/{file_name}"
