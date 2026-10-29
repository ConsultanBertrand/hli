"""Onglet 3 : Points — score d'une performance individuelle."""

import pandas as pd
import streamlit as st

from utils.cotation import calcul_score, format_temps
from utils.donnees import charger_donnees
from utils.interface import en_tete, score, section

donnees = charger_donnees()
nageurs = donnees["nageurs"]

en_tete("Calcul des points", surtitre="Outil",
        sous_titre="Convertissez un temps en points FFN, avec le coefficient d'âge masters.")

# Liste des nageurs : ceux du club choisi s'il y en a un, sinon tous
if st.session_state.get("nageurs_club"):
    liste_nageurs = [""] + st.session_state["nageurs_club"]
else:
    liste_nageurs = [""] + sorted(nageurs["NOM_PRE"].dropna().unique().tolist())

liste_ages = list(range(25, 101))
liste_epreuves = donnees["perfs"]["CODE_EPREUVE"].dropna().unique().tolist()

# Valeurs initiales (et remise à zéro si une valeur n'est plus dans sa liste)
if st.session_state.get("pts_nom") not in liste_nageurs:
    st.session_state["pts_nom"] = ""
st.session_state.setdefault("pts_sexe", "")
st.session_state.setdefault("pts_age", 25)
if st.session_state.get("pts_epreuve") not in liste_epreuves:
    st.session_state["pts_epreuve"] = "BRA_100" if "BRA_100" in liste_epreuves else liste_epreuves[0]
st.session_state.setdefault("pts_temps", 0.0)


def remplir_sexe_et_age():
    """Quand on choisit un nageur, son sexe et son âge sont remplis automatiquement."""
    ligne = nageurs[nageurs["NOM_PRE"] == st.session_state["pts_nom"]]
    if ligne.empty:
        return
    sexe = ligne.iloc[0]["SEXE"]
    age = ligne.iloc[0]["AGE_BIS"]
    if sexe in ("F", "M"):
        st.session_state["pts_sexe"] = sexe
    if pd.notna(age) and int(age) in liste_ages:
        st.session_state["pts_age"] = int(age)


with st.container(border=True):
    section("Performance")
    col_nom, col_sexe, col_age = st.columns([4, 2, 2])
    with col_nom:
        st.selectbox("Nageur", liste_nageurs, key="pts_nom", on_change=remplir_sexe_et_age,
                     help="Facultatif : remplit automatiquement le sexe et l'âge.")
    with col_sexe:
        st.selectbox("Sexe", ["", "F", "M"], key="pts_sexe",
                     format_func={"": "—", "F": "Femme", "M": "Homme"}.get)
    with col_age:
        st.selectbox("Âge", liste_ages, key="pts_age")
    col_epreuve, col_temps = st.columns([4, 4])
    with col_epreuve:
        st.selectbox("Épreuve", liste_epreuves, key="pts_epreuve")
    with col_temps:
        st.number_input("Temps (secondes)", min_value=0.0, max_value=10000.0, step=0.01,
                        format="%.2f", key="pts_temps")

temps = st.session_state["pts_temps"]
sexe = st.session_state["pts_sexe"]

st.write("")
if not sexe:
    st.info("Choisissez un nageur ou renseignez le sexe.", icon=":material/info:")
elif temps <= 0:
    st.info("Saisissez un temps supérieur à 0.", icon=":material/timer:")
else:
    resultat = calcul_score(donnees, sexe, st.session_state["pts_age"],
                            st.session_state["pts_epreuve"], temps)
    if resultat["points"] is None:
        st.warning("Impossible de calculer le score : coefficient d'âge ou table de cotation "
                   "introuvable pour cette épreuve et cette catégorie.")
    else:
        section("Résultat", f"{st.session_state['pts_epreuve']} en {format_temps(temps)}")
        score(f"{int(resultat['points'])}")
    st.write("")
    c1, c2, c3 = st.columns(3)
    c1.metric("Catégorie", resultat["categorie"] or "—")
    c2.metric("Coefficient d'âge", f"{resultat['coefficient']:.4f}"
              if resultat["coefficient"] is not None and not pd.isna(resultat["coefficient"]) else "—")
    c3.metric("Temps normé", f"{resultat['temps_norme']:.2f} s" if resultat["temps_norme"] else "—",
              help="Temps divisé par le coefficient d'âge, comparé à la table de cotation")
