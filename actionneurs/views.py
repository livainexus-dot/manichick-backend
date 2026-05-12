# actionneurs/views.py

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import EtatActionneur, CommandeManuelle
from .serializers import EtatActionneurSerializer, CommandeManuelleSerializer

class EtatActionneurDernierView(generics.RetrieveAPIView):
    serializer_class   = EtatActionneurSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return EtatActionneur.objects.first()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def envoyer_commande(request):
    actionneur = request.data.get('actionneur')
    etat       = request.data.get('etat')

    # Liste mise à jour avec les ampoules individuelles
    actionneurs_valides = [
        'ventilateur', 'distributeur', 'sirene',
        'ampoule_1', 'ampoule_2', 'ampoule_3',
        'ampoule_4', 'ampoule_5', 'ampoule_6',
        'toutes_ampoules',  # commande spéciale : toutes ON/OFF
    ]

    if actionneur not in actionneurs_valides:
        return Response(
            {'erreur': f'Actionneur inconnu : {actionneur}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    dernier = EtatActionneur.objects.first()

    # Construit le nouvel état en copiant l'existant
    nouvel_etat = {
        'ventilateur':   dernier.ventilateur   if dernier else False,
        'distributeur':  dernier.distributeur  if dernier else False,
        'sirene':        dernier.sirene        if dernier else False,
        'ampoule_1':     dernier.ampoule_1     if dernier else True,
        'ampoule_2':     dernier.ampoule_2     if dernier else True,
        'ampoule_3':     dernier.ampoule_3     if dernier else True,
        'ampoule_4':     dernier.ampoule_4     if dernier else True,
        'ampoule_5':     dernier.ampoule_5     if dernier else True,
        'ampoule_6':     dernier.ampoule_6     if dernier else True,
        'mode_eclairage': 'manuel',
        'source':        'manuel',
    }

    if actionneur == 'toutes_ampoules':
        # Commande spéciale : toutes les ampoules ON ou OFF
        for i in range(1, 7):
            nouvel_etat[f'ampoule_{i}'] = etat
    else:
        nouvel_etat[actionneur] = etat

    EtatActionneur.objects.create(**nouvel_etat)

    CommandeManuelle.objects.create(
        actionneur  = actionneur,
        etat        = etat if not isinstance(etat, dict) else True,
        utilisateur = request.user,
    )

    return Response(
        {'message': f'{actionneur} mis à jour'},
        status=status.HTTP_200_OK
    )