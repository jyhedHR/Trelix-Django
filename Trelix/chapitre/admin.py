from django.contrib import admin
from django.utils.html import format_html
from .models import Chapter

@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'video_tag')
    list_filter = ('course',)
    search_fields = ('title', 'course__title')
    readonly_fields = ('video_preview',)  # Pour aperçu dans le formulaire

    # Aperçu vidéo dans la liste
    def video_tag(self, obj):
        if obj.video:
            return format_html(
                '<video width="100" height="60" controls><source src="{}" type="video/mp4"></video>',
                obj.video.url
            )
        return "-"
    video_tag.short_description = "Vidéo"

    # Aperçu vidéo dans le formulaire
    def video_preview(self, obj):
        html = ''
        if obj and obj.video:
            html = f'<video width="300" height="200" controls><source src="{obj.video.url}" type="video/mp4"></video>'
        # Toujours retourner un div avec un id fixe pour le JS
        return format_html('<div id="video_preview_container">{}</div>', html)

    video_preview.short_description = "Video preview"


    class Media:
        js = ('js/video_preview.js',)  # Pour aperçu instantané avant submit
