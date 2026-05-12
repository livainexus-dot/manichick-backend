#!/bin/bash
set -e
echo "📦 Installation des dépendances..."
pip install -r requirements.txt

echo "📁 Fichiers statiques..."
python manage.py collectstatic --noinput

echo "🗄️ Migrations..."
python manage.py migrate

echo "👤 Création admin..."
python create_admin.py

echo "✅ Build terminé !"
