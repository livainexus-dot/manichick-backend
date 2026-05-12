# utilisateurs/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models

class Utilisateur(AbstractUser):
    """
    Modèle utilisateur étendu avec rôles et statut de validation.
    Un employé doit être validé par l'admin avant de pouvoir se connecter.
    """
    ROLE_CHOICES = [
        ('admin',       'Administrateur'),    # accès total
        ('employe',     'Employé'),           # saisie + lecture
        ('superviseur', 'Superviseur'),       # lecture seule
    ]
    role = models.CharField(
        max_length=15,
        choices=ROLE_CHOICES,
        default='employe'
    )
    telephone  = models.CharField(max_length=20, blank=True, null=True)
    # Un compte créé par inscription est en attente de validation
    valide     = models.BooleanField(default=False)
    # Date de validation par l'admin
    valide_le  = models.DateTimeField(null=True, blank=True)
    # Admin qui a validé le compte
    valide_par = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='comptes_valides',
    )
    # Photo de profil (optionnel)
    photo_url  = models.CharField(max_length=255, blank=True, null=True)
    # Dernière activité
    derniere_activite = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'utilisateurs'

    @property
    def nom_complet(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

    @property
    def peut_se_connecter(self):
        """Un utilisateur peut se connecter seulement s'il est validé OU admin."""
        return self.valide or self.is_superuser

    def __str__(self):
        return f"{self.username} ({self.role}) — {'validé' if self.valide else 'en attente'}"


class JournalActivite(models.Model):
    """
    Enregistre toutes les actions importantes des utilisateurs.
    Traçabilité complète : qui a fait quoi et quand.
    """
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        related_name='activites',
    )
    timestamp   = models.DateTimeField(auto_now_add=True)
    action      = models.CharField(max_length=100)  # ex: "login", "commande_ventilateur"
    details     = models.TextField(blank=True, default='')
    adresse_ip  = models.CharField(max_length=45, blank=True, null=True)

    class Meta:
        ordering  = ['-timestamp']
        db_table  = 'journal_activite'

    def __str__(self):
        return f"{self.utilisateur} — {self.action} — {self.timestamp}"