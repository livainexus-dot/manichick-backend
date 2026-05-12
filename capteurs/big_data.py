# capteurs/big_data.py

"""
Module Big Data Manichick.
Calcule des agrégations sur les séries temporelles IoT
stockées dans PostgreSQL.

Volume typique : ~500 000 mesures/mois
Stratégie : agrégations SQL côté base de données
(jamais charger tout en mémoire).
"""

from django.db.models import Avg, Max, Min, Count, StdDev
from django.db.models.functions import TruncHour, TruncDay, TruncWeek
from django.utils import timezone
import datetime


def agregation_par_periode(modele_mesure, champ: str, periode: str, nb_jours: int):
    """
    Agrège un champ de mesure par heure/jour/semaine.

    C'est le cœur du Big Data : au lieu de renvoyer
    500 000 lignes brutes, on calcule des statistiques
    agrégées directement dans PostgreSQL.

    Args:
        modele_mesure : le modèle Django Mesure
        champ         : 'temperature', 'humidite', etc.
        periode       : 'heure', 'jour', 'semaine'
        nb_jours      : fenêtre temporelle

    Returns:
        liste de dicts avec moy, min, max par période
    """
    depuis = timezone.now() - datetime.timedelta(days=nb_jours)

    trunc_fn = {
        'heure':   TruncHour,
        'jour':    TruncDay,
        'semaine': TruncWeek,
    }.get(periode, TruncDay)

    return list(
        modele_mesure.objects
        .filter(timestamp__gte=depuis)
        .annotate(periode=trunc_fn('timestamp'))
        .values('periode')
        .annotate(
            moy   = Avg(champ),
            min   = Min(champ),
            max   = Max(champ),
            count = Count('id'),
            ecart = StdDev(champ),
        )
        .order_by('periode')
    )


def stats_globales(modele_mesure, nb_jours: int = 30) -> dict:
    """
    Calcule les statistiques globales sur une période.
    Utilisé pour le rapport hebdomadaire et le Big Data dashboard.
    """
    depuis = timezone.now() - datetime.timedelta(days=nb_jours)
    qs     = modele_mesure.objects.filter(timestamp__gte=depuis)

    total = qs.count()
    if total == 0:
        return {'erreur': 'Aucune donnée disponible'}

    stats = qs.aggregate(
        temp_moy  = Avg('temperature'),
        temp_max  = Max('temperature'),
        temp_min  = Min('temperature'),
        hum_moy   = Avg('humidite'),
        gaz_moy   = Avg('gaz_ppm'),
        gaz_max   = Max('gaz_ppm'),
        eau_moy   = Avg('niveau_eau'),
        eau_min   = Min('niveau_eau'),
        nb_mesures = Count('id'),
    )

    # Compte les alertes sur la période
    from alertes.models import Alerte
    nb_alertes = Alerte.objects.filter(
        timestamp__gte=depuis
    ).count()

    nb_critiques = Alerte.objects.filter(
        timestamp__gte=depuis,
        gravite='critique',
    ).count()

    return {
        **{k: round(v, 2) if v else 0 for k, v in stats.items()},
        'nb_alertes':   nb_alertes,
        'nb_critiques': nb_critiques,
        'periode_jours': nb_jours,
    }


def detecter_patterns(modele_mesure) -> dict:
    """
    Détecte les patterns (schémas répétitifs) dans les données.
    Ex: température toujours haute entre 13h et 16h.

    C'est la valeur ajoutée Big Data : identifier les tendances
    récurrentes pour anticiper et optimiser.
    """
    # Agrégation par heure de la journée sur 7 jours
    sept_jours = timezone.now() - datetime.timedelta(days=7)

    par_heure = list(
        modele_mesure.objects
        .filter(timestamp__gte=sept_jours)
        .annotate(heure=TruncHour('timestamp'))
        .values('heure__hour')
        .annotate(
            temp_moy = Avg('temperature'),
            gaz_moy  = Avg('gaz_ppm'),
        )
        .order_by('heure__hour')
    )

    # Identifie les heures critiques
    heures_chaudes = [
        p for p in par_heure
        if p['temp_moy'] and p['temp_moy'] > 33
    ]
    heures_gaz = [
        p for p in par_heure
        if p['gaz_moy'] and p['gaz_moy'] > 200
    ]

    return {
        'par_heure':      par_heure,
        'heures_chaudes': heures_chaudes,
        'heures_gaz':     heures_gaz,
        'pattern_chaleur': (
            f"Chaleur récurrente entre {heures_chaudes[0]['heure__hour']}h "
            f"et {heures_chaudes[-1]['heure__hour']}h"
            if heures_chaudes else None
        ),
    }