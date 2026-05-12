# utilisateurs/serializers.py

from rest_framework import serializers
from django.utils import timezone
from .models import Utilisateur, JournalActivite

class UtilisateurSerializer(serializers.ModelSerializer):
    nom_complet = serializers.CharField(read_only=True)

    class Meta:
        model  = Utilisateur
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'nom_complet', 'role', 'telephone', 'valide',
            'valide_le', 'photo_url', 'derniere_activite',
            'date_joined',
        ]
        read_only_fields = [
            'id', 'valide', 'valide_le', 'nom_complet',
            'date_joined', 'derniere_activite',
        ]


class InscriptionSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour l'inscription d'un nouvel employé.
    Le compte est créé en attente de validation admin.
    """
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model  = Utilisateur
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'role', 'telephone',
        ]

    def validate(self, data):
        # Vérifie que les deux mots de passe correspondent
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError(
                {'password_confirm': 'Les mots de passe ne correspondent pas.'}
            )
        # Seuls employe et superviseur peuvent s'inscrire
        # L'admin est créé uniquement via manage.py createsuperuser
        if data.get('role') == 'admin':
            raise serializers.ValidationError(
                {'role': 'Impossible de s\'inscrire en tant qu\'administrateur.'}
            )
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        utilisateur = Utilisateur.objects.create_user(
            password = password,
            # Compte en attente de validation → is_active=False
            is_active = False,
            valide    = False,
            **validated_data,
        )
        return utilisateur


class ValidationCompteSerializer(serializers.Serializer):
    """Sérialiseur pour valider ou rejeter un compte."""
    action = serializers.ChoiceField(choices=['valider', 'rejeter'])


class JournalActiviteSerializer(serializers.ModelSerializer):
    utilisateur_nom = serializers.CharField(
        source='utilisateur.nom_complet', read_only=True
    )

    class Meta:
        model  = JournalActivite
        fields = [
            'id', 'timestamp', 'action',
            'details', 'utilisateur_nom',
        ]
        read_only_fields = ['id', 'timestamp']