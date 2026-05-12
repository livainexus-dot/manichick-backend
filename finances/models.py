# finances/models.py

from django.db import models
from utilisateurs.models import Utilisateur

class CategoriDepense(models.Model):
    """Catégories de dépenses personnalisables."""
    nom         = models.CharField(max_length=50)
    icone       = models.CharField(max_length=30, default='cash')
    couleur_hex = models.CharField(max_length=7, default='#6B7280')

    class Meta:
        db_table = 'categories_depenses'

    def __str__(self):
        return self.nom


class Depense(models.Model):
    """
    Enregistre chaque dépense du poulailler.
    Ex: achat nourriture, médicaments, électricité, main-d'œuvre.
    """
    date        = models.DateField()
    categorie   = models.ForeignKey(
        CategoriDepense,
        on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    description = models.CharField(max_length=255)
    montant_fcfa = models.FloatField()
    # Lot concerné (optionnel — dépense peut être globale)
    lot         = models.ForeignKey(
        'lots_poulets.Lot',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='depenses',
    )
    saisie_par  = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    notes       = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-date']
        db_table = 'depenses'

    def __str__(self):
        return f"{self.description} — {self.montant_fcfa} FCFA"


class Revenu(models.Model):
    """
    Enregistre chaque revenu du poulailler.
    Ex: vente d'œufs, vente de poulets, fumier.
    """
    date        = models.DateField()

    TYPE_CHOICES = [
        ('oeufs',   'Vente d\'œufs'),
        ('poulets', 'Vente de poulets vivants'),
        ('viande',  'Vente de viande'),
        ('fumier',  'Vente de fumier'),
        ('autre',   'Autre'),
    ]
    type_revenu      = models.CharField(max_length=10, choices=TYPE_CHOICES)
    description      = models.CharField(max_length=255)
    quantite         = models.FloatField(default=1)
    prix_unitaire_fcfa = models.FloatField()
    montant_fcfa     = models.FloatField()

    lot = models.ForeignKey(
        'lots_poulets.Lot',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='revenus',
    )
    saisie_par = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    notes = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-date']
        db_table = 'revenus'

    def save(self, *args, **kwargs):
        self.montant_fcfa = self.quantite * self.prix_unitaire_fcfa
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.type_revenu} — {self.montant_fcfa} FCFA"


class BudgetMensuel(models.Model):
    """
    Budget prévisionnel mensuel.
    Permet de comparer prévu vs réalisé.
    """
    annee   = models.IntegerField()
    mois    = models.IntegerField()  # 1-12
    budget_depenses_fcfa = models.FloatField(default=0)
    budget_revenus_fcfa  = models.FloatField(default=0)
    notes   = models.TextField(blank=True, default='')

    class Meta:
        db_table       = 'budgets_mensuels'
        unique_together = ['annee', 'mois']

    def __str__(self):
        return f"Budget {self.mois}/{self.annee}"