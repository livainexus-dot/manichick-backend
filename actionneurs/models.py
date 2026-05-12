# actionneurs/models.py — version complète mise à jour

from django.db import models

class EtatActionneur(models.Model):
    timestamp    = models.DateTimeField(auto_now_add=True)
    # ── Actionneurs existants ────────────────────────────
    ventilateur  = models.BooleanField(default=False)
    distributeur = models.BooleanField(default=False)
    sirene       = models.BooleanField(default=False)
    # ── Éclairage intelligent ────────────────────────────
    # Chaque ampoule est contrôlée individuellement
    ampoule_1    = models.BooleanField(default=True)
    ampoule_2    = models.BooleanField(default=True)
    ampoule_3    = models.BooleanField(default=True)
    ampoule_4    = models.BooleanField(default=True)
    ampoule_5    = models.BooleanField(default=True)
    ampoule_6    = models.BooleanField(default=True)
    # ── Mode éclairage ───────────────────────────────────
    MODE_CHOICES = [
        ('auto', 'Automatique — LDR'),
        ('manuel', 'Manuel'),
        ('nuit', 'Mode nuit — toutes éteintes'),
        ('jour', 'Mode jour — toutes allumées'),
    ]
    mode_eclairage = models.CharField(
        max_length=10,
        choices=MODE_CHOICES,
        default='auto'
    )

    SOURCE_CHOICES = [
        ('auto', 'Automatique'),
        ('manuel', 'Manuel'),
        ('mqtt', 'MQTT'),
        ('ia', 'Intelligence artificielle'),
    ]
    source = models.CharField(
        max_length=10,
        choices=SOURCE_CHOICES,
        default='auto'
    )

    class Meta:
        ordering = ['-timestamp']
        db_table = 'actionneurs'

    @property
    def nb_ampoules_allumees(self):
        """Compte combien d'ampoules sont allumées."""
        ampoules = [
            self.ampoule_1, self.ampoule_2, self.ampoule_3,
            self.ampoule_4, self.ampoule_5, self.ampoule_6,
        ]
        return sum(ampoules)

    def __str__(self):
        return f"Actionneurs {self.timestamp} — {self.nb_ampoules_allumees}/6 ampoules"


class CommandeManuelle(models.Model):
    timestamp   = models.DateTimeField(auto_now_add=True)
    actionneur  = models.CharField(max_length=30)
    etat        = models.BooleanField()
    utilisateur = models.ForeignKey(
        'utilisateurs.Utilisateur',
        on_delete=models.SET_NULL,
        null=True, blank=True,
    )

    class Meta:
        ordering = ['-timestamp']
        db_table = 'commandes_manuelles'