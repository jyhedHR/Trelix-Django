from django.shortcuts import render, get_object_or_404
from .models import Exam, StudentExam, Answer, Certificate
from django.shortcuts import redirect
from django.utils import timezone

from django.shortcuts import render
from .models import Exam, StudentExam
from django.http import JsonResponse
from django.template.loader import render_to_string 
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os
from reportlab.lib import colors
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
from django.contrib.auth.decorators import login_required
from cloudinary import uploader
import random
import string



@login_required
def exams_view(request):
    exams = Exam.objects.all()
    exams_status = []

    for exam in exams:
        student_exam = StudentExam.objects.filter(student=request.user, exam=exam).last()
        certificate = None
        if student_exam and student_exam.score >= 50:
            cert_obj = Certificate.objects.filter(student=request.user, exam=exam).first()
            if cert_obj and cert_obj.file_path:
                certificate = cert_obj.get_certificate_url()  # get the proper PDF URL from Cloudinary

        exams_status.append({
            'exam': exam,
            'completed': student_exam is not None,
            'score': student_exam.score if student_exam else None,
            'student_exam_id': student_exam.id if student_exam else None,
            'certificate': certificate
        })

    return render(request, 'trelix/exams.html', {'exams_status': exams_status})



def single_exam_view(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    questions = exam.questions.all()
    return render(request, 'trelix/exam_detail.html', {'exam': exam, 'questions': questions})


def submit_exam_view(request, exam_id):
    if request.method == "POST":
        exam = get_object_or_404(Exam, id=exam_id)
        student = request.user

        # Get or create StudentExam
        student_exam, created = StudentExam.objects.get_or_create(
            student=student,
            exam=exam
        )

        student_exam.completed_at = timezone.now()

        total_questions = exam.questions.count()
        correct_count = 0

        for question in exam.questions.all():
            answer_text = request.POST.get(f"q{question.id}", "").strip()

            Answer.objects.update_or_create(
                student_exam=student_exam,
                question=question,
                defaults={"text": answer_text}
            )

            if answer_text.lower() == question.correct_answer.lower():
                correct_count += 1

        student_exam.score = (correct_count / total_questions) * 100 if total_questions > 0 else 0
        student_exam.save()

        # ✅ Generate certificate if score >= 50%
        if student_exam.score >= 50:
            # Check if certificate already exists
            cert_obj, created = Certificate.objects.get_or_create(
                student=student,
                exam=exam
            )
            # Only generate and upload if certificate doesn't exist or doesn't have file
            if created or not cert_obj.file_path:
                certificate_path = generate_certificate(student, exam)
                full_path = os.path.join(settings.MEDIA_ROOT, certificate_path)
                if os.path.exists(full_path):
                    try:
                        # Upload to Cloudinary with raw resource type for PDF
                        upload_result = uploader.upload(
                            full_path, 
                            folder="certificates", 
                            resource_type="raw",
                            format="pdf"
                        )
                        # Store secure_url or public_id - prefer secure_url for direct access
                        if upload_result:
                            # Store public_id (CloudinaryField will use this)
                            if 'public_id' in upload_result:
                                cert_obj.file_path = upload_result['public_id']
                                cert_obj.save()
                            # Also can store secure_url in a different field if needed, but public_id works with get_certificate_url()
                    except Exception as e:
                        # Fallback: use File.save method
                        try:
                            from django.core.files import File
                            if cert_obj.pk:
                                with open(full_path, 'rb') as f:
                                    cert_obj.file_path.save(os.path.basename(certificate_path), File(f), save=False)
                                cert_obj.save()
                        except Exception:
                            pass  # Silently fail if upload fails

        return redirect('exam_submitted', exam_id=exam.id)

def exam_submitted_view(request, exam_id):
    student_exam = StudentExam.objects.filter(student=request.user, exam__id=exam_id).latest('completed_at')
    certificate = None
    if student_exam.score >= 50:
        certificate = student_exam.exam.certificate_set.filter(student=request.user).first()
    return render(request, 'trelix/exam_submitted.html', {
        'student_exam': student_exam,
        'certificate': certificate
    })
def exam_result_view(request, student_exam_id):
    student_exam = get_object_or_404(StudentExam, id=student_exam_id, student=request.user)
    answers = Answer.objects.filter(student_exam=student_exam)
    context = {
        'student_exam': student_exam,
        'answers': answers,
        'exam': student_exam.exam,
    }

    # If it's an AJAX request, return partial HTML
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('trelix/exam_result.html', context, request=request)
        return JsonResponse({'html': html})

    # Fallback normal render (if accessed directly)
    return render(request, 'trelix/exam_result.html', context)

def generate_certificate(student, exam):
    """
    Overlays the student's name and exam title onto a pre-designed PDF template
    using the Great Vibes font. Returns the relative file path for FileField.
    """
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    # Ensure certificates directory exists
    cert_dir = os.path.join(settings.MEDIA_ROOT, 'certificates')
    os.makedirs(cert_dir, exist_ok=True)

    # Output file
    file_name = f"{student.username}_{exam.title.replace(' ', '_')}.pdf"
    file_path = os.path.join(cert_dir, file_name)

    # Load template
    template_path = os.path.join(settings.BASE_DIR, 'Trelix', 'static', 'certificate_design_trelix.pdf')
    template_pdf = PdfReader(template_path)
    output_pdf = PdfWriter()

    # Create overlay PDF with ReportLab
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)

    # Register Great Vibes font
    font_path = os.path.join(settings.BASE_DIR, 'Trelix', 'static', 'fonts', 'GreatVibes-Regular.ttf')
    pdfmetrics.registerFont(TTFont('GreatVibes', font_path))

    # Customize coordinates to fit your template's placeholders
    student_name_x, student_name_y = 380, 260  # adjust to your template
    exam_title_x, exam_title_y = 380, 150      # adjust to your template
    # Draw current date
    can.setFont("Helvetica", 14)
    current_date = timezone.now().strftime("%d %B %Y")
    can.drawCentredString(300, 50, f"Date: {current_date}")
    # Draw student name and exam title using Great Vibes
    can.setFont("GreatVibes", 36)
    can.drawCentredString(student_name_x, student_name_y, student.get_full_name() or student.username)

    can.setFont("GreatVibes", 28)
    can.drawCentredString(exam_title_x, exam_title_y, exam.title)

    can.save()
    packet.seek(0)
    overlay_pdf = PdfReader(packet)

    # Merge overlay with template
    page = template_pdf.pages[0]
    page.merge_page(overlay_pdf.pages[0])
    output_pdf.add_page(page)

    # Save final certificate
    with open(file_path, "wb") as f:
        output_pdf.write(f)

    # Return relative path for FileField
    return f"certificates/{file_name}"

