# capteurs/serializers.py

from rest_framework import serializers
from .models import Mesure, PhotoIntrusion

class MesureSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Mesure
        fields = [
            'id', 'timestamp',
            'temperature', 'humidite', 'gaz_ppm', 'luminosite',
            'co2_ppm', 'nh3_ppm',
            'niveau_eau', 'presence', 'nb_poules',
            'nb_ampoules_allumees', 'photo_intrusion_url',
        ]
        read_only_fields = ['id', 'timestamp']

class PhotoIntrusionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PhotoIntrusion
        fields = [
            'id', 'timestamp', 'description',
            'zone', 'acquittee', 'image_base64'
        ]
        read_only_fields = ['id', 'timestamp']