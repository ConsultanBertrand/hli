"""Optimisation de l'équipe sur les 10 épreuves individuelles.

Traduction du bloc `selection_input` de app.R. Le programme linéaire (lpSolve en R)
est résolu avec scipy.optimize.milp (solveur HiGHS).
"""

import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, milp

from utils.cotation import calcul_score, format_temps

EPREUVES_INDIVIDUELLES = ["PAP_100", "DOS_50", "PAP_50", "NL_50", "NL_100",
                          "NL_200", "DOS_100", "BRA_50", "BRA_100", "N4_100"]
NB_MIN_FEMMES = 2
NB_MIN_HOMMES = 2
NB_MIN_NAGEURS = 10
COLONNES_RESULTAT = ["Nom_Prénom", "Epreuve", "Points", "Temps", "Date"]


# ---------------------------------------------------------------------------
# Outils communs
# ---------------------------------------------------------------------------

def libelles_epreuves(donnees):
    """Dictionnaire code -> libellé (ex. 'NL_50' -> '50 NAGE LIBRE')."""
    codes = donnees["codes_epreuves"].drop_duplicates("CODE_EPREUVE")
    return dict(zip(codes["CODE_EPREUVE"], codes["EPREUVE_GEN"]))


def performances_club(donnees, club_ids, debut, fin):
    """Performances des nageurs du club entre deux dates (incluses)."""
    perfs = donnees["perfs"]
    perfs = perfs[perfs["ID_CLUB"].isin(club_ids)]
    debut, fin = pd.Timestamp(debut), pd.Timestamp(fin)
    perfs = perfs[(perfs["DATE_EPREUVE"] >= debut) & (perfs["DATE_EPREUVE"] <= fin)]
    perfs = perfs.drop_duplicates().copy()
    # Libellé à partir de la table des codes (comme la jointure sqldf de app.R)
    perfs["EPREUVE_GEN"] = perfs["CODE_EPREUVE"].map(libelles_epreuves(donnees)).fillna(perfs["EPREUVE_GEN"])
    return perfs


def formater_points(valeur):
    """1234.0 -> '1 234' (séparateur de milliers espace, comme big.mark = ' ')."""
    if valeur is None or pd.isna(valeur):
        return ""
    return f"{float(valeur):,.0f}".replace(",", " ")


# ---------------------------------------------------------------------------
# Nageurs fixés
# ---------------------------------------------------------------------------

def creer_nageur_fixe(donnees, nom_pre, epreuve, temps):
    """Ligne décrivant un nageur fixé sur une épreuve, avec son score recalculé.

    Si aucun temps n'est saisi (0), le score est vide, comme dans app.R.
    Renvoie None si le nageur est introuvable.
    """
    nageurs = donnees["nageurs"]
    ligne = nageurs[nageurs["NOM_PRE"] == nom_pre]
    if ligne.empty:
        return None
    ligne = ligne.iloc[0]
    resultat = calcul_score(donnees, ligne["SEXE"], ligne["AGE_BIS"], epreuve, temps)
    return {
        "IUF": ligne["IUF"], "NOM": nom_pre, "EPREUVE": epreuve, "temps": float(temps),
        "AGE_BIS": ligne["AGE_BIS"], "SEXE": ligne["SEXE"], "NOM_PRE": nom_pre,
        "TEMPS_NORME": float(temps), "CAT": resultat["categorie"],
        "COEFFICIENT_AGE": resultat["coefficient"], "TEMPS_NORME_2": resultat["temps_norme"],
        "score_nag": resultat["points"],
    }


def ajouter_nageur_fixe(fixes, nouvelle_ligne):
    """Ajoute un nageur fixé. Un seul nageur par épreuve et une seule épreuve par nageur :
    en cas de doublon, c'est le dernier ajouté qui est conservé."""
    fixes = pd.concat([fixes, pd.DataFrame([nouvelle_ligne])], ignore_index=True)
    fixes = fixes.drop_duplicates("EPREUVE", keep="last")
    fixes = fixes.drop_duplicates("NOM", keep="last")
    return fixes.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Optimisation
# ---------------------------------------------------------------------------

def _matrice_points(histo, methode):
    """Une ligne par nageur, une colonne par épreuve, valeur = points retenus (0 si aucune perf)."""
    cles = ["IUF", "SEXE", "CODE_EPREUVE"]
    if methode == "max":  # meilleure performance
        points = histo.groupby(cles)["POINTS_BIS"].max()
    else:  # dernière performance (la première ligne en cas d'égalité de date)
        points = histo.sort_values("DATE_EPREUVE", kind="stable").groupby(cles)["POINTS_BIS"].last()
    matrice = points.unstack("CODE_EPREUVE", fill_value=0).fillna(0)
    return matrice.sort_index(level="SEXE")


def _resoudre(matrice):
    """Programme linéaire en variables binaires.

    x[i, e] = 1 si le nageur i nage l'épreuve e. On maximise la somme des points sous
    les contraintes : un nageur par épreuve, au plus une épreuve par nageur, au moins
    2 femmes et 2 hommes. Renvoie la matrice solution (0/1) ou None si impossible.
    """
    nb_nageurs, nb_epreuves = matrice.shape
    n = nb_nageurs * nb_epreuves
    sexes = matrice.index.get_level_values("SEXE")

    lignes, mini, maxi = [], [], []
    for e in range(nb_epreuves):  # exactement un nageur par épreuve
        ligne = np.zeros(n)
        ligne[e::nb_epreuves] = 1
        lignes.append(ligne); mini.append(1); maxi.append(1)
    for i in range(nb_nageurs):  # au plus une épreuve par nageur
        ligne = np.zeros(n)
        ligne[i * nb_epreuves:(i + 1) * nb_epreuves] = 1
        lignes.append(ligne); mini.append(0); maxi.append(1)
    for sexe, minimum in (("F", NB_MIN_FEMMES), ("M", NB_MIN_HOMMES)):  # mixité
        lignes.append(np.repeat((sexes == sexe).astype(float), nb_epreuves))
        mini.append(minimum); maxi.append(np.inf)

    resultat = milp(
        c=-matrice.to_numpy(dtype=float).ravel(),  # milp minimise : on prend l'opposé
        constraints=LinearConstraint(np.array(lignes), mini, maxi),
        integrality=np.ones(n),
        bounds=Bounds(0, 1),
    )
    if resultat.status != 0 or resultat.x is None:
        return None
    return pd.DataFrame(np.round(resultat.x).reshape(nb_nageurs, nb_epreuves),
                        index=matrice.index, columns=matrice.columns)


def optimiser_equipe(donnees, club_ids, debut, fin, methode, nageurs_preselectionnes, fixes):
    """Équipe optimale sur les épreuves individuelles.

    Renvoie un dictionnaire : {"erreur": message ou None, "tableau": DataFrame, "score": nombre}.
    """
    if len(nageurs_preselectionnes) < NB_MIN_NAGEURS:
        return {"erreur": f"Veuillez sélectionner au moins {NB_MIN_NAGEURS} nageurs.",
                "tableau": None, "score": None}

    epreuves_fixees = set(fixes["EPREUVE"]) if not fixes.empty else set()
    nageurs_fixes = set(fixes["NOM"]) if not fixes.empty else set()
    epreuves_a_optimiser = [e for e in EPREUVES_INDIVIDUELLES if e not in epreuves_fixees]

    # Historique des nageurs pré-sélectionnés, hors nageurs fixés
    histo = performances_club(donnees, club_ids, debut, fin)
    histo = histo[histo["CODE_EPREUVE"].isin(epreuves_a_optimiser)
                  & histo["NOM_PRE"].isin(nageurs_preselectionnes)
                  & ~histo["NOM_PRE"].isin(nageurs_fixes)]

    lignes_resultat = []
    score_total = 0.0
    if epreuves_a_optimiser:
        message = (f"Pas d'équipe optimale trouvée ! Veillez à bien pré-sélectionner au moins "
                   f"{NB_MIN_FEMMES} nageuses et {NB_MIN_HOMMES} nageurs ayant des performances "
                   f"sur la période du {pd.Timestamp(debut):%d/%m/%Y} au {pd.Timestamp(fin):%d/%m/%Y}.")
        if histo.empty:
            return {"erreur": message, "tableau": None, "score": None}
        matrice = _matrice_points(histo, methode)
        solution = _resoudre(matrice)
        if solution is None or solution.to_numpy().sum() == 0:
            return {"erreur": message, "tableau": None, "score": None}

        libelles = libelles_epreuves(donnees)
        for (iuf, _sexe), ligne in solution.iterrows():
            for code in ligne[ligne > 0].index:
                points = matrice.loc[(iuf, _sexe), code]
                # Performance correspondante, pour afficher le temps et la date
                perfs = histo[(histo["IUF"] == iuf) & (histo["CODE_EPREUVE"] == code)
                              & (histo["POINTS_BIS"] == points)].sort_values("DATE_EPREUVE")
                if perfs.empty:
                    perf = None
                else:  # dernière perf si méthode « dernière », sinon la plus ancienne à ce score
                    perf = perfs.iloc[-1] if methode != "max" else perfs.iloc[0]
                lignes_resultat.append({
                    "Nom_Prénom": perf["NOM_PRE"] if perf is not None else iuf,
                    "Epreuve": libelles.get(code, code),
                    "Points": points,
                    "Temps": format_temps(perf["TEMPS"]) if perf is not None else "",
                    "Date": f"{perf['DATE_EPREUVE']:%d/%m/%Y}" if perf is not None else "",
                })
                score_total += points

    # Ajout des nageurs fixés (sans temps ni date, comme dans app.R)
    if not fixes.empty:
        libelles = libelles_epreuves(donnees)
        for _, f in fixes.iterrows():
            points = f["score_nag"]
            lignes_resultat.append({"Nom_Prénom": f["NOM_PRE"],
                                    "Epreuve": libelles.get(f["EPREUVE"], f["EPREUVE"]),
                                    "Points": points, "Temps": "", "Date": ""})
            if points is not None and not pd.isna(points):
                score_total += points

    tableau = pd.DataFrame(lignes_resultat, columns=COLONNES_RESULTAT)
    tableau = tableau.sort_values("Nom_Prénom", kind="stable").reset_index(drop=True)
    tableau["Points"] = tableau["Points"].map(formater_points)
    return {"erreur": None, "tableau": tableau, "score": score_total}
