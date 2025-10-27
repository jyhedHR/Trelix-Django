from django.contrib import admin
from .models import Exam, Question, StudentExam, Certificate

admin.site.register(Exam)
admin.site.register(Question)
admin.site.register(StudentExam)
admin.site.register(Certificate)
