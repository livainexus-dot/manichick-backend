# alertes/views.py

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from .models import Alerte
from .serializers import AlerteSerializer

class AlerteListView(generics.ListAPIView):
    """
    GET /api/alertes/ → retourne toutes les alertes (actives en premier)
    """
    serializer_class = AlerteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # On peut filtrer par ?acquittee=false dans l'URL
        acquittee = self.request.query_params.get('acquittee', None)
        queryset = Alerte.objects.all()

        if acquittee is not None:
            # "false" (string) → False (booléen)
            queryset = queryset.filter(acquittee=(acquittee.lower() == 'true'))

        return queryset[:50]  # limite à 50 alertes


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def acquitter_alerte(request, pk):
    """
    PATCH /api/alertes/{id}/acquitter/ → acquitte une alerte par son id
    PATCH = modification partielle (on ne change que acquittee=True)
    """
    try:
        alerte = Alerte.objects.get(pk=pk)
    except Alerte.DoesNotExist:
        return Response(
            {'erreur': 'Alerte introuvable'},
            status=status.HTTP_404_NOT_FOUND
        )

    alerte.acquittee = True
    alerte.acquittee_par = request.user
    alerte.acquittee_le = timezone.now()
    alerte.save()

    return Response(AlerteSerializer(alerte).data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def acquitter_toutes(request):
    """
    PATCH /api/alertes/acquitter-toutes/ → acquitte toutes les alertes actives
    """
    # update() : mise à jour en masse sans charger chaque objet en mémoire
    Alerte.objects.filter(acquittee=False).update(
        acquittee=True,
        acquittee_par=request.user,
        acquittee_le=timezone.now(),
    )
    return Response(
        {'message': 'Toutes les alertes ont été acquittées'},
        status=status.HTTP_200_OK
    )