from rest_framework import status, generics, serializers
# utilisateurs/views.py

from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils import timezone
from .models import Utilisateur, JournalActivite
from .serializers import (
    UtilisateurSerializer, InscriptionSerializer,
    JournalActiviteSerializer,
)


def enregistrer_activite(utilisateur, action, details='', request=None):
    """Enregistre une action dans le journal d'activité."""
    ip = None
    if request:
        ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0] \
             or request.META.get('REMOTE_ADDR')
    JournalActivite.objects.create(
        utilisateur = utilisateur,
        action      = action,
        details     = details,
        adresse_ip  = ip,
    )


class ManichickTokenSerializer(TokenObtainPairSerializer):
    """
    Sérialiseur JWT personnalisé qui vérifie la validation du compte
    avant d'autoriser la connexion.
    """
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        # Vérifie si le compte est validé
        if not user.valide and not user.is_superuser:
            raise serializers.ValidationError(
                'Votre compte est en attente de validation par un administrateur.'
            )

        # Met à jour la dernière activité
        user.derniere_activite = timezone.now()
        user.save(update_fields=['derniere_activite'])

        # Enregistre le login dans le journal
        enregistrer_activite(user, 'login')

        # Ajoute les infos utilisateur à la réponse JWT
        data['utilisateur'] = UtilisateurSerializer(user).data
        return data


class ManichickLoginView(TokenObtainPairView):
    serializer_class = ManichickTokenSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def inscription(request):
    """
    POST /api/auth/inscription/
    Crée un compte en attente de validation.
    """
    serializer = InscriptionSerializer(data=request.data)
    if serializer.is_valid():
        utilisateur = serializer.save()
        return Response({
            'message': (
                'Compte créé avec succès. '
                'Un administrateur doit valider votre compte avant que vous puissiez vous connecter.'
            ),
            'username': utilisateur.username,
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profil(request):
    """GET /api/auth/profil/ → profil de l'utilisateur connecté."""
    serializer = UtilisateurSerializer(request.user)
    return Response(serializer.data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def modifier_profil(request):
    """PUT /api/auth/profil/modifier/ → met à jour le profil."""
    serializer = UtilisateurSerializer(
        request.user,
        data=request.data,
        partial=True,
    )
    if serializer.is_valid():
        serializer.save()
        enregistrer_activite(request.user, 'modifier_profil')
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ── Vues réservées aux admins ────────────────────────────

class EstAdmin:
    """Permission personnalisée : réservé aux admins."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and (request.user.role == 'admin' or request.user.is_superuser)
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def liste_employes(request):
    """
    GET /api/auth/employes/
    Liste tous les utilisateurs — admins seulement.
    """
    if not (request.user.role == 'admin' or request.user.is_superuser):
        return Response(
            {'erreur': 'Accès réservé aux administrateurs.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    statut = request.query_params.get('statut', 'tous')
    if statut == 'attente':
        users = Utilisateur.objects.filter(valide=False, is_superuser=False)
    elif statut == 'valides':
        users = Utilisateur.objects.filter(valide=True)
    else:
        users = Utilisateur.objects.filter(is_superuser=False)

    serializer = UtilisateurSerializer(users, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def valider_compte(request, user_id):
    """
    POST /api/auth/employes/{id}/valider/
    Valide ou rejette un compte en attente — admins seulement.
    Body: {"action": "valider"} ou {"action": "rejeter"}
    """
    if not (request.user.role == 'admin' or request.user.is_superuser):
        return Response(
            {'erreur': 'Accès réservé aux administrateurs.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        utilisateur = Utilisateur.objects.get(pk=user_id)
    except Utilisateur.DoesNotExist:
        return Response({'erreur': 'Utilisateur introuvable'}, status=404)

    action = request.data.get('action')

    if action == 'valider':
        utilisateur.valide     = True
        utilisateur.is_active  = True
        utilisateur.valide_le  = timezone.now()
        utilisateur.valide_par = request.user
        utilisateur.save()

        enregistrer_activite(
            request.user, 'valider_compte',
            f'Compte {utilisateur.username} validé'
        )
        return Response({
            'message': f'Compte de {utilisateur.username} validé avec succès.',
            'utilisateur': UtilisateurSerializer(utilisateur).data,
        })

    elif action == 'rejeter':
        nom = utilisateur.username
        utilisateur.delete()
        enregistrer_activite(
            request.user, 'rejeter_compte',
            f'Compte {nom} rejeté et supprimé'
        )
        return Response({'message': f'Compte de {nom} rejeté et supprimé.'})

    return Response(
        {'erreur': 'Action invalide. Utilisez "valider" ou "rejeter".'},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def journal_activite(request):
    """
    GET /api/auth/journal/
    Journal d'activité — admins et superviseurs seulement.
    """
    if request.user.role == 'employe' and not request.user.is_superuser:
        return Response(
            {'erreur': 'Accès non autorisé.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    activites = JournalActivite.objects.all()[:50]
    serializer = JournalActiviteSerializer(activites, many=True)
    return Response(serializer.data)