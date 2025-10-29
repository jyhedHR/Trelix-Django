from django.contrib import admin
from django.core.files import File
from django.utils.html import format_html
from django.urls import path
from django.http import JsonResponse
from django.conf import settings
from django import forms
import os, io, json, requests
from PIL import Image
from .models import Evenement



class EvenementAdminForm(forms.ModelForm):
    generated_image_path = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Evenement
        fields = "__all__"



def imageGen(payload):
    API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    headers = {"Authorization": f"Bearer {settings.IMAGEGEN_KEY}"}
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.content



@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    form = EvenementAdminForm
    list_display = ['titre', 'type', 'date_debut', 'date_fin', 'lieu', 'capacite_max', 'nombre_participants']
    readonly_fields = ['generate_image_button']
    list_filter = ['type', 'date_debut', 'date_fin']
    search_fields = ['titre', 'description', 'lieu']

    def generate_image_button(self, obj):
        return format_html(
            """
            <div>
                <button type="button" class="generate-image-btn" data-obj-id="{}">🎨 Générer l'image</button>
                <br>
                <img id="generated-image-preview-{}" style="margin-top:5px; max-width:200px; display:none;">
                <input type="hidden" name="generated_image_path" id="generated-image-path-{}">
            </div>
            """,
            obj.pk, obj.pk, obj.pk
        )
    generate_image_button.short_description = "Image IA"

    class Media:
             js = (
            'js/generate_image.js',
            'js/generate_description.js',
        )

    def nombre_participants(self, obj):
        return obj.participation_set.count()

    def save_model(self, request, obj, form, change):
        image_path = form.cleaned_data.get("generated_image_path")

        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as f:
                obj.image.save(os.path.basename(image_path), File(f), save=False)

        super().save_model(request, obj, form, change)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("generate-image/", self.admin_site.admin_view(self.generate_image_view), name="generate_image"),
        ]
        return custom_urls + urls

    def generate_image_view(self, request):
        if request.method == "POST":
            data = json.loads(request.body)
            title = data.get("title", "")

            image_bytes = imageGen({"inputs": f"Event poster for {title}, professional, modern"})
            os.makedirs("media/images", exist_ok=True)

            path = f"media/images/temp_gen_{title}.jpg"
            img = Image.open(io.BytesIO(image_bytes))
            img.save(path, format="JPEG")

            return JsonResponse({
                "image_url": "/" + path,
                "image_path": path
            })

        return JsonResponse({"error": "Méthode invalide"}, status=400)
