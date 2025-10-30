# badge_image.py
import os
import base64
import requests
from io import BytesIO
from PIL import Image
from django.conf import settings

# Load STABILITY_KEY dynamically to ensure we get the latest value
def get_stability_key():
    return getattr(settings, "STABILITY_API_KEY", None)

STABILITY_KEY = get_stability_key()


def generate_badge_image(badge_name: str) -> str:
    # Re-check STABILITY_KEY each time in case settings changed
    stability_key = get_stability_key()
    if not stability_key:
        print("⚠️ STABILITY_API_KEY missing - using fallback image")
        return _fallback_image(badge_name)

    url = "https://api.stability.ai/v2beta/stable-image/generate/sd3"

    headers = {
        "Authorization": f"Bearer {stability_key}",
        "Accept": "application/json",
    }

    files = {
        "prompt": (None, f"{badge_name} medal, round badge, shiny metallic texture, star in center, videogame style, glowing rim, high detail, award emblem"),
        "output_format": (None, "png"),
        "model": (None, "sd3"),
    }

    try:
        response = requests.post(url, headers=headers, files=files, timeout=90)
    except requests.RequestException as e:
        print(f"Request exception: {e}")
        return _fallback_image(badge_name)

    print(f"🔄 API Status: {response.status_code}")
    if response.status_code != 200:
        print(f"❌ API error {response.status_code}: {response.text[:500]}")
        return _fallback_image(badge_name)

    try:
        data = response.json()

        # NEW FORMAT: "image" field contains base64
        img_b64 = data.get("image")
        if not img_b64:
            print("No 'image' field in response")
            return _fallback_image(badge_name)

        img_bytes = base64.b64decode(img_b64)
        img = Image.open(BytesIO(img_bytes))

        return _save_image(img, badge_name)

    except Exception as exc:
        print(f"Image processing error: {exc}")
        return _fallback_image(badge_name)


def _save_image(pil_img: Image.Image, badge_name: str) -> str:
    file_name = f"{badge_name.replace(' ', '_').lower()}.png"
    badge_folder = os.path.join(settings.MEDIA_ROOT, "badges")
    os.makedirs(badge_folder, exist_ok=True)
    image_path = os.path.join(badge_folder, file_name)

    pil_img.save(image_path, format="PNG")
    print(f"✅ Generated badge image saved: {image_path}")
    return f"badges/{file_name}"


def _fallback_image(badge_name: str) -> str:
    file_name = f"{badge_name.replace(' ', '_').lower()}.png"
    badge_folder = os.path.join(settings.MEDIA_ROOT, "badges")
    os.makedirs(badge_folder, exist_ok=True)
    image_path = os.path.join(badge_folder, file_name)

    Image.new("RGB", (512, 512), (100, 100, 200)).save(image_path)
    print(f"⚠️ Fallback blue image saved: {image_path}")
    return f"badges/{file_name}"