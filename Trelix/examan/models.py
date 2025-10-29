from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class Exam(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    duration = models.IntegerField(help_text="Duration in minutes")
    date_created = models.DateTimeField(auto_now_add=True)

class Question(models.Model):
    TYPE_CHOICES = [
        ('MCQ', 'Multiple Choice'),
        ('TXT', 'Text Answer')
    ]
    exam = models.ForeignKey(Exam, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField()
    question_type = models.CharField(max_length=3, choices=TYPE_CHOICES)
    options = models.JSONField(blank=True, null=True)  # for MCQs
    correct_answer = models.TextField()

class StudentExam(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    score = models.FloatField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

class Certificate(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    date_issued = models.DateTimeField(auto_now_add=True)
    file_path = models.FileField(upload_to='certificates/') 


# examapp/models.py
class Answer(models.Model):
    student_exam = models.ForeignKey(StudentExam, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_exam.student.username} - {self.question.text[:20]}"
