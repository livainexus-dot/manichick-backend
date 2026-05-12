# suivi_poules/models.py

from django.db import models

class SuiviJournalier(models.Model):
    """
    Enregistre les données de suivi saisies manuellement
    par l'éleveur chaque jour.
    Une ligne = un jour dans le poulailler.
    """
    date         = models.DateField(unique=True)
    # ── Mortalité ───────────────────────────────────────
    # Nombre de poules trouvées mortes ce jour
    nb_morts     = models.IntegerField(default=0)
    # Nombre total de poules vivantes en fin de journée
    nb_vivantes  = models.IntegerField(default=0)
    # ── Ponte ───────────────────────────────────────────
    nb_oeufs     = models.IntegerField(default=0)
    # ── Alimentation ────────────────────────────────────
    # Quantité de nourriture consommée en kilogrammes
    nourriture_kg = models.FloatField(default=0.0)
    # Quantité d'eau consommée en litres
    eau_litres    = models.FloatField(default=0.0)
    # ── Notes libres ────────────────────────────────────
    notes         = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-date']
        db_table = 'suivi_journalier'

    def __str__(self):
        return f"Suivi {self.date} — {self.nb_oeufs} œufs, {self.nb_morts} morts"


class EntreeVeterinaire(models.Model):
    """
    Journal vétérinaire : vaccins, traitements, observations médicales.
    Une ligne = un événement vétérinaire.
    """
    date        = models.DateField()

    TYPE_CHOICES = [
        ('vaccin',      'Vaccination'),
        ('traitement',  'Traitement médical'),
        ('observation', 'Observation'),
        ('visite',      'Visite vétérinaire'),
    ]
    type_entree  = models.CharField(max_length=20, choices=TYPE_CHOICES)
    titre        = models.CharField(max_length=100)
    description  = models.TextField()
    # Nombre de poules concernées par cet événement
    nb_poules_concernees = models.IntegerField(default=0)
    # Coût en FCFA (optionnel)
    cout_fcfa    = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['-date']
        db_table = 'entrees_veterinaires'

    def __str__(self):
        return f"[{self.type_entree}] {self.titre} — {self.date}"