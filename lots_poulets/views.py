# lots_poulets/views.py

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum
from .models import Lot, SuiviLot, VenteProduction
from .serializers import (
    LotSerializer, LotDetailSerializer,
    SuiviLotSerializer, VenteProductionSerializer,
)
from .ia_nutrition import (
    calculer_besoins_lot,
    analyser_croissance,
    recommander_ajustement_nutrition,
)
from capteurs.models import Mesure


class LotListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/lots/          → liste tous les lots actifs
    POST /api/lots/          → crée un nouveau lot
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return LotSerializer

    def get_queryset(self):
        actif = self.request.query_params.get('actif', 'true')
        return Lot.objects.filter(actif=(actif == 'true'))


class LotDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/DELETE /api/lots/{id}/ → détail d'un lot avec suivis
    """
    permission_classes = [IsAuthenticated]
    queryset           = Lot.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return LotDetailSerializer
        return LotSerializer


class SuiviLotListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/lots/{lot_id}/suivis/ → liste des suivis d'un lot
    POST /api/lots/{lot_id}/suivis/ → ajoute un suivi hebdomadaire
    """
    serializer_class   = SuiviLotSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SuiviLot.objects.filter(
            lot_id=self.kwargs['lot_id']
        )

    def perform_create(self, serializer):
        lot = Lot.objects.get(pk=self.kwargs['lot_id'])
        serializer.save(
            lot=lot,
            semaine=lot.age_semaines,
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ia_besoins_lot(request, lot_id):
    """
    GET /api/lots/{id}/ia-besoins/
    Calcule les besoins nutritionnels du lot pour aujourd'hui.
    Tient compte de la température ambiante réelle du poulailler.
    """
    try:
        lot = Lot.objects.get(pk=lot_id)
    except Lot.DoesNotExist:
        return Response({'erreur': 'Lot introuvable'}, status=404)

    # Récupère la température actuelle depuis les capteurs
    derniere_mesure = Mesure.objects.first()
    temperature     = derniere_mesure.temperature if derniere_mesure else 25.0

    # Calcule les besoins de base
    besoins = calculer_besoins_lot(
        type_lot  = lot.type_lot,
        semaine   = lot.age_semaines,
        nb_sujets = lot.nb_sujets,
    )

    # Ajuste selon la température réelle
    recommandation = recommander_ajustement_nutrition(
        temperature_reelle = temperature,
        type_lot           = lot.type_lot,
        semaine            = lot.age_semaines,
        nb_sujets          = lot.nb_sujets,
    )

    return Response({
        'lot':             LotSerializer(lot).data,
        'age_semaines':    lot.age_semaines,
        'temperature_actuelle': temperature,
        'besoins_base':    besoins,
        'recommandation':  recommandation,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ia_analyse_croissance(request, lot_id):
    """
    GET /api/lots/{id}/ia-croissance/
    Analyse la courbe de croissance réelle vs référence FAO.
    """
    try:
        lot = Lot.objects.get(pk=lot_id)
    except Lot.DoesNotExist:
        return Response({'erreur': 'Lot introuvable'}, status=404)

    suivis = list(
        SuiviLot.objects.filter(lot=lot)
        .values('semaine', 'poids_moyen_g')
        .order_by('semaine')
    )

    analyse = analyser_croissance(suivis, lot.type_lot)

    return Response({
        'lot':     LotSerializer(lot).data,
        'analyse': analyse,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def tableau_bord_lots(request):
    """
    GET /api/lots/tableau-bord/
    Vue synthétique de tous les lots actifs avec leurs besoins du jour.
    C'est l'écran principal de l'onglet Lots dans l'app mobile.
    """
    lots   = Lot.objects.filter(actif=True)
    derniere_mesure = Mesure.objects.first()
    temperature     = derniere_mesure.temperature if derniere_mesure else 25.0

    resultat = []
    for lot in lots:
        besoins = calculer_besoins_lot(
            lot.type_lot, lot.age_semaines, lot.nb_sujets
        )
        recommandation = recommander_ajustement_nutrition(
            temperature, lot.type_lot, lot.age_semaines, lot.nb_sujets
        )

        # Dernier suivi pour comparaison
        dernier_suivi = SuiviLot.objects.filter(lot=lot).first()

        resultat.append({
            'lot':          LotSerializer(lot).data,
            'besoins_jour': recommandation,
            'dernier_suivi': SuiviLotSerializer(dernier_suivi).data
                if dernier_suivi else None,
        })

    return Response(resultat)


class VenteListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/lots/{lot_id}/ventes/
    POST /api/lots/{lot_id}/ventes/
    """
    serializer_class   = VenteProductionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return VenteProduction.objects.filter(
            lot_id=self.kwargs['lot_id']
        )

    def perform_create(self, serializer):
        lot = Lot.objects.get(pk=self.kwargs['lot_id'])
        serializer.save(lot=lot)