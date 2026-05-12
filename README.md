<<<<<<< HEAD
# 🐔 Manichick Backend - Système de Gestion de Poulailler

Bienvenue dans la partie serveur du projet **Manichick**. Ce projet permet de surveiller et de contrôler un poulailler intelligent via l'IoT et une application mobile.

## 🛠️ Architecture Technique
- **Backend :** Django 4.x / Python 3.11
- **Base de données :** PostgreSQL (avec système d'audit par Triggers)
- **Communication IoT :** Protocole MQTT via HiveMQ Cloud
- **OS de développement :** Kali Linux (`lambou@kali`)

## 📂 Structure des Livrables
Le dossier remis contient :
1.  **Code Source Backend** : Dossier `/manichick_backend/`
2.  **Code Source Mobile** : Dossier `/manichick_app/` (React Native/Expo)
3.  **Application Mobile** : Fichier `manichick.apk` (prêt à installer)
4.  **Base de données** : Script SQL complet avec procédures d'audit.

## 🚀 Installation Rapide
1. **Environnement virtuel :** `source venv/bin/activate`
2. **Dépendances :** `pip install -r requirements.txt`
3. **Migration DB :** `python manage.py migrate`
4. **Lancement :** `python manage.py runserver`

## 📋 Points clés du projet
- **Surveillance :** Réception en temps réel de la température, humidité et gaz.
- **Automatisation :** Gestion intelligente du ventilateur et de l'éclairage progressif.
- **Sécurité :** Détection d'intrusion par capteur PIR et alertes sonores.

---
**Développé par :** lambou (Étudiant PFE)
**Session :** Mai 2026
=======
# manichick-backend
>>>>>>> 1e6d6b6100dcab837652a4a7164f17a0a82d6d98
