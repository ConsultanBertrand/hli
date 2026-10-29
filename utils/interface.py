"""Charte graphique et composants d'interface réutilisables.

Toutes les couleurs sont définies ici : pour modifier le thème, il suffit de changer
les valeurs du dictionnaire COULEURS (et celles de .streamlit/config.toml).
"""

import html

import pandas as pd
import streamlit as st

COULEURS = {
    "bleu": "#0069A4",         # couleur principale HLi
    "bleu_fonce": "#00466E",
    "bleu_clair": "#E6F1F8",
    "magenta": "#D13983",      # accent HLi, réservé aux scores
    "magenta_clair": "#FBEAF2",
    "texte": "#1B2A36",
    "texte_doux": "#5B6B78",
    "bordure": "#E1E8EE",
    "fond": "#F4F7FA",
}

POINTS_MAX = 1400  # échelle des barres de points dans les tableaux


def appliquer_style():
    """Feuille de style commune, à appeler une fois dans app.py."""
    c = COULEURS
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Police du texte. Les icônes ne sont pas visées : elles utilisent une police
   spéciale (Material Symbols) qui transforme des mots comme « home » en pictogrammes. */
html, body, .stApp {{
    font-family: 'Inter', 'Segoe UI', sans-serif;
}}
[data-testid="stIconMaterial"], .material-symbols-rounded, .material-icons {{
    font-family: 'Material Symbols Rounded' !important;
}}

/* Marge haute suffisante pour passer sous la barre de navigation fixe */
.block-container, [data-testid="stMainBlockContainer"] {{
    padding-top: 5.5rem; padding-bottom: 3rem; max-width: 1280px;
}}

/* Titres */
h1, h2, h3 {{ color: {c['texte']}; letter-spacing: -0.01em; }}
h1 {{ font-weight: 700; }}
h2, h3 {{ font-weight: 600; }}

/* En-tête de page */
.hli-entete {{ margin-bottom: 1.4rem; }}
.hli-surtitre {{
    text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.75rem;
    font-weight: 600; color: {c['bleu']}; margin-bottom: 0.25rem;
}}
.hli-titre {{ font-size: 2rem; font-weight: 700; color: {c['texte']}; line-height: 1.2; margin: 0; }}
.hli-sous-titre {{ color: {c['texte_doux']}; font-size: 1rem; margin-top: 0.35rem; }}

/* Bandeau d'accueil */
.hli-bandeau {{
    background: linear-gradient(120deg, {c['bleu_fonce']} 0%, {c['bleu']} 60%, #2C8FC7 100%);
    border-radius: 1rem; padding: 2.4rem 2.6rem; color: white; margin-bottom: 1.6rem;
    box-shadow: 0 10px 30px rgba(0, 70, 110, 0.18);
}}
.hli-bandeau .hli-surtitre {{ color: rgba(255,255,255,0.75); }}
.hli-bandeau h1 {{ color: white; font-size: 2.3rem; margin: 0 0 0.6rem 0; padding: 0; }}
.hli-bandeau p {{ color: rgba(255,255,255,0.88); font-size: 1.05rem; max-width: 46rem; margin: 0; }}

/* Titres de section */
.hli-section {{ display: flex; align-items: baseline; gap: 0.6rem; margin: 0.4rem 0 0.8rem 0; }}
.hli-section-titre {{ font-size: 1.15rem; font-weight: 600; color: {c['texte']}; }}
.hli-section-texte {{ font-size: 0.9rem; color: {c['texte_doux']}; }}

/* Cartes (st.container(border=True)) */
[data-testid="stVerticalBlockBorderWrapper"] {{
    background: white; border-color: {c['bordure']} !important;
    box-shadow: 0 1px 2px rgba(16, 42, 67, 0.04);
}}

/* Indicateurs (st.metric) */
[data-testid="stMetric"] {{
    background: white; border: 1px solid {c['bordure']}; border-radius: 0.8rem;
    padding: 1rem 1.2rem; box-shadow: 0 1px 2px rgba(16, 42, 67, 0.04);
}}
[data-testid="stMetricLabel"] p {{
    font-size: 0.8rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.05em; color: {c['texte_doux']};
}}
[data-testid="stMetricValue"] {{ font-size: 1.9rem; font-weight: 700; color: {c['texte']}; }}

/* Score mis en avant */
.hli-score {{
    display: inline-flex; align-items: baseline; gap: 0.4rem;
    background: {c['magenta_clair']}; color: {c['magenta']};
    border-radius: 999px; padding: 0.35rem 1rem; font-weight: 700; font-size: 1.25rem;
}}
.hli-score span {{ font-size: 0.85rem; font-weight: 600; opacity: 0.85; }}

/* Étiquettes */
.hli-badge {{
    display: inline-block; background: {c['bleu_clair']}; color: {c['bleu']};
    border-radius: 999px; padding: 0.15rem 0.7rem; font-size: 0.8rem; font-weight: 600;
}}

/* Étapes (page d'accueil) */
.hli-etape-numero {{
    width: 2rem; height: 2rem; border-radius: 50%; background: {c['bleu_clair']};
    color: {c['bleu']}; font-weight: 700; display: flex; align-items: center;
    justify-content: center; margin-bottom: 0.6rem;
}}
.hli-etape-titre {{ font-weight: 600; color: {c['texte']}; margin-bottom: 0.25rem; }}
.hli-etape-texte {{ color: {c['texte_doux']}; font-size: 0.92rem; }}

/* Onglets */
.stTabs [data-baseweb="tab-list"] {{ gap: 0.3rem; border-bottom: 1px solid {c['bordure']}; }}
.stTabs [data-baseweb="tab"] {{ padding: 0.6rem 1rem; font-weight: 500; color: {c['texte_doux']}; }}
.stTabs [aria-selected="true"] {{ color: {c['bleu']}; font-weight: 600; }}

/* Boutons */
.stButton > button, .stDownloadButton > button {{ font-weight: 600; transition: all 0.15s ease; }}
.stButton > button:hover, .stDownloadButton > button:hover {{ transform: translateY(-1px); }}

/* Barre latérale */
[data-testid="stSidebar"] {{ border-right: 1px solid {c['bordure']}; }}
[data-testid="stSidebar"] h3 {{ font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.06em; color: {c['texte_doux']}; }}

/* Pied de page */
.hli-pied {{
    margin-top: 2.5rem; padding-top: 1rem; border-top: 1px solid {c['bordure']};
    display: flex; justify-content: space-between; flex-wrap: wrap; gap: 0.8rem;
    color: {c['texte_doux']}; font-size: 0.85rem;
}}
.hli-pied a {{ color: {c['bleu']}; text-decoration: none; margin-right: 1.2rem; }}

#MainMenu, footer {{ visibility: hidden; }}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Composants
# ---------------------------------------------------------------------------

def _e(texte):
    return html.escape(str(texte))


def en_tete(titre, sous_titre=None, surtitre=None):
    """Titre de page avec surtitre et phrase d'explication."""
    st.markdown(
        "<div class='hli-entete'>"
        + (f"<div class='hli-surtitre'>{_e(surtitre)}</div>" if surtitre else "")
        + f"<p class='hli-titre'>{_e(titre)}</p>"
        + (f"<div class='hli-sous-titre'>{_e(sous_titre)}</div>" if sous_titre else "")
        + "</div>",
        unsafe_allow_html=True,
    )


def bandeau(titre, texte, surtitre=None):
    """Grand bandeau bleu de la page d'accueil."""
    st.markdown(
        "<div class='hli-bandeau'>"
        + (f"<div class='hli-surtitre'>{_e(surtitre)}</div>" if surtitre else "")
        + f"<h1>{_e(titre)}</h1><p>{_e(texte)}</p></div>",
        unsafe_allow_html=True,
    )


def section(titre, texte=None):
    """Titre de section, éventuellement suivi d'une courte explication."""
    st.markdown(
        f"<div class='hli-section'><span class='hli-section-titre'>{_e(titre)}</span>"
        + (f"<span class='hli-section-texte'>{_e(texte)}</span>" if texte else "")
        + "</div>",
        unsafe_allow_html=True,
    )


def score(valeur, unite="points"):
    """Pastille magenta pour afficher un score."""
    st.markdown(f"<div class='hli-score'>{_e(valeur)} <span>{_e(unite)}</span></div>",
                unsafe_allow_html=True)


def etape(numero, titre, texte):
    """Carte d'étape numérotée (page d'accueil)."""
    with st.container(border=True):
        st.markdown(
            f"<div class='hli-etape-numero'>{numero}</div>"
            f"<div class='hli-etape-titre'>{_e(titre)}</div>"
            f"<div class='hli-etape-texte'>{_e(texte)}</div>",
            unsafe_allow_html=True,
        )


def pied_de_page():
    st.markdown(
        "<div class='hli-pied'><div>"
        "<a href='http://www.groupe-hli.com/accueil/' target='_blank'>Site Internet HLI</a>"
        "<a href='https://www.linkedin.com/company/hli-group/' target='_blank'>LinkedIn HLI</a>"
        "</div><div>© HLI — Optimisation d'équipe natation masters</div></div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Tableaux
# ---------------------------------------------------------------------------

def points_en_nombre(serie):
    """'1 234' -> 1234 (les tableaux de calcul contiennent des points formatés en texte)."""
    return pd.to_numeric(serie.astype(str).str.replace(r"\s", "", regex=True), errors="coerce")


def tableau(df, colonnes_points=("Points",), hauteur=None):
    """Tableau avec barres de progression pour les points."""
    df = df.copy()
    config = {}
    for col in colonnes_points:
        if col in df.columns:
            df[col] = points_en_nombre(df[col])
            config[col] = st.column_config.ProgressColumn(
                col, min_value=0, max_value=POINTS_MAX, format="%d")
    # En-têtes lisibles à l'écran (l'export CSV garde les noms d'origine)
    df = df.rename(columns={"Nom_Prénom": "Nageur", "Epreuve": "Épreuve"})
    options = {"hide_index": True, "width": "stretch", "column_config": config}
    if hauteur:
        options["height"] = hauteur
    st.dataframe(df, **options)
