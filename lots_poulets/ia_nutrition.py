# lots_poulets/ia_nutrition.py

"""
Tables de référence zootechniques pour la nutrition des volailles.
Sources : FAO, Institut Technique de l'Aviculture (ITAVI),
          Guides d'élevage Cameroun (MINEPIA).

Ces données sont des moyennes pour des conditions tropicales
similaires au Cameroun.
"""

import numpy as np
from sklearn.linear_model import LinearRegression

# ════════════════════════════════════════════════════════
# TABLES DE RÉFÉRENCE PAR TYPE DE VOLAILLE
# ════════════════════════════════════════════════════════

# Clé = semaine d'âge
# Valeur = (poids_attendu_g, nourriture_g_par_jour, eau_ml_par_jour)

TABLE_CHAIR = {
    1:  (100,   13,   30),
    2:  (200,   25,   55),
    3:  (400,   40,   85),
    4:  (650,   58,  120),
    5:  (900,   72,  155),
    6:  (1100,  84,  185),
    7:  (1400,  95,  210),
    8:  (1700, 105,  235),
    9:  (1950, 112,  250),
    10: (2100, 115,  260),
}
# Poulet de chair prêt à l'abattage : 6-8 semaines selon la race

TABLE_PONDEUSE = {
    1:  (70,    12,   25),
    2:  (140,   20,   45),
    3:  (220,   30,   65),
    4:  (320,   40,   85),
    5:  (430,   50,  100),
    6:  (550,   58,  115),
    7:  (680,   65,  128),
    8:  (820,   72,  140),
    12: (1100,  85,  170),
    16: (1350,  95,  190),
    20: (1500, 105,  200),   # début de ponte attendu
    24: (1600, 110,  210),   # ponte maximale
    40: (1700, 115,  215),   # ponte stable
    72: (1750, 110,  210),   # fin de vie productive
}

TABLE_POUSSIN = {
    1: (45,    8,   18),
    2: (95,   15,   32),
    3: (160,  22,   48),
    4: (240,  30,   62),
}
# Après 4 semaines, les poussins rejoignent la table pondeuse ou chair

# ── Température ambiante idéale par semaine ──────────────
TEMPERATURE_IDEALE = {
    1: 35,   # poussins très jeunes ont besoin de chaleur
    2: 32,
    3: 29,
    4: 26,
    5: 24,
    6: 22,
    8: 20,   # adultes : 18-22°C optimal
}

# ════════════════════════════════════════════════════════
# FONCTIONS IA NUTRITION
# ════════════════════════════════════════════════════════

def get_table(type_lot: str) -> dict:
    """Retourne la table de référence selon le type de lot."""
    tables = {
        'chair':    TABLE_CHAIR,
        'pondeuse': TABLE_PONDEUSE,
        'poussin':  TABLE_POUSSIN,
    }
    return tables.get(type_lot, TABLE_CHAIR)


def interpoler_reference(type_lot: str, semaine: int) -> dict:
    """
    Interpole les valeurs de référence pour une semaine donnée.
    Si la semaine exacte n'est pas dans la table, on interpole
    entre les semaines encadrantes.

    Exemple : semaine 11 pour pondeuse → interpolation entre S8 et S12
    """
    table = get_table(type_lot)
    semaines = sorted(table.keys())

    # Si la semaine dépasse la table → on prend la dernière valeur
    if semaine >= semaines[-1]:
        s = semaines[-1]
        poids, nourriture, eau = table[s]
        return {
            'semaine':       semaine,
            'poids_attendu': poids,
            'nourriture_g':  nourriture,
            'eau_ml':        eau,
            'interpolee':    False,
        }

    # Trouve les semaines encadrantes
    s_inf = max(s for s in semaines if s <= semaine)
    s_sup = min(s for s in semaines if s > semaine)

    # Interpolation linéaire entre les deux semaines
    ratio = (semaine - s_inf) / (s_sup - s_inf)

    p_inf, n_inf, e_inf = table[s_inf]
    p_sup, n_sup, e_sup = table[s_sup]

    poids      = p_inf + ratio * (p_sup - p_inf)
    nourriture = n_inf + ratio * (n_sup - n_inf)
    eau        = e_inf + ratio * (e_sup - e_inf)

    return {
        'semaine':       semaine,
        'poids_attendu': round(poids),
        'nourriture_g':  round(nourriture, 1),
        'eau_ml':        round(eau),
        'interpolee':    True,
    }


def calculer_besoins_lot(type_lot: str, semaine: int, nb_sujets: int) -> dict:
    """
    Calcule les besoins totaux du lot pour la journée.

    Retourne les quantités pour TOUT le lot (pas par sujet).
    C'est ce que l'éleveur doit distribuer concrètement.
    """
    ref = interpoler_reference(type_lot, semaine)

    # Facteur de correction selon la température
    # Les volailles mangent moins quand il fait chaud
    facteur_chaleur = 1.0  # sera ajusté par la température réelle

    return {
        'nourriture_totale_kg': round(
            (ref['nourriture_g'] * nb_sujets * facteur_chaleur) / 1000, 2
        ),
        'eau_totale_litres': round(
            (ref['eau_ml'] * nb_sujets) / 1000, 2
        ),
        'poids_attendu_g':   ref['poids_attendu'],
        'par_sujet':         ref,
    }


def analyser_croissance(suivis: list, type_lot: str) -> dict:
    """
    Analyse la courbe de croissance réelle vs référence.
    Détecte les retards de croissance et prédit la date optimale
    d'abattage (chair) ou de début de ponte (pondeuse).

    suivis = liste de dicts {'semaine': int, 'poids_moyen_g': float}
    """
    if len(suivis) < 2:
        return {
            'statut':    'insuffisant',
            'message':   'Pas assez de données de suivi',
        }

    semaines = [s['semaine'] for s in suivis]
    poids    = [s['poids_moyen_g'] for s in suivis]

    # Régression linéaire sur la courbe de croissance réelle
    X = np.array(semaines).reshape(-1, 1)
    Y = np.array(poids)
    modele = LinearRegression()
    modele.fit(X, Y)

    # Calcule l'écart avec la référence pour chaque semaine
    ecarts = []
    for s in suivis:
        ref   = interpoler_reference(type_lot, s['semaine'])
        ecart = s['poids_moyen_g'] - ref['poids_attendu']
        ecart_pct = (ecart / ref['poids_attendu']) * 100
        ecarts.append({
            'semaine':     s['semaine'],
            'poids_reel':  s['poids_moyen_g'],
            'poids_ref':   ref['poids_attendu'],
            'ecart_g':     round(ecart),
            'ecart_pct':   round(ecart_pct, 1),
        })

    # Statut global de la croissance
    dernier_ecart = ecarts[-1]['ecart_pct']
    if dernier_ecart >= -5:
        statut  = 'normal'
        message = 'Croissance conforme aux références'
    elif dernier_ecart >= -15:
        statut  = 'retard_leger'
        message = f'Légère sous-performance : {dernier_ecart}% sous la référence'
    else:
        statut  = 'retard_severe'
        message = f'Retard de croissance significatif : {dernier_ecart}% sous la référence'

    # Prédiction date optimale d'abattage (chair uniquement)
    prediction = None
    if type_lot == 'chair':
        # Poids cible d'abattage : 1800g (standard Cameroun)
        poids_cible = 1800
        derniere_semaine = semaines[-1]
        poids_actuel     = poids[-1]
        pente            = modele.coef_[0]

        if pente > 0:
            semaines_restantes = (poids_cible - poids_actuel) / pente
            semaine_abattage   = derniere_semaine + semaines_restantes
            prediction = {
                'poids_cible_g':     poids_cible,
                'semaine_prevue':    round(semaine_abattage, 1),
                'jours_restants':    round(semaines_restantes * 7),
            }

    return {
        'statut':     statut,
        'message':    message,
        'ecarts':     ecarts,
        'prediction': prediction,
    }


def recommander_ajustement_nutrition(
    temperature_reelle: float,
    type_lot: str,
    semaine: int,
    nb_sujets: int,
) -> dict:
    """
    Recommande un ajustement de la ration alimentaire
    en fonction de la température ambiante réelle.

    Les volailles réduisent leur consommation alimentaire
    quand il fait chaud (au-dessus de 25°C).
    """
    besoins_base = calculer_besoins_lot(type_lot, semaine, nb_sujets)

    # Température idéale pour cet âge
    semaines_ref = sorted(TEMPERATURE_IDEALE.keys())
    temp_ideale  = TEMPERATURE_IDEALE.get(
        min(semaines_ref, key=lambda s: abs(s - semaine)),
        22
    )

    # Facteur de correction selon l'écart de température
    ecart_temp = temperature_reelle - temp_ideale
    if ecart_temp > 5:
        # Réduction de 1.5% par degré au-dessus de la zone idéale
        facteur    = max(0.7, 1 - (ecart_temp * 0.015))
        recommandation = f'Chaleur excessive ({temperature_reelle}°C) — réduire ration de {round((1-facteur)*100)}%'
    elif ecart_temp < -3:
        # Augmentation si trop froid
        facteur        = min(1.3, 1 + (abs(ecart_temp) * 0.01))
        recommandation = f'Froid ({temperature_reelle}°C) — augmenter ration de {round((facteur-1)*100)}%'
    else:
        facteur        = 1.0
        recommandation = f'Température optimale ({temperature_reelle}°C) — ration normale'

    return {
        'nourriture_recommandee_kg': round(
            besoins_base['nourriture_totale_kg'] * facteur, 2
        ),
        'eau_recommandee_litres': besoins_base['eau_totale_litres'],
        'facteur_correction':     round(facteur, 2),
        'temperature_ideale':     temp_ideale,
        'recommandation':         recommandation,
    }