# capteurs/management/commands/lancer_ia.py

import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from capteurs.models import Mesure
from alertes.models import Alerte
from capteurs.ia_engine import (
    detecter_anomalie_zscore,
    predire_valeur,
    calculer_seuils_adaptatifs,
)

# Seuils fixes de référence (utilisés si pas assez de données historiques)
SEUILS_FIXES = {
    'temperature': {'avertissement': 32, 'critique': 35},
    'humidite':    {'avertissement': 80, 'critique': 90},
    'gaz_ppm':     {'avertissement': 200, 'critique': 300},
    'niveau_eau':  {'avertissement': 30, 'critique': 20},
}

class Command(BaseCommand):
    # Description affichée avec python manage.py help lancer_ia
    help = 'Lance le moteur IA Manichick en arrière-plan'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(
            '🤖 Moteur IA Manichick démarré — analyse toutes les 30 secondes'
        ))

        # Boucle infinie — s'arrête avec Ctrl+C
        while True:
            try:
                self.analyser()
            except KeyboardInterrupt:
                self.stdout.write('\n🛑 Moteur IA arrêté')
                break
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Erreur IA : {e}'))

            # Attend 30 secondes avant la prochaine analyse
            time.sleep(30)

    def analyser(self):
        """
        Analyse les 50 dernières mesures et crée des alertes IA si nécessaire.
        """
        # Récupère les 50 dernières mesures (les plus récentes en premier)
        mesures = list(Mesure.objects.all()[:50])

        if len(mesures) < 5:
            self.stdout.write('⏳ Pas assez de données pour l\'analyse IA')
            return

        # Inverse pour avoir les plus anciennes en premier
        # (nécessaire pour la régression linéaire qui attend un ordre chronologique)
        mesures_chrono = list(reversed(mesures))

        # Extrait les séries temporelles pour chaque métrique
        temperatures = [m.temperature for m in mesures_chrono]
        humidites    = [m.humidite    for m in mesures_chrono]
        gaz          = [m.gaz_ppm     for m in mesures_chrono]
        niveaux_eau  = [m.niveau_eau  for m in mesures_chrono]

        derniere = mesures_chrono[-1]  # mesure la plus récente

        self.stdout.write(f'🔍 Analyse IA — {len(mesures)} mesures — T°={derniere.temperature}°C')

        # ── Analyse température ──────────────────────────
        self.analyser_metrique(
            valeurs        = temperatures,
            derniere_valeur = derniere.temperature,
            nom_metrique   = 'temperature',
            unite          = '°C',
            type_alerte    = 'CHALEUR',
        )

        # ── Analyse humidité ─────────────────────────────
        self.analyser_metrique(
            valeurs        = humidites,
            derniere_valeur = derniere.humidite,
            nom_metrique   = 'humidite',
            unite          = '%',
            type_alerte    = 'HUMIDITE',
        )

        # ── Analyse gaz ──────────────────────────────────
        self.analyser_metrique(
            valeurs        = gaz,
            derniere_valeur = derniere.gaz_ppm,
            nom_metrique   = 'gaz_ppm',
            unite          = ' ppm',
            type_alerte    = 'GAZ',
        )

        # ── Prédiction température dans ~15 min ──────────
        # horizon=180 car mesure toutes les 5s → 180 * 5s = 900s = 15 min
        prediction = predire_valeur(temperatures, horizon=180)

        if prediction['prediction'] is not None:
            self.stdout.write(
                f'🔮 Prédiction T° dans 15min : {prediction["prediction"]}°C '
                f'(tendance : {prediction["tendance"]})'
            )

            # Si la prédiction dépasse le seuil critique → alerte préventive
            if prediction['prediction'] > 35 and prediction['tendance'] == 'hausse':
                # Vérifie qu'on n'a pas déjà créé cette alerte récemment
                # (dans les 5 dernières minutes)
                cinq_min = timezone.now() - timezone.timedelta(minutes=5)
                existe = Alerte.objects.filter(
                    type_alerte='PREDICTION_CHALEUR',
                    timestamp__gte=cinq_min,
                    acquittee=False,
                ).exists()

                if not existe:
                    Alerte.objects.create(
                        type_alerte = 'PREDICTION_CHALEUR',
                        message     = (
                            f'⚠️ IA prédit T°={prediction["prediction"]}°C '
                            f'dans 15 min — action préventive recommandée'
                        ),
                        valeur  = prediction['prediction'],
                        seuil   = 35,
                        gravite = 'avertissement',
                    )
                    self.stdout.write(self.style.WARNING(
                        f'🚨 Alerte prédictive créée : T° prévue {prediction["prediction"]}°C'
                    ))

    def analyser_metrique(
        self,
        valeurs: list,
        derniere_valeur: float,
        nom_metrique: str,
        unite: str,
        type_alerte: str,
    ):
        """
        Analyse une métrique avec Z-score + seuils adaptatifs.
        Crée une alerte IA si anomalie détectée.
        """
        # ── Z-score ──────────────────────────────────────
        resultat_z = detecter_anomalie_zscore(valeurs[:-1], derniere_valeur)

        if resultat_z['anomalie']:
            self.stdout.write(
                f'⚠️ Anomalie {nom_metrique} : Z={resultat_z["zscore"]} '
                f'({resultat_z["niveau"]}) — valeur={derniere_valeur}{unite}'
            )

            # Évite les doublons : pas d'alerte si une même existe < 5 min
            cinq_min = timezone.now() - timezone.timedelta(minutes=5)
            type_ia  = f'IA_{type_alerte}'
            existe   = Alerte.objects.filter(
                type_alerte=type_ia,
                timestamp__gte=cinq_min,
                acquittee=False,
            ).exists()

            if not existe:
                gravite = 'critique' if resultat_z['niveau'] == 'severe' else 'avertissement'
                Alerte.objects.create(
                    type_alerte = type_ia,
                    message     = (
                        f'IA détecte anomalie {nom_metrique} : '
                        f'{derniere_valeur}{unite} '
                        f'(Z-score={resultat_z["zscore"]}, '
                        f'moy={resultat_z["moyenne"]}{unite})'
                    ),
                    valeur  = derniere_valeur,
                    seuil   = resultat_z['moyenne'],
                    gravite = gravite,
                )

        # ── Seuils adaptatifs ────────────────────────────
        seuils = calculer_seuils_adaptatifs(valeurs)

        if seuils['adaptatif']:
            seuil_crit = seuils['seuil_critique']
            if derniere_valeur > seuil_crit:
                self.stdout.write(
                    f'📊 Seuil adaptatif {nom_metrique} dépassé : '
                    f'{derniere_valeur}{unite} > {seuil_crit}{unite}'
                )