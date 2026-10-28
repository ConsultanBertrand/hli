# Optimisation d'équipe — natation masters (HLi)

Migration en Python/Streamlit de l'application Shiny d'optimisation des équipes de natation masters.

## Lancer en local

```bash
conda activate monapp
pip install -r requirements.txt
streamlit run app.py
```

## Organisation

- `app.py` : point d'entrée, navigation et style
- `pages/` : une page par onglet (Accueil, Sélection de l'équipe, Points)
- `utils/` : chargement des données et calculs
- `data/` : fichiers de données (tables de cotation FFN, nageurs, performances, clubs)
- `assets/` : logo et images
