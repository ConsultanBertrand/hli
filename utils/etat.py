"""État partagé entre les pages (remplace les variables globales <<- et reactiveValues de Shiny)."""

import pandas as pd
import streamlit as st

COLONNES_FIXES = ["IUF", "NOM", "EPREUVE", "temps", "AGE_BIS", "SEXE", "NOM_PRE",
                  "TEMPS_NORME", "CAT", "COEFFICIENT_AGE", "TEMPS_NORME_2", "score_nag"]


def initialiser_etat():
    """Crée les clés de session si elles n'existent pas encore."""
    valeurs_par_defaut = {
        "club": None,             # nom du club choisi dans l'Accueil (input_choix_club)
        "club_ids": [],           # identifiants FFN correspondant à ce nom (list_id)
        "noms_club": [],          # NOM des nageurs du club (NOM_club_select)
        "nageurs_club": [],       # "NOM Prénom" des nageurs du club (NOM_PRE_club_select)
        "nageurs_fixes": pd.DataFrame(columns=COLONNES_FIXES),  # values$df_nag_fixe
    }
    for cle, valeur in valeurs_par_defaut.items():
        if cle not in st.session_state:
            st.session_state[cle] = valeur


def choisir_club(donnees, nom_club):
    """Enregistre le club choisi et prépare les listes de nageurs (bouton « Lancer l'optimisation »)."""
    clubs = donnees["clubs"]
    ids = clubs.loc[clubs["nom_club"] == nom_club, "id_club"].tolist()
    nageurs = donnees["nageurs"]
    du_club = nageurs[nageurs["ID_CLUB"].isin(ids)]

    st.session_state["club"] = nom_club
    st.session_state["club_ids"] = ids
    st.session_state["noms_club"] = sorted(du_club["NOM"].dropna().unique().tolist())
    st.session_state["nageurs_club"] = sorted(du_club["NOM_PRE"].dropna().unique().tolist())
    st.session_state["nageurs_fixes"] = pd.DataFrame(columns=COLONNES_FIXES)
