"""Point d'entrée de l'application : configuration, style commun et navigation.

Lancer en local :  streamlit run app.py
"""

from pathlib import Path

import streamlit as st

from utils.donnees import DOSSIER_DATA, fichiers_manquants
from utils.etat import initialiser_etat
from utils.interface import appliquer_style

RACINE = Path(__file__).resolve().parent
LOGO = RACINE / "assets" / "LOGO_HLI_BLANC.jpg"
ICONE = RACINE / "assets" / "apercu_favicon.png"

st.set_page_config(page_title="HLi Natation",
                    page_icon=str(ICONE) if ICONE.exists() else ":material/pool:",
                    layout="wide",
                    initial_sidebar_state="expanded")
appliquer_style()

if LOGO.exists():
    st.logo(str(LOGO), size="large")

initialiser_etat()

# Arrêt propre si les fichiers de données ne sont pas en place
manquants = fichiers_manquants()
if manquants:
    st.error(
        "Fichiers de données introuvables dans le dossier "
        f"`{DOSSIER_DATA}` :\n\n" + "\n".join(f"- {nom}" for nom in manquants)
        + "\n\nCopiez-y le contenu du dossier `data/` de l'application Shiny."
    )
    st.stop()

pages = [
    st.Page("pages/accueil.py", title="Accueil", icon=":material/home:", default=True),
    st.Page("pages/selection_equipe.py", title="Sélection de l'équipe", icon=":material/groups:"),
    st.Page("pages/points.py", title="Calcul des points", icon=":material/calculate:"),
]
st.navigation(pages, position="top").run()
