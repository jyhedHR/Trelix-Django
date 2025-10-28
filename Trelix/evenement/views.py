from django.shortcuts import render, get_object_or_404
from django.db.models import Count
from .models import Evenement

def liste_evenements(request):
    evenements = Evenement.objects.all().order_by('-date_debut')
    
    types_stats = Evenement.objects.values('type').annotate(count=Count('id'))
    
    for stat in types_stats:
        stat['type__display'] = dict(Evenement.TYPE_CHOICES)[stat['type']]
    
    context = {
        'evenements': evenements,
        'types': types_stats,
    }
    return render(request, 'evenement/liste_evenements.html', context)

def detail_evenement(request, evenement_id):
    evenement = get_object_or_404(Evenement, id=evenement_id)
    return render(request, 'evenement/detail_evenement.html', {'evenement': evenement})