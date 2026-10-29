"""Relais mixtes : 10x50 nage libre et 4x50 4 nages.

Traduction des blocs `rel_input_BIS1` et `rel_input_BIS2` de app.R. Les deux relais
sont composés à partir des nageurs retenus pour les épreuves individuelles.
"""

from itertools import combinations, permutations

import numpy as np
import pandas as pd

from utils.cotation import format_categorie, format_relais, format_temps, points_depuis_table
from utils.optimisation import formater_points, libelles_epreuves, performances_club

NAGES_4X50 = ["BRA_50", "DOS_50", "NL_50", "PAP_50"]


def _coefficient_nl50(donnees, sexe, age):
    """Coefficient d'âge du 50 NL pour un nageur (tables individuelles dames / messieurs)."""
    table = donnees["coef_dames"] if sexe == "F" else donnees["coef_messieurs"]
    categorie = format_categorie(age)
    ligne = table[table["EPREUVE"] == "NL_50"]
    if ligne.empty or categorie not in table.columns:
        return np.nan
    return float(ligne.iloc[0][categorie])


# ---------------------------------------------------------------------------
# Relais mixte 10x50 nage libre
# ---------------------------------------------------------------------------

def relais_10x50(donnees, club_ids, debut, fin, methode, noms_equipe):
    """Relais 10x50 NL avec les nageurs de l'équipe.

    Temps de chaque nageur : meilleur temps au 50 NL (méthode « meilleure ») ou temps de
    la dernière course (méthode « dernière »). Le temps total est divisé par la moyenne des
    coefficients d'âge, ramené à un relais de 4 nageurs, puis converti en points.
    """
    perfs = performances_club(donnees, club_ids, debut, fin)
    perfs = perfs[perfs["NOM_PRE"].isin(noms_equipe)]
    if perfs.empty:
        return {"erreur": "Aucune performance trouvée pour les nageurs de l'équipe sur la période.",
                "tableau": None, "points": None}

    lignes = []
    for iuf, perfs_nageur in perfs.groupby("IUF", sort=False):
        infos = perfs_nageur.iloc[0]
        nl50 = perfs_nageur[perfs_nageur["CODE_EPREUVE"] == "NL_50"].sort_values("DATE_EPREUVE", kind="stable")
        if nl50.empty:
            temps, date = 0.0, None  # aucun 50 NL : temps nul, comme dans app.R
        elif methode == "max":
            meilleure = nl50.loc[nl50["TEMPS"].idxmin()]
            temps, date = meilleure["TEMPS"], meilleure["DATE_EPREUVE"]
        else:
            derniere = nl50[nl50["DATE_EPREUVE"] == nl50["DATE_EPREUVE"].max()].iloc[0]
            temps, date = derniere["TEMPS"], derniere["DATE_EPREUVE"]
        lignes.append({
            "Nom": infos["NOM_PRE"],
            "Temps_s": float(temps),
            "Coefficient": _coefficient_nl50(donnees, infos["SEXE"], infos["AGE_BIS"]),
            "Date": f"{date:%d/%m/%Y}" if date is not None else "",
        })

    tableau = pd.DataFrame(lignes).sort_values("Nom").reset_index(drop=True)
    coef_moyen = tableau["Coefficient"].mean()
    temps_total = tableau["Temps_s"].sum()
    temps_norme = round(temps_total / coef_moyen, 2) / 10 * 4  # ramené à 4 relayeurs

    table = donnees["cot_relais_messieurs"]  # app.R utilise la table relais messieurs (crm2)
    points = points_depuis_table(table, "NL_50_R4", temps_norme, verifier_dernier=False)

    sans_temps = tableau.loc[tableau["Temps_s"] == 0, "Nom"].tolist()
    tableau["Temps"] = tableau["Temps_s"].map(lambda t: format_temps(t) if t > 0 else "")
    tableau["Coefficient"] = tableau["Coefficient"].map(lambda c: f"{c:.5g}" if pd.notna(c) else "")
    return {
        "erreur": None,
        "tableau": tableau[["Nom", "Temps", "Coefficient", "Date"]],
        "points": formater_points(points),
        "temps_total": format_temps(temps_total),
        "sans_temps": sans_temps,
    }


# ---------------------------------------------------------------------------
# Relais mixte 4x50 4 nages
# ---------------------------------------------------------------------------

def relais_4x50(donnees, club_ids, debut, fin, noms_equipe):
    """Relais 4x50 4 nages (2 hommes et 2 femmes) avec les nageurs de l'équipe.

    On essaie toutes les combinaisons de 2 hommes et 2 femmes et toutes les répartitions
    des 4 nages entre eux, et on retient celle dont la somme des meilleurs temps est la
    plus faible.
    """
    perfs = performances_club(donnees, club_ids, debut, fin)
    perfs = perfs[perfs["NOM_PRE"].isin(noms_equipe) & perfs["CODE_EPREUVE"].isin(NAGES_4X50)]
    perfs = perfs.dropna(subset=["IUF", "TEMPS"])

    # Meilleure performance de chaque nageur dans chaque nage
    meilleures = perfs.sort_values(["TEMPS", "IUF"], kind="stable").drop_duplicates(["IUF", "CODE_EPREUVE"])
    nageurs = meilleures.drop_duplicates("IUF").set_index("IUF")[["NOM_PRE", "SEXE", "AGE_BIS"]]
    perf = {(r.IUF, r.CODE_EPREUVE): r for r in meilleures.itertuples()}

    femmes = nageurs.index[nageurs["SEXE"] == "F"].tolist()
    hommes = nageurs.index[nageurs["SEXE"] == "M"].tolist()
    if len(femmes) < 2:
        return {"erreur": "Il n'y a pas assez de nageuses pour pouvoir faire un relais mixte.",
                "tableau": None, "points": None}
    if len(hommes) < 2:
        return {"erreur": "Il n'y a pas assez de nageurs pour pouvoir faire un relais mixte.",
                "tableau": None, "points": None}

    # Recherche de la meilleure composition : d'abord le plus de temps renseignés,
    # puis la somme des temps la plus faible
    meilleure, cle_meilleure = None, None
    for paire_h in combinations(hommes, 2):
        for paire_f in combinations(femmes, 2):
            equipe = paire_h + paire_f
            for nages in permutations(NAGES_4X50):
                temps = [perf[(i, n)].TEMPS if (i, n) in perf else np.nan for i, n in zip(equipe, nages)]
                nb_temps = int(np.sum(~np.isnan(temps)))
                cle = (-nb_temps, float(np.nansum(temps)))
                if cle_meilleure is None or cle < cle_meilleure:
                    meilleure, cle_meilleure = (equipe, nages, temps), cle

    equipe, nages, temps = meilleure
    nb_temps = -cle_meilleure[0]
    temps_total = cle_meilleure[1]

    somme_ages = float(nageurs.loc[list(equipe), "AGE_BIS"].sum())
    categorie = format_relais(somme_ages)
    ligne_coef = donnees["coef_relais"][donnees["coef_relais"]["EPREUVE"] == "N4_50"]
    if not ligne_coef.empty and categorie in ligne_coef.columns:
        coefficient = float(ligne_coef.iloc[0][categorie])
    else:
        coefficient = np.nan

    temps_norme = round(temps_total / coefficient, 2) / nb_temps * 4 if nb_temps else np.nan
    points = points_depuis_table(donnees["cot_relais_mixte"], "N4C_50_R4", temps_norme,
                                 verifier_dernier=False)

    libelles = libelles_epreuves(donnees)
    lignes = []
    for iuf, nage, t in zip(equipe, nages, temps):
        p = perf.get((iuf, nage))
        lignes.append({
            "Nom": nageurs.loc[iuf, "NOM_PRE"],
            "Temps": format_temps(t) if not np.isnan(t) else "",
            "Epreuve": libelles.get(nage, nage),
            "Date": f"{p.DATE_EPREUVE:%d/%m/%Y}" if p is not None else "",
        })
    return {
        "erreur": None,
        "tableau": pd.DataFrame(lignes),
        "points": formater_points(points),
        "temps_total": format_temps(temps_total),
        "somme_ages": int(somme_ages),
        "categorie": categorie,
        "coefficient": coefficient,
        "complet": nb_temps == 4,
    }
