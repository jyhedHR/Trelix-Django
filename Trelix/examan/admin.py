# admin.py (replace the QuestionForm section and QuestionAdmin)

from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import json
from .models import Exam, Question, StudentExam, Certificate, Answer


# ----------------------------------------------------------------------
# 1. EXAM FORM (unchanged)
# ----------------------------------------------------------------------
class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = '__all__'

    def clean_title(self):
        title = self.cleaned_data['title']
        if not title.strip():
            raise forms.ValidationError(_("Title cannot be empty."))
        return title.strip()

    def clean_duration(self):
        duration = self.cleaned_data['duration']
        if duration is None or duration < 1:
            raise forms.ValidationError(_("Duration must be a positive number (minutes)."))
        return duration


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    form = ExamForm
    list_display = ('title', 'description_short', 'duration', 'date_created')
    search_fields = ('title', 'description')
    list_filter = ('date_created',)
    ordering = ('-date_created',)
    list_per_page = 10

    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = "Description"


# ----------------------------------------------------------------------
# 2. USER-FRIENDLY MCQ OPTIONS WIDGET
# ----------------------------------------------------------------------
class MCQOptionsWidget(forms.Widget):
    template_name = 'admin/mcq_options_widget.html'  # We'll create this template
    input_type = 'text'

    def __init__(self, attrs=None):
        super().__init__(attrs)
        self.num_options = 4  # Default 4 options, admin can add/remove

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if value:
            try:
                options = json.loads(value) if isinstance(value, str) else value
                options = options if isinstance(options, list) else []
            except:
                options = []
        else:
            options = []
        
        # Fill with empty strings if less than num_options
        while len(options) < self.num_options:
            options.append('')
        
        context['widget']['options'] = options[:self.num_options]
        context['widget']['num_options'] = self.num_options
        return context

    def value_from_datadict(self, data, files, name):
        options = []
        for i in range(self.num_options):
            option_key = f"{name}_option_{i}"
            option_value = data.get(option_key, '').strip()
            if option_value:  # Only include non-empty options
                options.append(option_value)
        return json.dumps(options) if options else None


# ----------------------------------------------------------------------
# 3. QUESTION FORM WITH USER-FRIENDLY OPTIONS
# ----------------------------------------------------------------------
class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = '__all__'
        widgets = {
            'options': MCQOptionsWidget(attrs={'class': 'vTextField'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show/hide options field based on question type
        if self.instance.pk:  # Editing existing
            if self.instance.question_type != 'MCQ':
                self.fields['options'].widget = forms.HiddenInput()
        else:  # Adding new
            self.fields['options'].widget.attrs['style'] = 'display: none;' if self.data.get('question_type') != 'MCQ' else ''

    def clean_text(self):
        text = self.cleaned_data['text']
        if not text.strip():
            raise forms.ValidationError(_("Question text cannot be empty."))
        return text.strip()

    def clean(self):
        cleaned_data = super().clean()
        qtype = cleaned_data.get('question_type')
        options = cleaned_data.get('options')
        correct = cleaned_data.get('correct_answer')

        if qtype == 'MCQ':
            if not options:
                raise forms.ValidationError({"options": _("MCQ must provide at least 2 options.")})

            # Validate options structure
            try:
                opts = json.loads(options) if isinstance(options, str) else options
            except json.JSONDecodeError:
                raise forms.ValidationError({"options": _("Invalid options format.")})

            if not isinstance(opts, list) or len(opts) < 2:
                raise forms.ValidationError({"options": _("MCQ needs at least 2 options.")})

            # Remove empty options and validate
            valid_opts = [opt for opt in opts if opt.strip()]
            if len(valid_opts) < 2:
                raise forms.ValidationError({"options": _("At least 2 non-empty options required.")})

            # Correct answer must be one of the valid options
            if correct not in valid_opts:
                raise forms.ValidationError({
                    "correct_answer": _(f"Correct answer must be one of: {', '.join(valid_opts)}")
                })

        else:  # TXT
            if not correct or not correct.strip():
                raise forms.ValidationError({
                    "correct_answer": _("Text questions require a correct answer.")
                })

        return cleaned_data

    def clean_correct_answer(self):
        correct = self.cleaned_data.get('correct_answer', '').strip()
        qtype = self.cleaned_data.get('question_type')
        
        if qtype == 'MCQ':
            # For MCQ, we'll validate in clean() method above
            pass
        else:
            if not correct:
                raise forms.ValidationError(_("Text questions require a correct answer."))
        
        return correct


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    form = QuestionForm
    list_display = ('text_short', 'question_type', 'exam')
    list_filter = ('question_type', 'exam')
    search_fields = ('text',)
    list_per_page = 10
    class Media:
        js = ('admin/js/mcq_options.js',)  # We'll create this JS file

    def text_short(self, obj):
        return obj.text[:60] + '...' if len(obj.text) > 60 else obj.text
    text_short.short_description = "Question"

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'options':
            # Custom widget only for MCQ questions
            if self.form.declared_fields.get('question_type') == 'MCQ':
                kwargs['widget'] = MCQOptionsWidget()
        return super().formfield_for_dbfield(db_field, request, **kwargs)



class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ('question', 'text')
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