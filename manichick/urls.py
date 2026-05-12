# manichick/urls.py

from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include

def accueil(request):
    """Page d'accueil de l'API Manichick."""
    return JsonResponse({
        'projet': 'Manichick — Ferme Connectée IoT',
        'version': '2.0',
        'statut': '✅ API opérationnelle',
        'endpoints': {
            'admin': '/admin/',
            'capteurs': '/api/capteurs/',
            'actionneurs': '/api/actionneurs/',
            'alertes': '/api/alertes/',
            'auth': '/api/auth/',
            'suivi': '/api/suivi/',
            'lots': '/api/lots/',
            'finances': '/api/finances/',
        },
        'documentation': 'Voir rapport technique',
    })

urlpatterns = [
    path('',                  accueil),
    path('admin/',            admin.site.urls),
    path('api/capteurs/',     include('capteurs.urls')),
    path('api/actionneurs/',  include('actionneurs.urls')),
    path('api/alertes/',      include('alertes.urls')),
    path('api/auth/',         include('utilisateurs.urls')),
    path('api/suivi/',        include('suivi_poules.urls')),
    path('api/lots/',         include('lots_poulets.urls')),  # ← nouveau
    path('api/finances/',     include('finances.urls')),
]
