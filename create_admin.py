# create_admin.py

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'manichick.settings')
django.setup()

print(f"🔍 DATABASE connectée : {os.environ.get('DATABASE_URL', 'NON TROUVÉE')[:30]}...")

try:
    from utilisateurs.models import Utilisateur

    print(f"👥 Nombre d'utilisateurs en base : {Utilisateur.objects.count()}")

    if not Utilisateur.objects.filter(username='admin').exists():
        u = Utilisateur(
            username     = 'admin',
            email        = 'admin@manichick.com',
            is_superuser = True,
            is_staff     = True,
            is_active    = True,
            valide       = True,
            role         = 'admin',
        )
        u.set_password('admin1234')
        u.save()
        print('✅ Admin créé : admin / admin1234')
    else:
        u = Utilisateur.objects.get(username='admin')
        u.valide    = True
        u.is_active = True
        u.is_staff  = True
        u.is_superuser = True
        u.role      = 'admin'
        u.set_password('admin1234')
        u.save()
        print('✅ Admin mis à jour : admin / admin1234')

    print(f"👥 Total utilisateurs après : {Utilisateur.objects.count()}")

except Exception as e:
    print(f'❌ Erreur : {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)