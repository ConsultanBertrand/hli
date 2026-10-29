"""Génère un jeu de données FICTIF pour tester l'application (y compris l'optimisation).

Usage :  python outils/generer_donnees_test.py [dossier_sortie]
Par défaut, les fichiers sont écrits dans data_test/ à la racine du projet.
Les noms de nageurs et de clubs sont inventés. Les fichiers respectent les formats
attendus par utils/donnees.py (mêmes séparateurs, colonnes et formats de temps).
"""

import random
import sys
from datetime import date, timedelta
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from utils.cotation import format_categorie, points_depuis_table  # noqa: E402
from utils.donnees import COLONNES_COT_IND, _lire_coefficients, _lire_table_cotation  # noqa: E402

random.seed(2026)  # résultats identiques à chaque exécution

SORTIE = Path(sys.argv[1]) if len(sys.argv) > 1 else RACINE / "data_test"
SORTIE.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. Tables de cotation : un palier par point, de 1400 à 1
# ---------------------------------------------------------------------------
# Temps de référence à 1400 points (secondes), dans l'ordre des colonnes R
REF_IND_DAMES = [25.5, 55.5, 121, 256, 530, 670, 1010, 28.5, 61, 131, 31, 67.5, 146,
                 27, 60, 135, 63, 140, 300]
REF_IND_MESS = [22.5, 49.5, 109, 231, 480, 610, 915, 25.5, 54.5, 118, 27.5, 60, 131,
                24, 53.5, 121, 56, 124, 268]
REF_REL_MESS = [92, 202, 445, 103, 224, 138, 184, 230, 276, 404, 505, 104, 112, 98, 226]
REF_REL_MIXTE = [round(t * 0.88, 1) for t in [98, 216, 474, 109, 238, 147, 196, 245, 294, 432, 540, 110, 120, 104, 241]]
EXPOSANT = 0.36  # plus l'exposant est grand, plus les temps s'allongent quand les points baissent


def temps_pour_points(reference, points):
    return reference * (1400 / points) ** EXPOSANT


def mmss(secondes):
    """Format MM:SS.ss lu par convtemps (2 caractères de minutes)."""
    secondes = round(secondes, 2)
    minutes = int(secondes // 60)
    return f"{minutes:02d}:{secondes - 60 * minutes:05.2f}"


def ecrire_table(nom, references):
    lignes = [f"{p} " + " ".join(mmss(temps_pour_points(r, p)) for r in references)
              for p in range(1400, 0, -1)]
    (SORTIE / nom).write_text("\n".join(lignes) + "\n", encoding="utf-8")


ecrire_table("table_cot_ind_dame_2017.txt", REF_IND_DAMES)
ecrire_table("table_cot_ind_messieurs_2017.txt", REF_IND_MESS)
ecrire_table("table_cot_rel_messieurs_2017.txt", REF_REL_MESS)
ecrire_table("table_cot_rel_mixte_2017.txt", REF_REL_MIXTE)

# ---------------------------------------------------------------------------
# 2. Codes et libellés d'épreuves
# ---------------------------------------------------------------------------
LIBELLES = {
    "NL_50": "50 NAGE LIBRE", "NL_100": "100 NAGE LIBRE", "NL_200": "200 NAGE LIBRE",
    "DOS_50": "50 DOS", "DOS_100": "100 DOS", "BRA_50": "50 BRASSE", "BRA_100": "100 BRASSE",
    "PAP_50": "50 PAPILLON", "PAP_100": "100 PAPILLON", "N4_100": "100 4 NAGES",
}
EPREUVES = list(LIBELLES)
lignes = ["EPREUVE;CODE_EPREUVE"]
for code, libelle in LIBELLES.items():
    lignes += [f"{libelle} DAMES;{code}", f"{libelle} MESSIEURS;{code}"]
(SORTIE / "codes_epreuves.csv").write_text("\n".join(lignes) + "\n", encoding="utf-8")

# ---------------------------------------------------------------------------
# 3. Coefficients d'âge (1 en C1, croissants avec l'âge)
# ---------------------------------------------------------------------------
entete = "EPREUVE;" + ";".join(f"C{i}" for i in range(1, 17))
for nom, pente in [("coef_age_dames.csv", 0.045), ("coef_age_messieurs.csv", 0.040)]:
    lignes = [entete]
    for j, code in enumerate(EPREUVES):
        valeurs = [1 + pente * k * (1 + 0.03 * k + 0.01 * j) for k in range(16)]
        lignes.append(code + ";" + ";".join(f"{v:.4f}" for v in valeurs))
    (SORTIE / nom).write_text("\n".join(lignes) + "\n", encoding="utf-8")

lignes = ["EPREUVE;r0;r1;r2;r3;r4;r5;r6;r7;r8"]
for j, code in enumerate(["N4_50", "NL_50", "N4_100", "NL_100"]):
    lignes.append(code + ";" + ";".join(f"{1 + 0.06 * k * (1 + 0.02 * j):.4f}" for k in range(9)))
(SORTIE / "coef_relais_4.csv").write_text("\n".join(lignes) + "\n", encoding="utf-8")

# ---------------------------------------------------------------------------
# 4. Clubs et nageurs fictifs
# ---------------------------------------------------------------------------
CLUBS = [  # (id, nom, département, nb femmes, nb hommes)
    ("920000001", "CN EXEMPLE", "Hauts-de-Seine", 8, 9),
    ("920000002", "AQUA TEST", "Hauts-de-Seine", 6, 7),
    ("750000003", "NATATION DÉMO", "Paris", 5, 6),
    ("690000004", "LYON MASTERS FICTIF", "Rhône", 7, 6),
    ("130000005", "PETIT CLUB", "Bouches-du-Rhône", 3, 4),  # < 10 nageurs : doit être écarté
]
NOMS = ["MARTIN", "BERNARD", "THOMAS", "PETIT", "ROBERT", "RICHARD", "DURAND", "DUBOIS", "MOREAU",
        "LAURENT", "SIMON", "MICHEL", "LEFEBVRE", "LEROY", "ROUX", "DAVID", "BERTRAND", "MOREL",
        "FOURNIER", "GIRARD", "BONNET", "DUPONT", "LAMBERT", "FONTAINE", "ROUSSEAU", "VINCENT",
        "MULLER", "LEFÈVRE", "FAURE", "ANDRÉ", "MERCIER", "BLANC", "GUÉRIN", "BOYER", "GARNIER",
        "CHEVALIER", "FRANÇOIS", "LEGRAND", "GAUTHIER", "GARCIA", "PERRIN", "ROBIN", "CLÉMENT",
        "MORIN", "NICOLAS", "HENRY", "ROUSSEL", "MATHIEU", "GAUTIER", "MASSON", "MARCHAND",
        "DUVAL", "DENIS", "DUMONT", "MARIE", "LEMAIRE", "NOËL", "MEYER", "DUFOUR", "MEUNIER",
        "BRUN", "BLANCHARD", "GIRAUD", "JOLY", "RIVIÈRE", "LUCAS", "BRUNET", "GAILLARD", "BARBIER",
        "ARNAUD", "MARTINEZ", "GÉRARD", "ROCHE", "RENARD", "SCHMITT", "ROY", "LEROUX", "COLIN"]
PRENOMS_F = ["Élodie", "Claire", "Inès", "Hélène", "Lucie", "Sophie", "Camille", "Julie", "Anaïs",
             "Céline", "Marion", "Laure", "Chloé", "Émilie", "Nathalie", "Sandrine", "Aurélie"]
PRENOMS_M = ["Julien", "Mathieu", "Rémi", "Laurent", "Thomas", "Nicolas", "Hugo", "Jérôme",
             "Sébastien", "François", "Antoine", "Benoît", "Cédric", "Olivier", "Damien", "Loïc"]
random.shuffle(NOMS)

AUJOURDHUI = date(2026, 10, 27)
nageurs = []  # dicts
iuf = 3000100
for id_club, _, _, nb_f, nb_m in CLUBS:
    for sexe, nb, prenoms in [("F", nb_f, PRENOMS_F), ("M", nb_m, PRENOMS_M)]:
        for _ in range(nb):
            age = random.choice([random.randint(25, 45), random.randint(25, 70)])
            nageurs.append({
                "IUF": iuf, "NOM": NOMS.pop(), "PRENOM": random.choice(prenoms), "SEXE": sexe,
                "AGE": age, "ID_CLUB": id_club,
                "NIVEAU": random.uniform(550, 1150),  # niveau moyen en points
                "SPECIALITE": random.choice(["NL", "DOS", "BRA", "PAP", "N4"]),
            })
            iuf += 1

lignes = ["Nom;Prenom;ID;Age;id_club"]
lignes += [f"{n['NOM']};{n['PRENOM']};{n['IUF']};{n['AGE']};{n['ID_CLUB']}" for n in nageurs]
# Un nageur de moins de 25 ans, qui doit être écarté par le filtre d'âge
lignes.append("JEUNE;Paul;3999999;22;920000001")
(SORTIE / "df_nageurs.csv").write_text("\n".join(lignes) + "\n", encoding="utf-8")

lignes = ["id_club;nom_club;Departement"]
lignes += [f"{c[0]};{c[1]};{c[2]}" for c in CLUBS]
(SORTIE / "df_clubs.csv").write_text("\n".join(lignes) + "\n", encoding="utf-8")

# ---------------------------------------------------------------------------
# 5. Performances (points calculés avec les tables générées ci-dessus)
# ---------------------------------------------------------------------------
cot = {"F": _lire_table_cotation(SORTIE / "table_cot_ind_dame_2017.txt", COLONNES_COT_IND),
       "M": _lire_table_cotation(SORTIE / "table_cot_ind_messieurs_2017.txt", COLONNES_COT_IND)}
coef = {"F": _lire_coefficients(SORTIE / "coef_age_dames.csv"),
        "M": _lire_coefficients(SORTIE / "coef_age_messieurs.csv")}
ref = {"F": dict(zip(COLONNES_COT_IND[1:], REF_IND_DAMES)),
       "M": dict(zip(COLONNES_COT_IND[1:], REF_IND_MESS))}

entete = ("iuf,nom,prenom,sexe,annee_naissance,age_bis,nom_pre,code_epreuve,temps,date_epreuve,"
          "bassin,annee_epreuve,age,categorie,coefficient_age,temps_norme_2,points,epreuve_gen,"
          "categorie_bis,coefficient_age_bis,temps_norme_2_bis,points_bis,id_club")
lignes = [entete]
nb_perfs = 0
for n in nageurs:
    # Toujours le 50 NL (pour le relais 10x50), quelques 50 des autres nages (relais 4 nages),
    # plus les épreuves de la spécialité et quelques autres au hasard.
    choix = {"NL_50"}
    choix |= set(random.sample(["DOS_50", "BRA_50", "PAP_50"], k=random.randint(1, 3)))
    choix |= {e for e in EPREUVES if e.startswith(n["SPECIALITE"])}
    choix |= set(random.sample(EPREUVES, k=random.randint(1, 3)))
    for code in sorted(choix):
        bonus = 120 if code.startswith(n["SPECIALITE"]) else 0
        for _ in range(random.randint(1, 4)):  # plusieurs perfs : meilleure ≠ dernière
            # Dates entre 2021 et aujourd'hui (celles avant 2023 testent le filtre de dates)
            jour = date(2021, 1, 1) + timedelta(days=random.randint(0, (AUJOURDHUI - date(2021, 1, 1)).days))
            age = n["AGE"] - (AUJOURDHUI.year - jour.year)
            if age < 25:
                continue
            cat = format_categorie(age)
            c = float(coef[n["SEXE"]].loc[coef[n["SEXE"]]["EPREUVE"] == code, cat].iloc[0])
            points_vises = min(1350, max(150, n["NIVEAU"] + bonus + random.gauss(0, 60)))
            temps = round(temps_pour_points(ref[n["SEXE"]][code], points_vises) * c, 2)
            temps_norme = round(temps / c, 2)
            pts = int(points_depuis_table(cot[n["SEXE"]], code, temps_norme))
            nom_pre = f"{n['NOM']} {n['PRENOM']}"
            lignes.append(
                f"{n['IUF']},{n['NOM']},{n['PRENOM']},{n['SEXE']},{AUJOURDHUI.year - n['AGE']},"
                f"{n['AGE']},{nom_pre},{code},{temps},{jour:%d/%m/%Y},{random.choice([25, 50])},"
                f"{jour.year},{age},{cat},{c},{temps_norme},{pts},{LIBELLES[code]},{cat},{c},"
                f"{temps_norme},{pts},{n['ID_CLUB']}"
            )
            nb_perfs += 1
(SORTIE / "df_perfs.csv").write_text("\n".join(lignes) + "\n", encoding="utf-8")

print(f"{len(nageurs)} nageurs, {nb_perfs} performances, {len(CLUBS)} clubs -> {SORTIE}")
