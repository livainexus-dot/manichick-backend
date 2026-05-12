# lots_poulets/serializers.py

from rest_framework import serializers
from .models import Lot, SuiviLot, VenteProduction

class SuiviLotSerializer(serializers.ModelSerializer):
    class Meta:
        model  = SuiviLot
        fields = '__all__'
        read_only_fields = ['id']

class VenteProductionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = VenteProduction
        fields = '__all__'
        read_only_fields = ['id', 'montant_fcfa']

class LotSerializer(serializers.ModelSerializer):
    # Champs calculés depuis les propriétés du modèle
    age_jours    = serializers.IntegerField(read_only=True)
    age_semaines = serializers.IntegerField(read_only=True)
    # Nombre de suivis enregistrés
    nb_suivis    = serializers.SerializerMethodField()

    class Meta:
        model  = Lot
        fields = [
            'id', 'nom', 'type_lot', 'nb_sujets',
            'date_arrivee', 'actif', 'notes',
            'date_abattage_prevue', 'date_ponte_prevue',
            'age_jours', 'age_semaines', 'nb_suivis',
        ]
        read_only_fields = ['id', 'age_jours', 'age_semaines', 'nb_suivis']

    def get_nb_suivis(self, obj):
        return obj.suivis.count()

class LotDetailSerializer(LotSerializer):
    """Sérialiseur complet avec les suivis inclus."""
    suivis = SuiviLotSerializer(many=True, read_only=True)
    ventes = VenteProductionSerializer(many=True, read_only=True)

    class Meta(LotSerializer.Meta):
        fields = LotSerializer.Meta.fields + ['suivis', 'ventes']