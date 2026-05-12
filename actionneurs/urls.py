# actionneurs/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('etat/', views.EtatActionneurDernierView.as_view(), name='etat-actionneurs'),
    path('commande/', views.envoyer_commande, name='commande'),
]