# finances/views.py

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncMonth, TruncWeek
from django.utils import timezone
import datetime
from .models import Depense, Revenu, CategoriDepense, BudgetMensuel
from .serializers import (
    DepenseSerializer, RevenuSerializer,
    CategoriDepenseSerializer, BudgetMensuelSerializer,
)


class DepenseListCreateView(generics.ListCreateAPIView):
    serializer_class   = DepenseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Depense.objects.all()
        # Filtre par mois si fourni : ?mois=2026-05
        mois = self.request.query_params.get('mois')
        if mois:
            annee, m = mois.split('-')
            qs = qs.filter(date__year=annee, date__month=m)
        return qs[:100]

    def perform_create(self, serializer):
        serializer.save(saisie_par=self.request.user)


class RevenuListCreateView(generics.ListCreateAPIView):
    serializer_class   = RevenuSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Revenu.objects.all()
        mois = self.request.query_params.get('mois')
        if mois:
            annee, m = mois.split('-')
            qs = qs.filter(date__year=annee, date__month=m)
        return qs[:100]

    def perform_create(self, serializer):
        serializer.save(saisie_par=self.request.user)


class DepenseDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class   = DepenseSerializer
    permission_classes = [IsAuthenticated]
    queryset           = Depense.objects.all()


class RevenuDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class   = RevenuSerializer
    permission_classes = [IsAuthenticated]
    queryset           = Revenu.objects.all()


class CategoriListView(generics.ListCreateAPIView):
    serializer_class   = CategoriDepenseSerializer
    permission_classes = [IsAuthenticated]
    queryset           = CategoriDepense.objects.all()


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tableau_bord_finances(request):
    """
    GET /api/finances/tableau-bord/
    Vue synthétique complète : totaux, tendances, ROI par lot.
    C'est l'endpoint principal du module Big Data financier.
    """
    if request.user.role == 'employe' and not request.user.is_superuser:
        return Response(
            {'erreur': 'Accès réservé aux administrateurs et superviseurs.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    aujourd_hui = timezone.now().date()
    debut_mois  = aujourd_hui.replace(day=1)

    # ── Totaux du mois en cours ──────────────────────────
    depenses_mois = Depense.objects.filter(
        date__gte=debut_mois
    ).aggregate(total=Sum('montant_fcfa'))['total'] or 0

    revenus_mois = Revenu.objects.filter(
        date__gte=debut_mois
    ).aggregate(total=Sum('montant_fcfa'))['total'] or 0

    benefice_mois = revenus_mois - depenses_mois

    # ── Totaux globaux ───────────────────────────────────
    total_depenses = Depense.objects.aggregate(
        total=Sum('montant_fcfa')
    )['total'] or 0

    total_revenus = Revenu.objects.aggregate(
        total=Sum('montant_fcfa')
    )['total'] or 0

    # ── Évolution mensuelle sur 6 mois (Big Data) ────────
    six_mois_avant = aujourd_hui - datetime.timedelta(days=180)

    evolution_depenses = list(
        Depense.objects
        .filter(date__gte=six_mois_avant)
        .annotate(mois=TruncMonth('date'))
        .values('mois')
        .annotate(total=Sum('montant_fcfa'))
        .order_by('mois')
    )

    evolution_revenus = list(
        Revenu.objects
        .filter(date__gte=six_mois_avant)
        .annotate(mois=TruncMonth('date'))
        .values('mois')
        .annotate(total=Sum('montant_fcfa'))
        .order_by('mois')
    )

    # ── Dépenses par catégorie (camembert) ───────────────
    depenses_par_categorie = list(
        Depense.objects
        .values('categorie__nom', 'categorie__couleur_hex')
        .annotate(total=Sum('montant_fcfa'))
        .order_by('-total')
    )

    # ── ROI par lot ──────────────────────────────────────
    from lots_poulets.models import Lot
    roi_par_lot = []
    for lot in Lot.objects.filter(actif=True):
        dep = Depense.objects.filter(lot=lot).aggregate(
            total=Sum('montant_fcfa')
        )['total'] or 0
        rev = Revenu.objects.filter(lot=lot).aggregate(
            total=Sum('montant_fcfa')
        )['total'] or 0
        roi_par_lot.append({
            'lot_nom':       lot.nom,
            'type_lot':      lot.type_lot,
            'depenses_fcfa': dep,
            'revenus_fcfa':  rev,
            'benefice_fcfa': rev - dep,
            'roi_pct':       round(((rev - dep) / dep * 100) if dep > 0 else 0, 1),
        })

    # ── Projections IA ───────────────────────────────────
    # Projection simple : moyenne des 3 derniers mois × facteur tendance
    trois_mois = aujourd_hui - datetime.timedelta(days=90)
    moy_dep_3m = Depense.objects.filter(
        date__gte=trois_mois
    ).aggregate(moy=Avg('montant_fcfa'))['moy'] or 0

    moy_rev_3m = Revenu.objects.filter(
        date__gte=trois_mois
    ).aggregate(moy=Avg('montant_fcfa'))['moy'] or 0

    return Response({
        'mois_courant': {
            'depenses':  depenses_mois,
            'revenus':   revenus_mois,
            'benefice':  benefice_mois,
            'rentable':  benefice_mois > 0,
        },
        'totaux': {
            'depenses': total_depenses,
            'revenus':  total_revenus,
            'benefice': total_revenus - total_depenses,
        },
        'evolution_mensuelle': {
            'depenses': [
                {
                    'mois':  e['mois'].strftime('%Y-%m'),
                    'total': e['total'],
                }
                for e in evolution_depenses
            ],
            'revenus': [
                {
                    'mois':  e['mois'].strftime('%Y-%m'),
                    'total': e['total'],
                }
                for e in evolution_revenus
            ],
        },
        'depenses_par_categorie': depenses_par_categorie,
        'roi_par_lot':            roi_par_lot,
        'projection_ia': {
            'depenses_mois_prochain':  round(moy_dep_3m * 30, 0),
            'revenus_mois_prochain':   round(moy_rev_3m * 30, 0),
            'benefice_projete':        round((moy_rev_3m - moy_dep_3m) * 30, 0),
        },
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def rapport_mensuel(request):
    """
    GET /api/finances/rapport/?mois=2026-05
    Rapport détaillé d'un mois donné.
    """
    mois_param = request.query_params.get(
        'mois',
        timezone.now().strftime('%Y-%m')
    )
    annee, mois = mois_param.split('-')

    depenses = Depense.objects.filter(
        date__year=annee, date__month=mois
    )
    revenus = Revenu.objects.filter(
        date__year=annee, date__month=mois
    )

    total_dep = depenses.aggregate(t=Sum('montant_fcfa'))['t'] or 0
    total_rev = revenus.aggregate(t=Sum('montant_fcfa'))['t'] or 0

    return Response({
        'periode':   mois_param,
        'depenses':  DepenseSerializer(depenses, many=True).data,
        'revenus':   RevenuSerializer(revenus, many=True).data,
        'total_depenses': total_dep,
        'total_revenus':  total_rev,
        'benefice':       total_rev - total_dep,
    })
