"""Fonctions de calcul : catégories d'âge, conversions de temps et calcul des points.

Traduction des fonctions de IMPORT_TABLES_COTATION.R et des calculs de score de app.R.
"""

import math

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# 1. Catégories (format_categorie, format_relais, format_epreuve en R)
# ---------------------------------------------------------------------------

def format_categorie(age):
    """Catégorie masters (C1 à C16) à partir de l'âge. Renvoie "NA" hors tranches."""
    if age is None or (isinstance(age, float) and math.isnan(age)):
        return "NA"
    a = float(age)
    # C1 = 25-29, C2 = 30-34, ... C15 = 95-99 : mêmes bornes que le case_when en R
    for i in range(15):
        debut = 25 + 5 * i
        if debut <= a <= debut + 4:
            return f"C{i + 1}"
    if 100 <= a <= 120:
        return "C16"
    return "NA"


def format_relais(somme_ages):
    """Catégorie de relais (R1 à R8) à partir de la somme des âges des relayeurs."""
    if somme_ages is None or (isinstance(somme_ages, float) and math.isnan(somme_ages)):
        return "NA"
    a = float(somme_ages)
    tranches = [(100, 119, "R1"), (120, 159, "R2"), (160, 199, "R3"), (200, 239, "R4"),
                (240, 279, "R5"), (280, 319, "R6"), (320, 359, "R7")]
    for debut, fin, cat in tranches:
        if debut <= a <= fin:
            return cat
    if a >= 360:
        return "R8"
    return "NA"


CODES_EPREUVES = {
    "50 NAGE LIBRE": "NL_50", "100 NAGE LIBRE": "NL_100", "200 NAGE LIBRE": "NL_200",
    "400 NAGE LIBRE": "NL_400", "800 NAGE LIBRE": "NL_800", "1000 NAGE LIBRE": "NL_1000",
    "1500 NAGE LIBRE": "NL_1500", "50 DOS": "DOS_50", "100 DOS": "DOS_100", "200 DOS": "DOS_200",
    "50 BRASSE": "BRA_50", "100 BRASSE": "BRA_100", "200 BRASSE": "BRA_200",
    "50 PAPILLON": "PAP_50", "100 PAPILLON": "PAP_100", "200 PAPILLON": "PAP_200",
    "100 4 NAGES": "N4_100", "200 4 NAGES": "N4_200", "400 4 NAGES": "N4_400",
}


def format_epreuve(libelle):
    """Sigle d'une épreuve à partir de son libellé (ex. '50 DOS' -> 'DOS_50')."""
    return CODES_EPREUVES.get(libelle, "NA")


# ---------------------------------------------------------------------------
# 2. Conversions de temps
# ---------------------------------------------------------------------------

def conv_temps(texte):
    """'MM:SS.ss' -> secondes (convtemps en R : 2 premiers caractères = minutes)."""
    if texte is None or (isinstance(texte, float) and math.isnan(texte)):
        return np.nan
    texte = str(texte).strip()
    try:
        return float(texte[0:2]) * 60 + float(texte[3:8])
    except ValueError:
        return np.nan


def en_secondes(texte):
    """'H:M:S', 'M:S' ou 'S' -> secondes (toSeconds en R)."""
    if texte is None or (isinstance(texte, float) and math.isnan(texte)):
        return np.nan
    morceaux = [float(x) for x in str(texte).split(":")]
    if len(morceaux) == 3:
        return morceaux[0] * 3600 + morceaux[1] * 60 + morceaux[2]
    if len(morceaux) == 2:
        return morceaux[0] * 60 + morceaux[1]
    return morceaux[0]


def format_temps(secondes):
    """Secondes -> 'MM:SS.ss' (équivalent de strftime(as.hms(x), '%M:%OS2'))."""
    if secondes is None or (isinstance(secondes, float) and math.isnan(secondes)):
        return ""
    total = round(float(secondes), 2)
    minutes = int(total // 60) % 60  # %M en R n'affiche que les minutes (0-59)
    reste = total - int(total // 60) * 60
    return f"{minutes:02d}:{reste:05.2f}"


# ---------------------------------------------------------------------------
# 3. Coefficients d'âge et points
# ---------------------------------------------------------------------------

def coefficient_age(coef_dames, coef_messieurs, sexe, epreuve, categorie):
    """Coefficient de rajeunissement pour un sexe, une épreuve et une catégorie.

    Les tables de coefficients ont une ligne par épreuve (colonne EPREUVE)
    et une colonne par catégorie (C1, C2, ...). Renvoie NaN si introuvable.
    """
    table = coef_dames if sexe == "F" else coef_messieurs
    ligne = table.loc[table["EPREUVE"] == epreuve]
    if ligne.empty or categorie not in table.columns:
        return np.nan
    return pd.to_numeric(ligne.iloc[0][categorie], errors="coerce")


def points_depuis_table(table, colonne, temps, verifier_dernier=True):
    """Points correspondant à un temps dans une table de cotation.

    On cherche le plus petit temps de la table qui est >= au temps réalisé,
    et on renvoie les points de cette ligne (logique which.min de app.R).
    Si `verifier_dernier` est vrai et que le temps est plus lent que la
    dernière ligne de la table, le score vaut 0.
    """
    if temps is None or (isinstance(temps, float) and math.isnan(temps)):
        return None
    valeurs = pd.to_numeric(table[colonne], errors="coerce").to_numpy(dtype=float)
    if verifier_dernier and temps > valeurs[-1]:
        return 0
    ecarts = valeurs - temps
    ecarts[ecarts < 0] = 999
    ecarts[np.isnan(ecarts)] = np.inf  # which.min ignore les NA
    return table["POINTS"].iloc[int(np.argmin(ecarts))]


def calcul_score(donnees, sexe, age, epreuve, temps):
    """Score d'une performance individuelle.

    Renvoie un dictionnaire avec les étapes du calcul (catégorie, coefficient,
    temps normé et points) pour pouvoir les afficher et les vérifier.
    """
    resultat = {"categorie": None, "coefficient": None, "temps_norme": None, "points": None}
    if sexe not in ("F", "M") or age is None or not epreuve or not temps:
        return resultat

    categorie = format_categorie(age)
    coef = coefficient_age(donnees["coef_dames"], donnees["coef_messieurs"], sexe, epreuve, categorie)
    resultat["categorie"] = categorie
    resultat["coefficient"] = coef
    if coef is None or math.isnan(coef) or coef == 0:
        return resultat

    temps_norme = round(float(temps) / coef, 2)
    resultat["temps_norme"] = temps_norme

    table = donnees["cot_dames"] if sexe == "F" else donnees["cot_messieurs"]
    if epreuve not in table.columns:
        return resultat
    resultat["points"] = points_depuis_table(table, epreuve, temps_norme)
    return resultat
