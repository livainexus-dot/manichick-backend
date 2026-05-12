# capteurs/ia_engine.py

import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression

# ════════════════════════════════════════════════════════
# NIVEAU 1 — DÉTECTION D'ANOMALIES PAR Z-SCORE
# ════════════════════════════════════════════════════════

def detecter_anomalie_zscore(valeurs_historiques: list, nouvelle_valeur: float) -> dict:
    """
    Détecte si une nouvelle valeur est statistiquement anormale
    par rapport à l'historique récent.

    Le Z-score mesure combien d'écarts-types sépare la nouvelle valeur
    de la moyenne historique.

    Formule : Z = (valeur - moyenne) / écart_type

    Z > 2  = anomalie modérée  (valeur inhabituelle)
    Z > 3  = anomalie sévère   (valeur très inhabituelle)
    """
    # Besoin d'au moins 10 valeurs pour un calcul statistique fiable
    if len(valeurs_historiques) < 10:
        return {'anomalie': False, 'zscore': 0, 'niveau': 'insuffisant'}

    tableau = np.array(valeurs_historiques)
    moyenne  = np.mean(tableau)
    ecart_type = np.std(tableau)

    # Si toutes les valeurs sont identiques → pas d'anomalie possible
    if ecart_type == 0:
        return {'anomalie': False, 'zscore': 0, 'niveau': 'stable'}

    # Calcul du Z-score
    zscore = abs((nouvelle_valeur - moyenne) / ecart_type)

    if zscore > 3:
        niveau = 'severe'
        anomalie = True
    elif zscore > 2:
        niveau = 'moderee'
        anomalie = True
    else:
        niveau = 'normal'
        anomalie = False

    return {
        'anomalie':  anomalie,
        'zscore':    round(zscore, 2),
        'niveau':    niveau,
        'moyenne':   round(float(moyenne), 2),
        'ecart_type': round(float(ecart_type), 2),
    }


# ════════════════════════════════════════════════════════
# NIVEAU 2 — PRÉDICTION PAR RÉGRESSION LINÉAIRE
# ════════════════════════════════════════════════════════

def predire_valeur(valeurs_recentes: list, horizon: int = 6) -> dict:
    """
    Prédit la valeur future par régression linéaire simple.

    horizon = nombre de pas dans le futur à prédire
    Si on envoie une mesure toutes les 5s, horizon=6 = prédiction dans 30s.
    Pour prédire dans 15 min avec mesures toutes les 5s : horizon=180

    La régression linéaire trouve la droite qui s'adapte le mieux
    aux données passées, puis l'extrapole vers le futur.
    """
    if len(valeurs_recentes) < 5:
        return {'prediction': None, 'tendance': 'insuffisant'}

    # X = indices de temps (0, 1, 2, 3...)
    # Y = valeurs mesurées
    X = np.arange(len(valeurs_recentes)).reshape(-1, 1)
    Y = np.array(valeurs_recentes)

    modele = LinearRegression()
    modele.fit(X, Y)

    # Prédit la valeur à l'index futur
    index_futur = np.array([[len(valeurs_recentes) + horizon]])
    prediction  = modele.predict(index_futur)[0]

    # La pente (slope) indique la tendance
    pente = modele.coef_[0]
    if pente > 0.1:
        tendance = 'hausse'
    elif pente < -0.1:
        tendance = 'baisse'
    else:
        tendance = 'stable'

    return {
        'prediction': round(float(prediction), 2),
        'tendance':   tendance,
        'pente':      round(float(pente), 4),
    }


# ════════════════════════════════════════════════════════
# NIVEAU 3 — SEUILS ADAPTATIFS
# ════════════════════════════════════════════════════════

def calculer_seuils_adaptatifs(valeurs_historiques: list) -> dict:
    """
    Calcule des seuils d'alerte personnalisés basés sur
    l'historique réel du poulailler.

    Au lieu d'utiliser des seuils fixes (ex: toujours 35°C),
    on calcule des seuils basés sur la distribution statistique
    des valeurs observées dans CE poulailler spécifique.

    Seuil avertissement = moyenne + 1.5 * écart_type
    Seuil critique      = moyenne + 2.5 * écart_type

    Ainsi si un poulailler est naturellement plus chaud,
    les alertes s'adaptent à sa réalité.
    """
    if len(valeurs_historiques) < 20:
        # Pas assez de données → on retourne les seuils fixes par défaut
        return {
            'adaptatif': False,
            'seuil_avertissement': None,
            'seuil_critique': None,
        }

    tableau    = np.array(valeurs_historiques)
    moyenne    = np.mean(tableau)
    ecart_type = np.std(tableau)

    seuil_avert   = moyenne + (1.5 * ecart_type)
    seuil_critique = moyenne + (2.5 * ecart_type)

    return {
        'adaptatif':           True,
        'moyenne':             round(float(moyenne), 2),
        'ecart_type':          round(float(ecart_type), 2),
        'seuil_avertissement': round(float(seuil_avert), 2),
        'seuil_critique':      round(float(seuil_critique), 2),
    }