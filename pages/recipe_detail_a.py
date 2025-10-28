"""Page de détail A - Recipe detail page (version A for alternating navigation)."""

import streamlit as st

from services.data_loader import load_recipes
from services.recommender import get_recommender
from utils.navigation import navigate_to_recipe
from utils.recipe_detail import render_recipe_detail

st.set_page_config(page_title="Détail Recette - Mangetamain", page_icon="📖", layout="wide")

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
