# alertes/serializers.py

from rest_framework import serializers
from .models import Alerte

class AlerteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alerte
        fields = ['id', 'timestamp', 'type_alerte', 'message',
                  'valeur', 'seuil', 'gravite', 'acquittee',
                  'acquittee_par', 'acquittee_le']
        read_only_fields = ['id', 'timestamp', 'acquittee_par', 'acquittee_le']