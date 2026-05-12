# lots_poulets/models.py

from django.db import models
from django.utils import timezone

class Lot(models.Model):
    """
    Un lot = un groupe de poulets du même type et du même âge.
    Ex: "Lot A — 50 pondeuses — arrivées le 01/01/2026"
    """
    TYPE_CHOICES = [
        ('chair',    'Poulet de chair'),
        ('pondeuse', 'Pondeuse'),
        ('poussin',  'Poussin'),
    ]
    nom          = models.CharField(max_length=100)
    type_lot     = models.CharField(max_length=10, choices=TYPE_CHOICES)
    nb_sujets    = models.IntegerField()         # nombre initial de sujets
    date_arrivee = models.DateField()            # date d'entrée dans le poulailler
    actif        = models.BooleanField(default=True)
    notes        = models.TextField(blank=True, default='')

    # Pour les poulets de chair : date prévue d'abattage
    date_abattage_prevue = models.DateField(null=True, blank=True)

    # Pour les pondeuses : date début de ponte attendue
    date_ponte_prevue = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-date_arrivee']
        db_table = 'lots'

    @property
    def age_jours(self):
        """Calcule l'âge du lot en jours depuis l'arrivée."""
        return (timezone.now().date() - self.date_arrivee).days

    @property
    def age_semaines(self):
        """Calcule l'âge en semaines."""
        return self.age_jours // 7

    def __str__(self):
        return f"{self.nom} ({self.type_lot}) — {self.age_semaines} semaines"


class SuiviLot(models.Model):
    """
    Suivi hebdomadaire d'un lot : poids, mortalité, consommation.
    Une ligne = une semaine de suivi pour un lot donné.
    """
    lot          = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name='suivis')
    date         = models.DateField()
    semaine      = models.IntegerField()         # numéro de semaine depuis l'arrivée

    # Poids moyen observé en grammes
    poids_moyen_g    = models.FloatField(default=0)
    # Nombre de sujets vivants cette semaine
    nb_vivants        = models.IntegerField(default=0)
    # Mortalité de la semaine
    nb_morts_semaine  = models.IntegerField(default=0)
    # Consommation réelle nourriture en kg pour tout le lot
    nourriture_kg     = models.FloatField(default=0)
    # Consommation réelle eau en litres
    eau_litres        = models.FloatField(default=0)
    # Œufs collectés (pondeuses seulement)
    nb_oeufs          = models.IntegerField(default=0)
    notes             = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-date']
        db_table  = 'suivis_lots'
        unique_together = ['lot', 'semaine']  # une seule entrée par semaine/lot

    def __str__(self):
        return f"{self.lot.nom} — semaine {self.semaine} — {self.poids_moyen_g}g"


class VenteProduction(models.Model):
    """
    Enregistre les ventes et productions liées à un lot.
    """
    lot       = models.ForeignKey(Lot, on_delete=models.CASCADE, related_name='ventes')
    date      = models.DateField()

    TYPE_CHOICES = [
        ('oeufs',   'Vente d\'œufs'),
        ('poulets', 'Vente de poulets'),
        ('fumier',  'Vente de fumier'),
        ('autre',   'Autre'),
    ]
    type_vente   = models.CharField(max_length=10, choices=TYPE_CHOICES)
    quantite     = models.FloatField()           # kg pour poulets, nombre pour œufs
    prix_unitaire_fcfa = models.FloatField()     # prix par kg ou par œuf
    montant_fcfa = models.FloatField()           # montant total = quantite × prix_unitaire

    class Meta:
        ordering = ['-date']
        db_table  = 'ventes_production'

    def save(self, *args, **kwargs):
        # Calcule automatiquement le montant total avant sauvegarde
        self.montant_fcfa = self.quantite * self.prix_unitaire_fcfa
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.lot.nom} — {self.type_vente} — {self.montant_fcfa} FCFA"