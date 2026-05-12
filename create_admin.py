# create_admin.py

import os
import sys

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'manichick.settings')
django.setup()

try:
    from utilisateurs.models import Utilisateur

    if not Utilisateur.objects.filter(username='admin').exists():
        u = Utilisateur.objects.create_superuser(
            username='admin',
            email='admin@manichick.com',
            password='admin1234',
        )
        u.role = 'admin'
        u.valide = True
        u.is_active = True
        u.save()
        print('✅ Admin créé avec succès')
    else:
        # Met à jour l'admin existant pour s'assurer qu'il est validé.
        u = Utilisateur.objects.get(username='admin')
        u.valide = True
        u.is_active = True
        u.role = 'admin'
        u.set_password('admin1234')
        u.save()
        print('✅ Admin mis à jour')

except Exception as e:
    print(f'❌ Erreur création admin : {e}')
    sys.exit(1)
