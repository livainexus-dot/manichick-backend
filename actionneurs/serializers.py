# actionneurs/serializers.py

from rest_framework import serializers
from .models import EtatActionneur, CommandeManuelle

class EtatActionneurSerializer(serializers.ModelSerializer):
    # Champ calculé : nombre d'ampoules allumées
    nb_ampoules_allumees = serializers.IntegerField(read_only=True)

    class Meta:
        model  = EtatActionneur
        fields = [
            'id', 'timestamp',
            'ventilateur', 'distributeur', 'sirene',
            'ampoule_1', 'ampoule_2', 'ampoule_3',
            'ampoule_4', 'ampoule_5', 'ampoule_6',
            'nb_ampoules_allumees', 'mode_eclairage', 'source',
        ]
        read_only_fields = ['id', 'timestamp', 'nb_ampoules_allumees']

class CommandeManuelleSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CommandeManuelle
        fields = ['id', 'timestamp', 'actionneur', 'etat', 'utilisateur']
        read_only_fields = ['id', 'timestamp', 'utilisateur']