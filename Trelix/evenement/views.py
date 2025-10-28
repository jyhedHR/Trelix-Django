from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from .models import Evenement

def liste_evenements(request):
    evenements = Evenement.objects.all().order_by('-date_debut')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(evenements, 6)  # 6 événements par page
    
    try:
        evenements = paginator.page(page)
    except PageNotAnInteger:
        evenements = paginator.page(1)
    except EmptyPage:
        evenements = paginator.page(paginator.num_pages)
    
    return render(request, 'evenement/liste_evenements.html', {'evenements': evenements})

def detail_evenement(request, evenement_id):
    evenement = get_object_or_404(Evenement, id=evenement_id)
    deja_participe = False
    
    if request.user.is_authenticated:
        from participation.models import Participation
        deja_participe = Participation.objects.filter(
            utilisateur=request.user, 
            evenement=evenement
        ).exists()
    
    context = {
        'evenement': evenement,
        'deja_participe': deja_participe,
        'now': timezone.now(),
    }
    return render(request, 'evenement/detail_evenement.html', context)