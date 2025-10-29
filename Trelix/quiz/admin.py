from django.contrib import admin
from .models import Quiz, Question, Choice, Badge, UserBadge


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "pass_mark")
    list_filter = ("is_active",)
    search_fields = ("title",)
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "quiz", "points")
    inlines = [ChoiceInline]


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ("text", "question", "is_correct")


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "icon")
    
    # ✅ On retire slug du formulaire (Django le crée automatiquement)
    fields = ("name", "description", "icon")

    # ✅ Slug visible seulement en lecture si on veut l'afficher
    readonly_fields = ("slug",)


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ("user", "badge", "quiz", "score", "created_at")
    list_filter = ("badge", "quiz", "user")
    search_fields = ("user__username", "badge__name")
