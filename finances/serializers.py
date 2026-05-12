# finances/serializers.py

from rest_framework import serializers
from .models import Depense, Revenu, CategoriDepense, BudgetMensuel

class CategoriDepenseSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CategoriDepense
        fields = '__all__'

class DepenseSerializer(serializers.ModelSerializer):
    categorie_nom = serializers.CharField(
        source='categorie.nom', read_only=True
    )
    lot_nom = serializers.CharField(
        source='lot.nom', read_only=True
    )

    class Meta:
        model  = Depense
        fields = [
            'id', 'date', 'categorie', 'categorie_nom',
            'description', 'montant_fcfa', 'lot', 'lot_nom',
            'notes', 'saisie_par',
        ]
        read_only_fields = ['id', 'saisie_par', 'categorie_nom', 'lot_nom']

class RevenuSerializer(serializers.ModelSerializer):
    lot_nom = serializers.CharField(
        source='lot.nom', read_only=True
    )

    class Meta:
        model  = Revenu
        fields = [
            'id', 'date', 'type_revenu', 'description',
            'quantite', 'prix_unitaire_fcfa', 'montant_fcfa',
            'lot', 'lot_nom', 'notes', 'saisie_par',
        ]
        read_only_fields = ['id', 'montant_fcfa', 'saisie_par', 'lot_nom']

class BudgetMensuelSerializer(serializers.ModelSerializer):
    class Meta:
        model  = BudgetMensuel
        fields = '__all__'
        read_only_fields = ['id']