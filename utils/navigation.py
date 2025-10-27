"""Helper de navigation pour les pages de détail."""

import streamlit as st


def navigate_to_recipe(recipe_id: int):
    """
    Navigue vers le détail d'une recette.

    Args:
        recipe_id: ID de la recette à afficher
    """
    # Stocker l'ID de la recette
    st.session_state.recipe_id_to_view = recipe_id

    # Naviguer vers la page de détail
    st.switch_page("pages/recipe_detail.py")
