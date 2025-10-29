from django.contrib import admin
from django.utils.html import format_html
from .models import Course

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title','image_tag', 'level', 'is_published')
    list_filter = ('level', 'is_published')
    search_fields = ('title', 'description')
    readonly_fields = ('image_preview',)


    # Méthode pour afficher un aperçu de l'image
    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "-"
    image_tag.short_description = 'Image'
    # Aperçu dans le formulaire
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img id="image_preview" src="{}" style="max-width:300px; max-height:300px;" />', obj.image.url)
        return format_html('<img id="image_preview" style="max-width:300px; max-height:300px; display:none;" />')
    image_preview.short_description = 'Image preview'
    class Media:
        js = ('js/image_preview.js',)
