"""Onglet 1 : Accueil — présentation et choix du club."""

from pathlib import Path

import streamlit as st

from utils.donnees import charger_donnees
from utils.etat import choisir_club
from utils.interface import bandeau, etape, pied_de_page, section

DEPARTEMENT_PAR_DEFAUT = "Hauts-de-Seine"
CLUB_PAR_DEFAUT = "CSM PUTEAUX"
GIF = Path(__file__).resolve().parent.parent / "assets" / "gif_natation1.gif"

donnees = charger_donnees()
clubs = donnees["clubs"]

bandeau(
    "Composez la meilleure équipe de votre club",
    "À partir de l'historique des performances FFN, l'application sélectionne les nageurs "
    "et les épreuves qui maximisent les points de votre équipe masters, relais compris.",
    surtitre="Natation masters · Interclubs",
)

col_choix, col_visuel = st.columns([5, 4], gap="large")

with col_choix:
    with st.container(border=True):
        section("Choisir votre club")
        departements = sorted(clubs["Departement"].dropna().unique().tolist())
        index_dep = departements.index(DEPARTEMENT_PAR_DEFAUT) if DEPARTEMENT_PAR_DEFAUT in departements else 0
        departement = st.selectbox("Département", departements, index=index_dep)

        liste_clubs = sorted(clubs.loc[clubs["Departement"] == departement, "nom_club"].dropna().unique().tolist())
        club_actuel = st.session_state.get("club") or CLUB_PAR_DEFAUT
        index_club = liste_clubs.index(club_actuel) if club_actuel in liste_clubs else 0
        club = st.selectbox("Club", liste_clubs, index=index_club if liste_clubs else None)

        nb_nageurs = 0
        if club:
            ids = clubs.loc[clubs["nom_club"] == club, "id_club"]
            nb_nageurs = donnees["nageurs"]["ID_CLUB"].isin(ids).sum()
            st.caption(f"{nb_nageurs} nageurs masters référencés dans ce club")

        if st.button("Lancer l'optimisation", icon=":material/arrow_forward:", type="primary",
                     width="stretch"):
            if club:
                choisir_club(donnees, club)
                st.switch_page("pages/selection_equipe.py")
            else:
                st.error("Veuillez choisir un club.")

with col_visuel:
    if GIF.exists():
        st.image(str(GIF), width="stretch")
    else:
        c1, c2 = st.columns(2)
        c1.metric("Clubs", len(clubs))
        c2.metric("Nageurs", len(donnees["nageurs"]))
        st.metric("Performances analysées", f"{len(donnees['perfs']):,}".replace(",", " "))

st.write("")
section("Comment ça marche ?")
e1, e2, e3 = st.columns(3)
with e1:
    etape(1, "Choisissez votre club",
          "Sélectionnez le département puis le club : ses nageurs et leurs performances sont chargés.")
with e2:
    etape(2, "Ajustez les paramètres",
          "Période d'historique, meilleure ou dernière performance, nageurs disponibles ou imposés.")
with e3:
    etape(3, "Obtenez l'équipe optimale",
          "10 épreuves individuelles, relais 10×50 NL et 4×50 4 nages, exportables en CSV.")

pied_de_page()
