# utilisateurs/urls.py

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Auth
    path('login/',              views.ManichickLoginView.as_view(), name='login'),
    path('token/refresh/',      TokenRefreshView.as_view(),         name='token-refresh'),
    path('inscription/',        views.inscription,                  name='inscription'),

    # Profil
    path('profil/',             views.profil,                       name='profil'),
    path('profil/modifier/',    views.modifier_profil,              name='profil-modifier'),

    # Admin
    path('employes/',                           views.liste_employes,  name='employes-liste'),
    path('employes/<int:user_id>/valider/',     views.valider_compte,  name='compte-valider'),
    path('journal/',                            views.journal_activite,name='journal'),
]