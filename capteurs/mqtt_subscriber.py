# capteurs/mqtt_subscriber.py

import json
import django
import os
import sys

sys.path.insert(0, '/home/lambou/manichick_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'manichick.settings')
django.setup()

import paho.mqtt.client as mqtt
from capteurs.models import Mesure, PhotoIntrusion
from actionneurs.models import EtatActionneur
from capteurs.views import verifier_et_creer_alertes

# ── Configuration HiveMQ ─────────────────────────────────
MQTT_HOST     = 'a84dc66da43049539e20a61d594aa217.s1.eu.hivemq.cloud'   # ← remplace
MQTT_PORT     = 8883
MQTT_USERNAME = 'lambou'             # ← remplace
MQTT_PASSWORD = 'Admin1234'             # ← remplace

TOPIC_CAPTEURS  = 'manichick/capteurs'
TOPIC_STATUS    = 'manichick/status'
TOPIC_CAMERA    = 'manichick/camera'


def on_connect(client, userdata, flags, reason_code, properties):
    if not reason_code.is_failure:
        print("✅ Subscriber connecté à HiveMQ Cloud")
        client.subscribe(TOPIC_CAPTEURS)
        client.subscribe(TOPIC_STATUS)
        client.subscribe(TOPIC_CAMERA)
        print(f"📡 Abonné à : {TOPIC_CAPTEURS}, {TOPIC_STATUS}, {TOPIC_CAMERA}")
    else:
        print(f"❌ Connexion échouée : {reason_code}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        print(f"📩 [{msg.topic}] : {str(payload)[:80]}...")

        if msg.topic == TOPIC_CAPTEURS:
            traiter_mesure(payload)
        elif msg.topic == TOPIC_STATUS:
            traiter_actionneurs(payload)
        elif msg.topic == TOPIC_CAMERA:
            traiter_photo_intrusion(payload)

    except json.JSONDecodeError:
        print(f"⚠️ JSON invalide : {msg.payload}")
    except Exception as e:
        print(f"❌ Erreur : {e}")


def traiter_mesure(payload: dict):
    """Crée une mesure en base et vérifie les alertes."""
    mesure = Mesure.objects.create(
        temperature          = payload.get('temperature',          0),
        humidite             = payload.get('humidite',             0),
        gaz_ppm              = payload.get('gaz_ppm',              0),
        luminosite           = payload.get('luminosite',           0),
        co2_ppm              = payload.get('co2_ppm',              400),
        nh3_ppm              = payload.get('nh3_ppm',              0),
        niveau_eau           = payload.get('niveau_eau',           100),
        presence             = payload.get('presence',             False),
        nb_poules            = payload.get('nb_poules',            0),
        nb_ampoules_allumees = payload.get('nb_ampoules_allumees', 6),
    )
    print(f"💾 Mesure sauvegardée : T°={mesure.temperature}°C — lux={mesure.luminosite}")
    verifier_et_creer_alertes(mesure)


def traiter_actionneurs(payload: dict):
    """Met à jour l'état des actionneurs en base."""
    EtatActionneur.objects.create(
        ventilateur    = payload.get('ventilateur',    False),
        distributeur   = payload.get('distributeur',   False),
        sirene         = payload.get('sirene',         False),
        ampoule_1      = payload.get('ampoule_1',      True),
        ampoule_2      = payload.get('ampoule_2',      True),
        ampoule_3      = payload.get('ampoule_3',      True),
        ampoule_4      = payload.get('ampoule_4',      True),
        ampoule_5      = payload.get('ampoule_5',      True),
        ampoule_6      = payload.get('ampoule_6',      True),
        mode_eclairage = payload.get('mode_eclairage', 'auto'),
        source         = 'mqtt',
    )
    print(f"⚡ Actionneurs mis à jour depuis Wokwi")


def traiter_photo_intrusion(payload: dict):
    """Enregistre une photo d'intrusion simulée."""
    PhotoIntrusion.objects.create(
        description  = payload.get('description', 'Intrusion détectée'),
        zone         = payload.get('zone',        'Zone principale'),
        image_base64 = payload.get('image_base64', ''),
    )
    print(f"📸 Photo intrusion enregistrée")


def demarrer():
    client = mqtt.Client(
        callback_api_version = mqtt.CallbackAPIVersion.VERSION2,
        client_id            = "manichick_django_subscriber_v2",
    )
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.tls_set()
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"🔄 Connexion à {MQTT_HOST}:{MQTT_PORT}...")
    try:
        client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n🛑 Subscriber arrêté")
        client.disconnect()
    except Exception as e:
        print(f"❌ Erreur : {e}")


if __name__ == '__main__':
    demarrer()