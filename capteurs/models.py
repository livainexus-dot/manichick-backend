# capteurs/models.py — version complète mise à jour

from django.db import models

class Mesure(models.Model):
    timestamp    = models.DateTimeField(auto_now_add=True)
    # ── Capteurs environnementaux ────────────────────────
    temperature  = models.FloatField()
    humidite     = models.FloatField()
    gaz_ppm      = models.IntegerField()
    luminosite   = models.IntegerField()
    # ── Nouveaux capteurs qualité air ────────────────────
    co2_ppm      = models.IntegerField(default=400)   # CO2 en ppm
    nh3_ppm      = models.FloatField(default=0.0)     # Ammoniac dédié
    # ── Capteurs existants ───────────────────────────────
    niveau_eau   = models.FloatField(default=100.0)
    presence     = models.BooleanField(default=False)
    nb_poules    = models.IntegerField(default=0)
    # ── Éclairage ────────────────────────────────────────
    # Nombre d'ampoules actuellement allumées (0 à 6)
    nb_ampoules_allumees = models.IntegerField(default=6)
    # ── Caméra ───────────────────────────────────────────
    # URL de la photo prise si intrusion (None = pas de photo)
    photo_intrusion_url  = models.CharField(
        max_length=255, null=True, blank=True
    )

    class Meta:
        ordering = ['-timestamp']
        db_table = 'mesures'

    def __str__(self):
        return f"Mesure {self.timestamp} — {self.temperature}°C"


class PhotoIntrusion(models.Model):
    """
    Stocke les photos prises automatiquement lors d'une intrusion.
    En simulation : on stocke des métadonnées + image base64 simulée.
    """
    timestamp   = models.DateTimeField(auto_now_add=True)
    # Image encodée en base64 (simulée dans Wokwi, réelle avec ESP32-CAM)
    image_base64 = models.TextField(blank=True, default='')
    # Description automatique générée
    description = models.CharField(max_length=255, default='Intrusion détectée')
    # Localisation dans le poulailler (ex: "Zone nord", "Entrée principale")
    zone        = models.CharField(max_length=50, default='Zone principale')
    acquittee   = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']
        db_table = 'photos_intrusion'

    def __str__(self):
        return f"Photo intrusion {self.timestamp}"