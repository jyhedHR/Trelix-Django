from django.contrib import admin
from .models import Exam, Question, StudentExam, Certificate, Answer


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'description_short', 'duration', 'date_created')
    search_fields = ('title', 'description')
    list_filter = ('date_created',)
    ordering = ('-date_created',)
    list_per_page = 10

    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = "Description"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text_short', 'question_type', 'exam')
    list_filter = ('question_type', 'exam')
    search_fields = ('text',)
    list_per_page = 10

    def text_short(self, obj):
        return obj.text[:60] + '...' if len(obj.text) > 60 else obj.text
    text_short.short_description = "Question"

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0  # don't show empty extra forms
    readonly_fields = ('question', 'text')  # make answers read-only
    can_delete = False
@admin.register(StudentExam)
class StudentExamAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'score', 'completed_at')
    list_filter = ('completed_at', 'exam')
    search_fields = ('student__username', 'exam__title')
    ordering = ('-completed_at',)
    list_per_page = 10
    inlines = [AnswerInline]


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'date_issued')
    list_filter = ('date_issued',)
    search_fields = ('student__username', 'exam__title')
    ordering = ('-date_issued',)
    list_per_page = 10

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('student_exam', 'question', 'short_text')
    search_fields = ('student_exam__student__username', 'question__text', 'text')
    list_filter = ('question__exam',)
    list_per_page = 20

    def short_text(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    short_text.short_description = "Answer"