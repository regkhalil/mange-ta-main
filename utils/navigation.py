"""Helper de navigation pour alterner entre les pages de détail."""

import streamlit as st


def navigate_to_recipe(recipe_id: int):
    """
    Navigue vers le détail d'une recette en alternant entre detail_a et detail_b.
    Force le scroll en haut en changeant de page.

    Args:
        recipe_id: ID de la recette à afficher
    """
    # Stocker l'ID de la recette
    st.session_state.recipe_id_to_view = recipe_id

    # Déterminer quelle page utiliser pour forcer le rechargement
    current_page = st.session_state.get("current_detail_page", "a")
    next_page = "b" if current_page == "a" else "a"

    # Stocker la nouvelle page
    st.session_state.current_detail_page = next_page

    # Naviguer vers la page alternée
    st.switch_page(f"pages/recipe_detail_{next_page}.py")
