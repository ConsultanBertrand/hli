"""Onglet 2 : Sélection de l'équipe — épreuves individuelles, relais 10x50 NL et 4x50 4 nages."""

from datetime import date

import pandas as pd
import streamlit as st

from utils.donnees import charger_donnees
from utils.etat import COLONNES_FIXES
from utils.optimisation import (EPREUVES_INDIVIDUELLES, ajouter_nageur_fixe, creer_nageur_fixe,
                                formater_points, optimiser_equipe)
from utils.relais import relais_4x50, relais_10x50
from utils.interface import en_tete, score, section, tableau

donnees = charger_donnees()

# ---------------------------------------------------------------------------
# Club obligatoire (choisi dans l'Accueil)
# ---------------------------------------------------------------------------
if not st.session_state.get("club"):
    st.warning("Choisissez d'abord un club dans l'Accueil, puis cliquez sur « Lancer l'optimisation ».")
    if st.button("Aller à l'Accueil"):
        st.switch_page("pages/accueil.py")
    st.stop()

club = st.session_state["club"]
club_ids = tuple(st.session_state["club_ids"])
nageurs_club = st.session_state["nageurs_club"]

# ---------------------------------------------------------------------------
# Calculs mis en cache (relancés seulement si un paramètre change)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Optimisation en cours…")
def calculer_equipe(club_ids, debut, fin, methode, preselection, fixes):
    return optimiser_equipe(charger_donnees(), list(club_ids), debut, fin, methode,
                            list(preselection), fixes)


@st.cache_data(show_spinner="Calcul du relais 10x50…")
def calculer_relais_10x50(club_ids, debut, fin, methode, noms):
    return relais_10x50(charger_donnees(), list(club_ids), debut, fin, methode, list(noms))


@st.cache_data(show_spinner="Calcul du relais 4x50 4 nages…")
def calculer_relais_4x50(club_ids, debut, fin, noms):
    return relais_4x50(charger_donnees(), list(club_ids), debut, fin, list(noms))


# ---------------------------------------------------------------------------
# Barre latérale : nageurs pré-sélectionnés, période, méthode
# ---------------------------------------------------------------------------
def cle_case(nom):
    return f"presel|{club}|{nom}"


def cocher_tout(valeur):
    for nom in nageurs_club:
        st.session_state[cle_case(nom)] = valeur


METHODES = {"max": "Meilleure performance", "tail": "Dernière performance"}

with st.sidebar:
    st.subheader("Paramètres")
    aujourd_hui = date.today()
    periode = st.date_input(
        "Période d'historique",
        value=(date(aujourd_hui.year - 3, 1, 1), aujourd_hui),
        min_value=date(2005, 1, 1), max_value=aujourd_hui, format="DD/MM/YYYY",
        help="Seules les performances réalisées sur cette période sont prises en compte.",
    )
    methode = st.segmented_control(
        "Performance retenue", options=list(METHODES), format_func=METHODES.get,
        default="max", width="stretch",
    ) or "max"

    st.subheader("Nageurs disponibles")
    for nom in nageurs_club:  # toutes les cases cochées au départ
        st.session_state.setdefault(cle_case(nom), True)
    nb_coches = sum(st.session_state[cle_case(nom)] for nom in nageurs_club)
    with st.expander(f"{nb_coches} sur {len(nageurs_club)} sélectionnés", expanded=nb_coches < 10):
        col_tout, col_rien = st.columns(2)
        col_tout.button("Tous", on_click=cocher_tout, args=(True,), width="stretch")
        col_rien.button("Aucun", on_click=cocher_tout, args=(False,), width="stretch")
        preselection = [nom for nom in nageurs_club if st.checkbox(nom, key=cle_case(nom))]

    st.divider()
    if st.button("Changer de club", icon=":material/swap_horiz:", width="stretch"):
        st.switch_page("pages/accueil.py")

if not isinstance(periode, (tuple, list)) or len(periode) != 2:
    st.info("Choisissez une date de début et une date de fin dans la barre latérale.")
    st.stop()
debut, fin = periode

fixes = st.session_state.get("nageurs_fixes", pd.DataFrame(columns=COLONNES_FIXES))

def fixer_nageur():
    """Appelée au clic sur « Fixer le nageur », avant le recalcul de la page."""
    nom = st.session_state["fix_nag"]
    epreuve = st.session_state["fix_epr"]
    temps = st.session_state["fix_temps"]
    if nom == " " and epreuve == " ":
        return
    if epreuve == " ":
        st.session_state["message_fixe"] = ("erreur", f"Oups ! Veuillez choisir l'épreuve sur laquelle vous fixez {nom}.")
        return
    if nom == " ":
        st.session_state["message_fixe"] = ("erreur", f"Oups ! Veuillez choisir le nageur que vous voulez fixer sur l'épreuve {epreuve}.")
        return
    ligne = creer_nageur_fixe(donnees, nom, epreuve, temps)
    if ligne is None:
        st.session_state["message_fixe"] = ("erreur", f"Nageur introuvable : {nom}.")
        return
    st.session_state["nageurs_fixes"] = ajouter_nageur_fixe(st.session_state["nageurs_fixes"], ligne)
    st.session_state["message_fixe"] = ("ok", f"{nom} a bien été fixé(e) pour l'épreuve {epreuve}.")
    # Remise à zéro des champs
    st.session_state["fix_nag"] = " "
    st.session_state["fix_epr"] = " "
    st.session_state["fix_temps"] = 0.0


def retirer_fixes():
    st.session_state["nageurs_fixes"] = pd.DataFrame(columns=COLONNES_FIXES)



# ---------------------------------------------------------------------------
# Calculs
# ---------------------------------------------------------------------------
equipe = calculer_equipe(club_ids, debut, fin, methode, tuple(preselection), fixes)
noms_equipe = tuple(equipe["tableau"]["Nom_Prénom"]) if not equipe["erreur"] else ()
relais = calculer_relais_10x50(club_ids, debut, fin, methode, noms_equipe) if noms_equipe else None
relais4 = calculer_relais_4x50(club_ids, debut, fin, noms_equipe) if noms_equipe else None

# ---------------------------------------------------------------------------
# En-tête et indicateurs
# ---------------------------------------------------------------------------
en_tete(club, surtitre="Sélection de l'équipe",
        sous_titre=f"Performances du {debut:%d/%m/%Y} au {fin:%d/%m/%Y} · {METHODES[methode].lower()}")

message = st.session_state.pop("message_fixe", None)
if message:
    type_message, texte = message
    if type_message == "ok":
        st.toast(texte, icon=":material/check_circle:")
    else:
        st.error(texte)


def valeur_relais(resultat):
    return resultat["points"] if resultat and not resultat["erreur"] else "—"


k1, k2, k3, k4 = st.columns(4)
k1.metric("Épreuves individuelles", formater_points(equipe["score"]) if not equipe["erreur"] else "—",
          help="Somme des points des 10 épreuves individuelles")
k2.metric("Relais 10×50 NL", valeur_relais(relais))
k3.metric("Relais 4×50 4 nages", valeur_relais(relais4))
k4.metric("Nageurs disponibles", f"{len(preselection)} / {len(nageurs_club)}",
          help="Nageurs cochés dans la barre latérale")

st.write("")
onglet_ind, onglet_10, onglet_4 = st.tabs(
    [":material/person: Épreuves individuelles", ":material/waves: Relais 10×50 NL",
     ":material/pool: Relais 4×50 4 nages"])

# ---------------------------------------------------------------------------
# 1. Épreuves individuelles
# ---------------------------------------------------------------------------
with onglet_ind:
    if equipe["erreur"]:
        st.error(equipe["erreur"], icon=":material/error:")
    else:
        col_score, col_export = st.columns([3, 1], vertical_alignment="center")
        with col_score:
            score(formater_points(equipe["score"]))
        with col_export:
            csv = equipe["tableau"].to_csv(sep=";", index=False).encode("cp1252", errors="replace")
            st.download_button("Exporter en CSV", data=csv, file_name="Optimisation.csv",
                               mime="text/csv", icon=":material/download:", width="stretch")
        tableau(equipe["tableau"])

    with st.container(border=True):
        section("Imposer un nageur sur une épreuve",
                "Le nageur et l'épreuve sont retirés de l'optimisation. Le temps est optionnel.")
        col_nag, col_epr, col_temps, col_bouton = st.columns([3, 2, 2, 2], vertical_alignment="bottom")
        with col_nag:
            st.selectbox("Nageur", [" "] + nageurs_club, key="fix_nag")
        with col_epr:
            st.selectbox("Épreuve", [" "] + sorted(EPREUVES_INDIVIDUELLES), key="fix_epr")
        with col_temps:
            st.number_input("Temps (secondes)", min_value=0.0, max_value=10000.0, step=0.01,
                            format="%.2f", key="fix_temps")
        with col_bouton:
            st.button("Fixer le nageur", icon=":material/push_pin:", on_click=fixer_nageur,
                      type="primary", width="stretch")

        if not fixes.empty:
            apercu = fixes[["NOM_PRE", "EPREUVE", "temps", "score_nag"]].rename(columns={
                "NOM_PRE": "Nageur fixé", "EPREUVE": "Épreuve", "temps": "Temps (s)",
                "score_nag": "Points"})
            tableau(apercu)
            st.button("Retirer les nageurs fixés", icon=":material/close:", on_click=retirer_fixes)

# ---------------------------------------------------------------------------
# 2. Relais (calculés à partir des nageurs retenus en individuel)
# ---------------------------------------------------------------------------
with onglet_10:
    if relais is None:
        st.info("Le relais sera calculé une fois l'équipe individuelle constituée.")
    elif relais["erreur"]:
        st.error(relais["erreur"])
    else:
        score(relais["points"])
        st.caption(f"Temps cumulé : {relais['temps_total']} · composé des 10 nageurs de l'équipe individuelle")
        tableau(relais["tableau"], colonnes_points=())
        if relais["sans_temps"]:
            st.warning("Sans 50 NL sur la période (compté 0 s, ce qui avantage le relais) : "
                       + ", ".join(relais["sans_temps"]), icon=":material/warning:")

with onglet_4:
    if relais4 is None:
        st.info("Le relais sera calculé une fois l'équipe individuelle constituée.")
    elif relais4["erreur"]:
        st.error(relais4["erreur"])
    else:
        score(relais4["points"])
        st.caption(f"Temps cumulé : {relais4['temps_total']} · somme des âges : "
                   f"{relais4['somme_ages']} ans ({relais4['categorie']}) · "
                   f"coefficient : {relais4['coefficient']:.4f}")
        tableau(relais4["tableau"], colonnes_points=())
        if not relais4["complet"]:
            st.warning("Aucune combinaison n'a un temps pour les 4 nageurs : "
                       "les points sont estimés à partir des temps disponibles.")
