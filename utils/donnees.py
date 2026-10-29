"""Chargement et préparation des données.

Traduction de IMPORT_TABLES_COTATION.R. Les fichiers sont lus tels quels depuis
le dossier data/ (copie du dossier data/ de l'application Shiny).
"""

from pathlib import Path

import pandas as pd

from utils.cotation import conv_temps

try:  # le cache Streamlit n'est utilisé que si Streamlit est disponible
    import streamlit as st
    _cache = st.cache_data(show_spinner="Chargement des données…")
except ImportError:  # permet de tester ce module sans Streamlit
    def _cache(fonction):
        return fonction


DOSSIER_DATA = Path(__file__).resolve().parent.parent / "data"

# Identifiant FFN du club CSM PUTEAUX (filtre repris tel quel du code R)
ID_CSM_PUTEAUX = "130920620"
NAGEURS_CSM_PUTEAUX = [
    "AÏT-HAMADOUCHE Nadir", "AGEORGES Carine", "AUBERT Clément", "BOUCHACHI Mehdi",
    "CHAUCHARD Jean-Luc", "DE AMARO Dylan", "DESMAREST Eva", "DONZEL Clément",
    "DUPREZ Véronique", "GOYET Julien", "GROENE Alexis", "IAZ Karim", "ISLAS PEREZ Carlos",
    "ISNARDON Paul", "IZARZUGAZA Alienor", "KOUIDRI Malek", "LABAT Sophie", "LABE Véronique",
    "LAMALLE Celine", "LE THIEC Aymeric", "LEBLANC Benoît", "LECOMPT Cyril",
    "LIBBRECHT Mathieu", "LOISON Adeline", "LY Jérôme", "NOURICHARD Franck",
    "PARMENTIER Antoine", "PO Stanislas", "SANSON Brigitte", "SANSON Gilles",
    "SIMONNET Jérôme", "VALIDIRE Jerome", "XU Hui",
]
FILTRER_CSM_PUTEAUX = True  # mettre à False pour garder tous les nageurs de CSM PUTEAUX

COLONNES_COT_IND = [
    "POINTS", "NL_50", "NL_100", "NL_200", "NL_400", "NL_800", "NL_1000", "NL_1500",
    "DOS_50", "DOS_100", "DOS_200", "BRA_50", "BRA_100", "BRA_200", "PAP_50",
    "PAP_100", "PAP_200", "N4_100", "N4_200", "N4_400",
]
COLONNES_COT_REL = [
    "POINTS", "NL_50_R4", "NL_100_R4", "NL_200_R4", "N4C_50_R4", "N4C_100_R4",
    "NL_50_R6", "NL_50_R8", "NL_50_R10", "NL_50_R12", "NL_100_R8",
    "NL_100_R10", "DOS_50_R4", "BRA_50_R4", "PAP_50_R4", "N4_100_R4",
]
COLONNES_PERFS = [
    "IUF", "NOM", "PRENOM", "SEXE", "ANNEE_NAISSANCE", "AGE_BIS", "NOM_PRE", "CODE_EPREUVE",
    "TEMPS", "DATE_EPREUVE", "BASSIN", "ANNEE_EPREUVE", "AGE", "CATEGORIE", "COEFFICIENT_AGE",
    "TEMPS_NORME_2", "POINTS", "EPREUVE_GEN", "CATEGORIE_BIS", "COEFFICIENT_AGE_BIS",
    "TEMPS_NORME_2_BIS", "POINTS_BIS", "ID_CLUB",
]
COLONNES_PERFS_NUMERIQUES = [
    "ANNEE_NAISSANCE", "AGE_BIS", "TEMPS", "BASSIN", "ANNEE_EPREUVE", "AGE", "COEFFICIENT_AGE",
    "TEMPS_NORME_2", "POINTS", "COEFFICIENT_AGE_BIS", "TEMPS_NORME_2_BIS", "POINTS_BIS",
]

FICHIERS = {
    "cot_dames": "table_cot_ind_dame_2017.txt",
    "cot_messieurs": "table_cot_ind_messieurs_2017.txt",
    "cot_relais_messieurs": "table_cot_rel_messieurs_2017.txt",
    "cot_relais_mixte": "table_cot_rel_mixte_2017.txt",
    "codes_epreuves": "codes_epreuves.csv",
    "coef_dames": "coef_age_dames.csv",
    "coef_messieurs": "coef_age_messieurs.csv",
    "coef_relais": "coef_relais_4.csv",
    "nageurs": "df_nageurs.csv",
    "perfs": "df_perfs.csv",
    "clubs": "df_clubs.csv",
}


# ---------------------------------------------------------------------------
# Outils de lecture
# ---------------------------------------------------------------------------

def _lire_csv(chemin, **options):
    """Lit un CSV en UTF-8, ou en Windows-1252 si les accents ne passent pas."""
    try:
        return pd.read_csv(chemin, encoding="utf-8-sig", **options)
    except UnicodeDecodeError:
        return pd.read_csv(chemin, encoding="cp1252", **options)


def _en_texte(serie):
    """Identifiants (IUF, club) en texte propre, pour que les jointures fonctionnent."""
    return serie.astype("string").str.strip().str.replace(r"\.0$", "", regex=True)


def _en_nombre(serie):
    """Conversion numérique tolérante (virgule décimale, valeurs '.')."""
    if serie.dtype == object or str(serie.dtype) == "string":
        serie = serie.astype("string").str.replace(",", ".", regex=False)
    return pd.to_numeric(serie, errors="coerce")


def fichiers_manquants(dossier=DOSSIER_DATA):
    """Liste des fichiers attendus absents du dossier data/."""
    return [nom for nom in FICHIERS.values() if not (Path(dossier) / nom).exists()]


# ---------------------------------------------------------------------------
# Tables de référence FFN
# ---------------------------------------------------------------------------

def _lire_table_cotation(chemin, colonnes):
    """Tables de cotation : temps 'MM:SS.ss' convertis en secondes (cid2, cim2, crm2, crx2)."""
    table = _lire_csv(chemin, sep=" ", header=None, names=colonnes, dtype=str)
    resultat = pd.DataFrame({"POINTS": _en_nombre(table["POINTS"])})
    for colonne in colonnes[1:]:
        resultat[colonne] = table[colonne].map(conv_temps)
    return resultat


def _lire_coefficients(chemin):
    """Tables de coefficients d'âge : une ligne par épreuve, une colonne par catégorie."""
    table = _lire_csv(chemin, sep=";", na_values=".", dtype=str)
    table.columns = ["EPREUVE"] + [str(c).strip().upper() for c in table.columns[1:]]
    table["EPREUVE"] = table["EPREUVE"].str.strip()
    for colonne in table.columns[1:]:
        table[colonne] = _en_nombre(table[colonne])
    return table


def _lire_codes_epreuves(chemin):
    codes = _lire_csv(chemin, sep=";", dtype=str)
    codes["SEXE"] = codes["EPREUVE"].str.contains("MESSIEURS").map({True: "M", False: "F"})
    codes["EPREUVE_GEN"] = (codes["EPREUVE"].str.replace(" MESSIEURS", "", regex=False)
                                            .str.replace(" DAMES", "", regex=False))
    return codes


# ---------------------------------------------------------------------------
# Données des nageurs (webscrapées)
# ---------------------------------------------------------------------------

def _lire_nageurs(chemin):
    nageurs = _lire_csv(chemin, sep=";", dtype=str)
    nageurs["Age"] = _en_nombre(nageurs["Age"])
    nageurs = nageurs[nageurs["Age"] >= 25].copy()
    nageurs["NOM_PRE"] = nageurs["Nom"] + " " + nageurs["Prenom"]
    nageurs = nageurs.rename(columns={"ID": "IUF"})
    nageurs = nageurs[["IUF", "Nom", "Prenom", "NOM_PRE", "id_club"]].drop_duplicates()
    nageurs.columns = [c.upper() for c in nageurs.columns]  # IUF, NOM, PRENOM, NOM_PRE, ID_CLUB
    nageurs["IUF"] = _en_texte(nageurs["IUF"])
    nageurs["ID_CLUB"] = _en_texte(nageurs["ID_CLUB"])

    if FILTRER_CSM_PUTEAUX:
        garder = (nageurs["ID_CLUB"] != ID_CSM_PUTEAUX) | nageurs["NOM_PRE"].isin(NAGEURS_CSM_PUTEAUX)
        nageurs = nageurs[garder]
    return nageurs


def _lire_perfs(chemin):
    perfs = _lire_csv(chemin, dtype=str)  # séparateur virgule, comme read.csv par défaut
    if perfs.shape[1] != len(COLONNES_PERFS):
        raise ValueError(
            f"{chemin.name} contient {perfs.shape[1]} colonnes, "
            f"{len(COLONNES_PERFS)} étaient attendues."
        )
    perfs.columns = COLONNES_PERFS
    perfs["IUF"] = _en_texte(perfs["IUF"])
    perfs["ID_CLUB"] = _en_texte(perfs["ID_CLUB"])
    for colonne in COLONNES_PERFS_NUMERIQUES:
        perfs[colonne] = _en_nombre(perfs[colonne])
    perfs["DATE_EPREUVE"] = pd.to_datetime(perfs["DATE_EPREUVE"], dayfirst=True,
                                           format="mixed", errors="coerce")
    return perfs


def _clubs_eligibles(nageurs):
    """Clubs avec au moins 10 nageurs, dont 2 hommes et 2 femmes."""
    stats = (nageurs.assign(IUF_SEXE=nageurs["IUF"] + "_" + nageurs["SEXE"],
                            HOMME=nageurs["SEXE"] == "M",
                            FEMME=nageurs["SEXE"] == "F")
                    .groupby("ID_CLUB")
                    .agg(n=("IUF_SEXE", "nunique"), n_M=("HOMME", "sum"), n_F=("FEMME", "sum")))
    return stats[(stats["n"] >= 10) & (stats["n_M"] >= 2) & (stats["n_F"] >= 2)].index.tolist()


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------

def lire_donnees(dossier=DOSSIER_DATA):
    """Lit et prépare toutes les tables. Renvoie un dictionnaire de DataFrames."""
    dossier = Path(dossier)
    chemin = {cle: dossier / nom for cle, nom in FICHIERS.items()}

    perfs = _lire_perfs(chemin["perfs"])
    nageurs = _lire_nageurs(chemin["nageurs"])

    # Sexe et âge de chaque nageur, pris sur sa première performance
    infos = perfs.drop_duplicates("IUF")[["IUF", "SEXE", "AGE_BIS"]]
    nageurs = nageurs.merge(infos, on="IUF", how="left")
    nageurs = nageurs[nageurs["SEXE"].notna()]

    clubs_10 = _clubs_eligibles(nageurs)
    nageurs = nageurs[nageurs["ID_CLUB"].isin(clubs_10)].reset_index(drop=True)
    perfs = perfs[perfs["ID_CLUB"].isin(clubs_10)].reset_index(drop=True)

    clubs = _lire_csv(chemin["clubs"], sep=";", dtype=str)
    clubs["id_club"] = _en_texte(clubs["id_club"])
    clubs = clubs[clubs["id_club"].isin(clubs_10)].reset_index(drop=True)

    coef_relais = _lire_coefficients(chemin["coef_relais"])
    if coef_relais.shape[1] == 10:  # renommage fait dans app.R
        coef_relais.columns = ["EPREUVE"] + [f"R{i}" for i in range(9)]

    return {
        "nageurs": nageurs,
        "perfs": perfs,
        "clubs": clubs,
        "codes_epreuves": _lire_codes_epreuves(chemin["codes_epreuves"]),
        "cot_dames": _lire_table_cotation(chemin["cot_dames"], COLONNES_COT_IND),
        "cot_messieurs": _lire_table_cotation(chemin["cot_messieurs"], COLONNES_COT_IND),
        "cot_relais_messieurs": _lire_table_cotation(chemin["cot_relais_messieurs"], COLONNES_COT_REL),
        "cot_relais_mixte": _lire_table_cotation(chemin["cot_relais_mixte"], COLONNES_COT_REL),
        "coef_dames": _lire_coefficients(chemin["coef_dames"]),
        "coef_messieurs": _lire_coefficients(chemin["coef_messieurs"]),
        "coef_relais": coef_relais,
    }


@_cache
def charger_donnees():
    """Version mise en cache de lire_donnees(), à utiliser dans les pages."""
    return lire_donnees()
