# manichick/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/',            admin.site.urls),
    path('api/capteurs/',     include('capteurs.urls')),
    path('api/actionneurs/',  include('actionneurs.urls')),
    path('api/alertes/',      include('alertes.urls')),
    path('api/auth/',         include('utilisateurs.urls')),
    path('api/suivi/',        include('suivi_poules.urls')),
    path('api/lots/',         include('lots_poulets.urls')),  # ← nouveau
    path('api/finances/',     include('finances.urls')),
]