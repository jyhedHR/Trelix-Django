from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone  # Important
from evenement.models import Evenement
from .models import Participation
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .forms import ParticipationForm
from django.db.models import Count
from reportlab.pdfgen import canvas
import os
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle




def download_pdf(request, pk):
    participation = get_object_or_404(Participation, id=pk, utilisateur=request.user)
    evenement = participation.evenement

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="participation_{pk}.pdf"'

    p = canvas.Canvas(response)

    # ----- Image événement -----
    if evenement.image:
        img_path = os.path.join(settings.MEDIA_ROOT, str(evenement.image))
        if os.path.exists(img_path):
            p.drawImage(img_path, 350, 720, width=150, height=120, preserveAspectRatio=True)
    # ---------------------------

    # Title
    p.setFont("Helvetica-Bold", 18)
    p.drawString(100, 800, "Attestation de Participation")

    p.setFont("Helvetica", 12)

    p.drawString(100, 740, f"Événement : {evenement.titre}")
    p.drawString(100, 720, f"Rôle : {participation.role}")
    p.drawString(100, 700, f"Niveau d'étude : {participation.niveau_etude}")
    p.drawString(100, 680, f"Années d'expérience : {participation.annee_experience}")
    p.drawString(100, 660, f"Domaine de compétence : {participation.domaine_competence}")
    p.drawString(100, 640, f"Expérience précédente : {participation.experience_precedente}")
    p.drawString(100, 620, f"Date de participation : {participation.date_participation.strftime('%d/%m/%Y')}")

    p.showPage()
    p.save()
    return response







@login_required
def participer_evenement(request, evenement_id):
    evenement = get_object_or_404(Evenement, id=evenement_id)
    
    # Vérifier si l'utilisateur participe déjà
    if Participation.objects.filter(utilisateur=request.user, evenement=evenement).exists():
        messages.warning(request, "Vous participez déjà à cet événement.")
        return redirect('evenement:detail_evenement', evenement_id=evenement_id)
    
    # Vérifier si l'événement n'est pas déjà terminé
    if evenement.date_fin < timezone.now():
        messages.error(request, "Cet événement est déjà terminé.")
        return redirect('evenement:detail_evenement', evenement_id=evenement_id)
    
    if request.method == 'POST':
        form = ParticipationForm(request.POST)
        if form.is_valid():
            participation = form.save(commit=False)
            participation.utilisateur = request.user
            participation.evenement = evenement
            participation.save()
            
            messages.success(request, "Your participation has been successfully registered!")
            return redirect('evenement:detail_evenement', evenement_id=evenement_id)
    else:
        form = ParticipationForm()
    
    return render(request, 'participation/participation_form.html', {
        'form': form,
        'evenement': evenement
    })

@login_required
def annuler_participation(request, evenement_id):
    evenement = get_object_or_404(Evenement, id=evenement_id)
    participation = get_object_or_404(
        Participation, 
        utilisateur=request.user, 
        evenement=evenement
    )
    
    if request.method == 'POST':
        participation.delete()
        messages.success(request, "Votre participation a été annulée.")
    
    return redirect('evenement:detail_evenement', evenement_id=evenement_id)

@login_required
def mes_participations(request):
    # Récupérer les participations de l'utilisateur
    participations = Participation.objects.filter(utilisateur=request.user).select_related('evenement')
    
    # Appliquer les filtres
    selected_role = request.GET.get('role', '')
    selected_domaine = request.GET.get('domaine', '')
    selected_niveau = request.GET.get('niveau', '')
    selected_type = request.GET.get('type_evenement', '')
    
    if selected_role:
        participations = participations.filter(role=selected_role)
    if selected_domaine:
        participations = participations.filter(domaine_competence=selected_domaine)
    if selected_niveau:
        participations = participations.filter(niveau_etude=selected_niveau)
    if selected_type:
        participations = participations.filter(evenement__type=selected_type)
    
    # Appliquer le tri
    sort = request.GET.get('sort', 'date_desc')
    if sort == 'date_asc':
        participations = participations.order_by('date_participation')
    elif sort == 'title_asc':
        participations = participations.order_by('evenement__titre')
    elif sort == 'title_desc':
        participations = participations.order_by('-evenement__titre')
    else:  # date_desc par défaut
        participations = participations.order_by('-date_participation')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(participations, 8)
    
    try:
        participations_page = paginator.page(page)
    except PageNotAnInteger:
        participations_page = paginator.page(1)
    except EmptyPage:
        participations_page = paginator.page(paginator.num_pages)
    
    # Statistiques
    now = timezone.now()
    total_participations = Participation.objects.filter(utilisateur=request.user).count()
    upcoming_count = Participation.objects.filter(
        utilisateur=request.user, 
        evenement__date_debut__gt=now
    ).count()
    ongoing_count = Participation.objects.filter(
        utilisateur=request.user,
        evenement__date_debut__lte=now,
        evenement__date_fin__gte=now
    ).count()
    completed_count = Participation.objects.filter(
        utilisateur=request.user,
        evenement__date_fin__lt=now
    ).count()
    
    # Compter par rôle pour les compteurs
    role_counts_query = Participation.objects.filter(utilisateur=request.user).values('role').annotate(count=Count('role'))
    role_counts = {item['role']: item['count'] for item in role_counts_query}
    
    context = {
        'participations': participations_page,
        'total_participations': total_participations,
        'upcoming_count': upcoming_count,
        'ongoing_count': ongoing_count,
        'completed_count': completed_count,
        'selected_role': selected_role,
        'selected_domaine': selected_domaine,
        'selected_niveau': selected_niveau,
        'selected_type': selected_type,
        'role_counts': role_counts,
        'now': now,
        
        # CHOIX POUR LES FILTRES
        'ROLE_CHOICES': Participation.ROLE_CHOICES,
        'NIVEAU_ETUDE_CHOICES': Participation.NIVEAU_ETUDE_CHOICES,
        'DOMAINE_COMPETENCE_CHOICES': Participation.DOMAINE_COMPETENCE_CHOICES,
        'TYPE_CHOICES': [
            ('hackathon', 'Hackathon'),
            ('workshop', 'Workshop'),
            ('conference', 'Conférence'),
            ('formation', 'Formation'),
        ],
    }
    
    return render(request, 'participation/mes_participations.html', context)