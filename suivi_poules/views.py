# suivi_poules/views.py

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Avg
from .models import SuiviJournalier, EntreeVeterinaire
from .serializers import SuiviJournalierSerializer, EntreeVeterinaireSerializer

class SuiviListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/suivi/journalier/ → liste des 30 derniers jours
    POST /api/suivi/journalier/ → crée une entrée pour aujourd'hui
    """
    serializer_class   = SuiviJournalierSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SuiviJournalier.objects.all()[:30]


class SuiviDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/DELETE /api/suivi/journalier/{id}/
    Permet de modifier une entrée existante (correction d'erreur)
    """
    serializer_class   = SuiviJournalierSerializer
    permission_classes = [IsAuthenticated]
    queryset           = SuiviJournalier.objects.all()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stats_suivi(request):
    """
    GET /api/suivi/stats/ → statistiques agrégées sur 30 jours
    Utilisé par l'écran Statistiques de l'app mobile.
    """
    donnees = SuiviJournalier.objects.all()[:30]

    # aggregate : calcule des totaux sur un queryset entier
    totaux = donnees.aggregate(
        total_oeufs     = Sum('nb_oeufs'),
        total_morts     = Sum('nb_morts'),
        total_nourriture= Sum('nourriture_kg'),
        moy_oeufs       = Avg('nb_oeufs'),
    )

    return Response({
        'total_oeufs':      totaux['total_oeufs']      or 0,
        'total_morts':      totaux['total_morts']      or 0,
        'total_nourriture': totaux['total_nourriture'] or 0,
        'moyenne_oeufs_par_jour': round(totaux['moy_oeufs'] or 0, 1),
        'nb_jours':         donnees.count(),
    })


class VetListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/suivi/veterinaire/ → journal vétérinaire
    POST /api/suivi/veterinaire/ → nouvelle entrée vétérinaire
    """
    serializer_class   = EntreeVeterinaireSerializer
    permission_classes = [IsAuthenticated]
    queryset           = EntreeVeterinaire.objects.all()


class VetDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class   = EntreeVeterinaireSerializer
    permission_classes = [IsAuthenticated]
    queryset           = EntreeVeterinaire.objects.all()