"""Page de détail A - Recipe detail page (version A for alternating navigation)."""

import streamlit as st

from services.data_loader import load_recipes
from services.recommender import get_recommender
from utils.navigation import navigate_to_recipe
from utils.recipe_detail import render_recipe_detail

st.set_page_config(page_title="Détail Recette - Mangetamain", page_icon="📖", layout="wide")

# Forcer le mode light partout
st.markdown(
    """
<style>
    /* Forcer le thème light */
    :root {
        color-scheme: light !important;
    }
    
    /* Fond blanc partout */
    body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], 
    .main, section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
    }
    
    /* Masquer sidebar */
    [data-testid="stSidebar"], [data-testid="stSidebarCollapseButton"] {
        display: none !important;
    }
    
    /* Texte noir pour TOUS les éléments */
    *, h1, h2, h3, h4, h5, h6, p, span, div, td, th, label, li {
        color: #000000 !important;
    }
    
    /* Exception: texte blanc dans les cartes de recettes similaires (fond noir) */
    .recipe-similar-card-dark h3 {
        color: #ffffff !important;
    }
    .recipe-similar-card-dark p {
        color: #b0b0b0 !important;
    }
    .recipe-similar-card-dark .recipe-rating-stars {
        color: #ffc107 !important;
    }
    .recipe-similar-card-dark .recipe-rating-text {
        color: #ffffff !important;
    }
    
    /* Tables avec fond blanc */
    table, thead, tbody, tr, td, th {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Markdown en noir */
    [data-testid="stMarkdown"], [data-testid="stMarkdown"] * {
        color: #000000 !important;
    }
    
    /* Boutons style rose comme "Rechercher" */
    button[kind="secondary"], button[kind="primary"], button {
        background: linear-gradient(135deg, #ff4d6d 0%, #ff758f 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 6px rgba(255, 77, 109, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(255, 77, 109, 0.4) !important;
    }
    button p, button div, button span {
        color: #ffffff !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

# AUTO-REDIRECT ON PAGE REFRESH
# Ne rediriger QUE si on n'a ni navigation flag ni recipe_id
if "from_navigation" not in st.session_state and "recipe_id_to_view" not in st.session_state:
    st.switch_page("app.py")


def main():
    """Affiche le détail d'une recette."""
    # Clear navigation flag after verification
    if "from_navigation" in st.session_state:
        del st.session_state.from_navigation

    recipe_id = st.session_state.get("recipe_id_to_view") or st.query_params.get("id")

    if not recipe_id:
        st.error("❌ Aucune recette spécifiée")
        if st.button("← Retour à la recherche"):
            st.switch_page("app.py")
        return

    try:
        recipe_id = int(recipe_id)
        st.session_state.current_recipe_id = recipe_id
    except ValueError:
        st.error("❌ ID de recette invalide")
        if st.button("← Retour à la recherche"):
            st.switch_page("app.py")
        return

    recipes_df = load_recipes()
    recommender = get_recommender(recipes_df)

    render_recipe_detail(recipes_df, recommender, recipe_id, on_view_similar=navigate_to_recipe)


if __name__ == "__main__":
    main()
