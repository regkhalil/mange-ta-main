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

    # Mark as navigation event (not refresh)
    st.session_state.from_navigation = True

    # Determine which page to use for forced reload
    current_page = st.session_state.get("current_detail_page", "a")
    next_page = "b" if current_page == "a" else "a"

    # Stocker la nouvelle page
    st.session_state.current_detail_page = next_page

    # Navigate to alternate page - switch immédiatement
    st.switch_page(f"pages/recipe_detail_{next_page}.py")
