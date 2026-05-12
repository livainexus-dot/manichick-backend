# alertes/models.py

from django.db import models

class Alerte(models.Model):
    """
    Enregistre chaque alerte déclenchée par le système.
    Une alerte = un seuil dépassé détecté par l'IA ou l'ESP32.
    """
    timestamp = models.DateTimeField(auto_now_add=True)

    TYPE_CHOICES = [
        ('CHALEUR', 'Chaleur excessive'),
        ('GAZ', 'Gaz dangereux'),
        ('HUMIDITE', 'Humidité anormale'),
        ('LUMINOSITE', 'Luminosité insuffisante'),
        ('EAU', 'Niveau eau faible'),
        ('INTRUSION', 'Intrusion détectée'),
        ('CO2', 'CO2 élevé'),
        ('NH3', 'Ammoniac élevé'),
        ('PREDICTION_CHALEUR', 'Prédiction chaleur IA'),
        ('IA_CHALEUR', 'Anomalie chaleur IA'),
        ('IA_HUMIDITE', 'Anomalie humidité IA'),
        ('IA_GAZ', 'Anomalie gaz IA'),
    ]
    type_alerte = models.CharField(max_length=20, choices=TYPE_CHOICES)
    message     = models.CharField(max_length=255)
    valeur      = models.FloatField()   # valeur mesurée au moment de l'alerte
    seuil       = models.FloatField()   # seuil qui a été dépassé

    GRAVITE_CHOICES = [
        ('critique', 'Critique'),
        ('avertissement', 'Avertissement'),
    ]
    gravite   = models.CharField(max_length=15, choices=GRAVITE_CHOICES)
    acquittee = models.BooleanField(default=False)

    # Qui a acquitté l'alerte (null si pas encore acquittée)
    acquittee_par = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    acquittee_le = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']
        db_table = 'alertes'

    def __str__(self):
        return f"[{self.gravite.upper()}] {self.type_alerte} — {self.valeur}"
