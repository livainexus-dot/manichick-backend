# create_admin.py
# Script exécuté automatiquement au démarrage pour créer l'admin

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'manichick.settings')
django.setup()

from utilisateurs.models import Utilisateur

# Crée l'admin seulement s'il n'existe pas déjà
if not Utilisateur.objects.filter(username='admin').exists():
    Utilisateur.objects.create_superuser(
        username  = 'admin',
        email     = 'admin@manichick.com',
        password  = 'admin1234',
        role      = 'admin',
        valide    = True,
        is_active = True,
    )
    print('✅ Admin créé : admin / admin1234')
else:
    print('ℹ️ Admin existe déjà')