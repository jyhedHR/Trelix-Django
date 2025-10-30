# badge_image.py
import base64
import requests
from io import BytesIO
from PIL import Image

# Load STABILITY_KEY dynamically to ensure we get the latest value
def get_stability_key():
    from django.conf import settings
    return getattr(settings, "STABILITY_API_KEY", None)


def generate_badge_image(badge_name: str):
    """
    Generate badge image using Stability AI API or return fallback.
    Returns tuple: (PIL.Image, bool) where bool indicates if it's a fallback.
    """
    # Re-check STABILITY_KEY each time in case settings changed
    stability_key = get_stability_key()
    if not stability_key:
        print("⚠️ STABILITY_API_KEY missing - using fallback image")
        fallback_img = Image.new("RGB", (512, 512), (100, 100, 200))
        return fallback_img, True  # Return image and is_fallback=True

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
        fallback_img = Image.new("RGB", (512, 512), (100, 100, 200))
        return fallback_img, True

    print(f"🔄 API Status: {response.status_code}")
    if response.status_code != 200:
        print(f"❌ API error {response.status_code}: {response.text[:500]}")
        fallback_img = Image.new("RGB", (512, 512), (100, 100, 200))
        return fallback_img, True

    try:
        data = response.json()

        # NEW FORMAT: "image" field contains base64
        img_b64 = data.get("image")
        if not img_b64:
            print("No 'image' field in response")
            fallback_img = Image.new("RGB", (512, 512), (100, 100, 200))
            return fallback_img, True

        img_bytes = base64.b64decode(img_b64)
        img = Image.open(BytesIO(img_bytes))

        print(f"✅ Generated badge image from API")
        return img, False  # Return image and is_fallback=False

    except Exception as exc:
        print(f"Image processing error: {exc}")
        fallback_img = Image.new("RGB", (512, 512), (100, 100, 200))
        return fallback_img, True