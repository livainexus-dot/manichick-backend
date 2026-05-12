# suivi_poules/serializers.py

from rest_framework import serializers
from .models import SuiviJournalier, EntreeVeterinaire

class SuiviJournalierSerializer(serializers.ModelSerializer):
    class Meta:
        model  = SuiviJournalier
        fields = '__all__'  # inclut tous les champs
        read_only_fields = ['id']

class EntreeVeterinaireSerializer(serializers.ModelSerializer):
    class Meta:
        model  = EntreeVeterinaire
        fields = '__all__'
        read_only_fields = ['id']