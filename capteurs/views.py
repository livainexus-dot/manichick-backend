# capteurs/views.py — version complète

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.utils import timezone
import datetime
from .models import Mesure, PhotoIntrusion
from .serializers import MesureSerializer, PhotoIntrusionSerializer
from alertes.models import Alerte
from actionneurs.models import EtatActionneur
from capteurs.ia_engine import (
    predire_valeur,
    detecter_anomalie_zscore,
    calculer_seuils_adaptatifs
)

# ── Seuils environnementaux ──────────────────────────────
SEUILS = {
    'temperature': {'avertissement': 32, 'critique': 35},
    'humidite':    {'avertissement': 80, 'critique': 90},
    'gaz_ppm':     {'avertissement': 200, 'critique': 300},
    'co2_ppm':     {'avertissement': 2000, 'critique': 3000},
    'nh3_ppm':     {'avertissement': 10, 'critique': 25},
    'niveau_eau':  {'avertissement': 30, 'critique': 20},
}

# ── Seuils luminosité pour éclairage automatique ─────────
# En dessous de ces seuils → on allume des ampoules
SEUILS_LUX = [800, 600, 400, 300, 200, 100]
# Ex: lux=350 → ampoules 4,5,6 allumées (seuils 300, 200, 100 dépassés)


def calculer_ampoules(luminosite: int) -> dict:
    """
    Calcule quelles ampoules doivent être allumées
    selon la luminosité naturelle (LDR).

    Logique : plus il fait sombre, plus on allume d'ampoules.
    Les ampoules s'éteignent progressivement quand le jour arrive.

    Retourne un dict avec ampoule_1 à ampoule_6.
    """
    etats = {}
    for i, seuil in enumerate(SEUILS_LUX, 1):
        # L'ampoule i s'allume si la luminosité est sous son seuil
        etats[f'ampoule_{i}'] = luminosite < seuil
    return etats


def gerer_eclairage(mesure: Mesure):
    """
    Gère l'éclairage automatique en fonction de la luminosité.
    Crée un nouvel état d'actionneur si le nombre d'ampoules change.
    """
    # Récupère le dernier état
    dernier = EtatActionneur.objects.first()

    # Calcule les nouveaux états d'ampoules
    nouveaux_etats = calculer_ampoules(mesure.luminosite)

    # Vérifie si l'état a changé
    if dernier:
        # Compare chaque ampoule
        change = any(
            getattr(dernier, f'ampoule_{i}') != nouveaux_etats[f'ampoule_{i}']
            for i in range(1, 7)
        )
        if not change:
            return  # Pas de changement → rien à faire

    # Crée un nouvel état avec les ampoules mises à jour
    EtatActionneur.objects.create(
        ventilateur  = dernier.ventilateur  if dernier else False,
        distributeur = dernier.distributeur if dernier else False,
        sirene       = dernier.sirene       if dernier else False,
        mode_eclairage = 'auto',
        source       = 'auto',
        **nouveaux_etats,  # ampoule_1 à ampoule_6
    )

    nb = sum(nouveaux_etats.values())
    print(f"💡 Éclairage mis à jour : {nb}/6 ampoules — lux={mesure.luminosite}")


def gerer_camera_intrusion(mesure: Mesure):
    """
    Déclenche la caméra si une intrusion est détectée la nuit.
    En simulation : génère des métadonnées réalistes.
    En production : l'ESP32-CAM envoie une vraie image base64.
    """
    if not mesure.presence:
        return

    heure = timezone.now().hour
    # Intrusion valide seulement entre 20h et 6h
    if not (heure >= 20 or heure < 6):
        return

    # Évite les doublons dans les 2 dernières minutes
    deux_min = timezone.now() - timezone.timedelta(minutes=2)
    if PhotoIntrusion.objects.filter(timestamp__gte=deux_min).exists():
        return

    # Crée l'entrée photo (simulée)
    PhotoIntrusion.objects.create(
        description = f'Intrusion détectée à {timezone.now().strftime("%H:%M:%S")}',
        zone        = 'Zone principale',
        # En simulation : image base64 vide
        # En production : reçue depuis ESP32-CAM via MQTT
        image_base64 = '',
    )

    # Crée l'alerte intrusion
    Alerte.objects.create(
        type_alerte = 'INTRUSION',
        message     = f'Caméra : mouvement détecté à {timezone.now().strftime("%H:%M")}',
        valeur      = 1,
        seuil       = 0,
        gravite     = 'critique',
    )

    # Active la sirène automatiquement
    dernier = EtatActionneur.objects.first()
    if dernier and not dernier.sirene:
        EtatActionneur.objects.create(
            ventilateur  = dernier.ventilateur,
            distributeur = dernier.distributeur,
            sirene       = True,
            ampoule_1    = dernier.ampoule_1,
            ampoule_2    = dernier.ampoule_2,
            ampoule_3    = dernier.ampoule_3,
            ampoule_4    = dernier.ampoule_4,
            ampoule_5    = dernier.ampoule_5,
            ampoule_6    = dernier.ampoule_6,
            mode_eclairage = dernier.mode_eclairage,
            source       = 'auto',
        )
    print(f"📸 Photo intrusion enregistrée + sirène activée")


def verifier_et_creer_alertes(mesure: Mesure):
    """
    Vérifie tous les seuils et crée les alertes nécessaires.
    """
    verifications = [
        ('temperature', mesure.temperature, 'CHALEUR',   '°C'),
        ('humidite',    mesure.humidite,    'HUMIDITE',  '%'),
        ('gaz_ppm',     mesure.gaz_ppm,     'GAZ',       ' ppm'),
        ('co2_ppm',     mesure.co2_ppm,     'CO2',       ' ppm'),
        ('nh3_ppm',     mesure.nh3_ppm,     'NH3',       ' ppm'),
    ]

    for champ, valeur, type_alerte, unite in verifications:
        seuils = SEUILS[champ]
        if valeur >= seuils['critique']:
            gravite, seuil_depasse = 'critique', seuils['critique']
        elif valeur >= seuils['avertissement']:
            gravite, seuil_depasse = 'avertissement', seuils['avertissement']
        else:
            continue

        Alerte.objects.create(
            type_alerte = type_alerte,
            message     = f'{type_alerte} : {valeur}{unite} dépasse {seuil_depasse}{unite}',
            valeur      = valeur,
            seuil       = seuil_depasse,
            gravite     = gravite,
        )

    # ── Alerte niveau eau ────────────────────────────────
    if mesure.niveau_eau < SEUILS['niveau_eau']['critique']:
        Alerte.objects.create(
            type_alerte = 'EAU',
            message     = f'Abreuvoir presque vide : {mesure.niveau_eau}%',
            valeur      = mesure.niveau_eau,
            seuil       = SEUILS['niveau_eau']['critique'],
            gravite     = 'critique',
        )
    elif mesure.niveau_eau < SEUILS['niveau_eau']['avertissement']:
        Alerte.objects.create(
            type_alerte = 'EAU',
            message     = f'Niveau eau faible : {mesure.niveau_eau}%',
            valeur      = mesure.niveau_eau,
            seuil       = SEUILS['niveau_eau']['avertissement'],
            gravite     = 'avertissement',
        )

    # ── Éclairage automatique ────────────────────────────
    gerer_eclairage(mesure)

    # ── Caméra intrusion ─────────────────────────────────
    gerer_camera_intrusion(mesure)


# ── Vues API ─────────────────────────────────────────────

class MesureListView(generics.ListAPIView):
    serializer_class   = MesureSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Mesure.objects.all()[:100]


class MesureDerniereView(generics.RetrieveAPIView):
    serializer_class   = MesureSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return Mesure.objects.first()


@api_view(['POST'])
@permission_classes([AllowAny])
def creer_mesure(request):
    serializer = MesureSerializer(data=request.data)
    if serializer.is_valid():
        mesure = serializer.save()
        verifier_et_creer_alertes(mesure)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analyse_ia(request):
    mesures = list(reversed(list(Mesure.objects.all()[:50])))
    if len(mesures) < 5:
        return Response({'erreur': 'Pas assez de données'})

    temperatures = [m.temperature for m in mesures]
    humidites    = [m.humidite    for m in mesures]

    prediction_temp = predire_valeur(temperatures, horizon=180)
    zscore_temp     = detecter_anomalie_zscore(temperatures[:-1], temperatures[-1])
    zscore_hum      = detecter_anomalie_zscore(humidites[:-1], humidites[-1])
    seuils_temp     = calculer_seuils_adaptatifs(temperatures)

    return Response({
        'prediction_temperature': prediction_temp,
        'anomalie_temperature':   zscore_temp,
        'anomalie_humidite':      zscore_hum,
        'seuils_adaptatifs':      seuils_temp,
        'nb_mesures_analysees':   len(mesures),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def photos_intrusion(request):
    """
    GET /api/capteurs/photos-intrusion/ → liste des photos d'intrusion
    """
    photos = PhotoIntrusion.objects.all()[:20]
    serializer = PhotoIntrusionSerializer(photos, many=True)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def acquitter_photo(request, pk):
    """
    PATCH /api/capteurs/photos-intrusion/{id}/acquitter/
    """
    try:
        photo = PhotoIntrusion.objects.get(pk=pk)
        photo.acquittee = True
        photo.save()
        return Response({'message': 'Photo acquittée'})
    except PhotoIntrusion.DoesNotExist:
        return Response({'erreur': 'Photo introuvable'}, status=404)
    
    # Ajoute à la fin de capteurs/views.py

from capteurs.big_data import agregation_par_periode, stats_globales, detecter_patterns

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def big_data_dashboard(request):
    """
    GET /api/capteurs/big-data/
    Agrégations Big Data complètes — utilisé par l'écran Statistiques.

    Paramètres URL optionnels :
    ?periode=jour&jours=30
    """
    periode = request.query_params.get('periode', 'jour')
    nb_jours = int(request.query_params.get('jours', 7))

    temp_agregee = agregation_par_periode(Mesure, 'temperature', periode, nb_jours)
    hum_agregee  = agregation_par_periode(Mesure, 'humidite',    periode, nb_jours)
    gaz_agrege   = agregation_par_periode(Mesure, 'gaz_ppm',     periode, nb_jours)

    stats = stats_globales(Mesure, nb_jours)
    patterns = detecter_patterns(Mesure)

    return Response({
        'periode':     periode,
        'nb_jours':    nb_jours,
        'statistiques_globales': stats,
        'series_temporelles': {
            'temperature': [
                {
                    'periode': str(e['periode']),
                    'moy':     round(e['moy'], 2) if e['moy'] else 0,
                    'min':     round(e['min'], 2) if e['min'] else 0,
                    'max':     round(e['max'], 2) if e['max'] else 0,
                }
                for e in temp_agregee
            ],
            'humidite': [
                {
                    'periode': str(e['periode']),
                    'moy':     round(e['moy'], 2) if e['moy'] else 0,
                }
                for e in hum_agregee
            ],
            'gaz': [
                {
                    'periode': str(e['periode']),
                    'moy':     round(e['moy'], 2) if e['moy'] else 0,
                    'max':     round(e['max'], 2) if e['max'] else 0,
                }
                for e in gaz_agrege
            ],
        },
        'patterns': patterns,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_csv(request):
    """
    GET /api/capteurs/export-csv/?jours=30
    Exporte les mesures en CSV pour analyse externe.
    C'est la partie "export" du Big Data.
    """
    from django.http import HttpResponse
    import csv

    nb_jours = int(request.query_params.get('jours', 7))
    depuis   = timezone.now() - datetime.timedelta(days=nb_jours)
    mesures  = Mesure.objects.filter(timestamp__gte=depuis).order_by('timestamp')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="manichick_mesures_{nb_jours}j.csv"'
    )

    writer = csv.writer(response)
    # En-tête
    writer.writerow([
        'timestamp', 'temperature', 'humidite', 'gaz_ppm',
        'luminosite', 'co2_ppm', 'nh3_ppm',
        'niveau_eau', 'presence', 'nb_poules',
        'nb_ampoules_allumees',
    ])
    # Données
    for m in mesures:
        writer.writerow([
            m.timestamp.isoformat(),
            m.temperature, m.humidite, m.gaz_ppm,
            m.luminosite, m.co2_ppm, m.nh3_ppm,
            m.niveau_eau, m.presence, m.nb_poules,
            m.nb_ampoules_allumees,
        ])

    return response