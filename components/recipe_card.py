"""
Composant de carte de recette pour Streamlit.
"""

import pandas as pd
import streamlit as st


def render_recipe_card(recipe: pd.Series, show_similarity: bool = False, similarity_score: float = None):
    """
    Affiche une carte de recette.

    Args:
        recipe: Série pandas contenant les données de la recette
        show_similarity: Afficher ou non le score de similarité
        similarity_score: Score de similarité (si show_similarity=True)
    """
    # Couleurs pour les grades nutritionnels
    grade_colors = {
        "A": "#038141",  # Vert foncé
        "B": "#85BB2F",  # Vert clair
        "C": "#FECB02",  # Jaune
        "D": "#EE8100",  # Orange
        "E": "#E63E11",  # Rouge
    }

    with st.container():
        # Récupérer le nom de la recette et le limiter
        recipe_name = recipe.get("name", f"Recette #{int(recipe['id'])}")
        display_name = recipe_name if len(recipe_name) <= 50 else recipe_name[:47] + "..."

        st.markdown(
            f"""
        <div style="
            padding: 1.5rem; 
            border: 1px solid #e0e0e0; 
            border-radius: 12px; 
            background-color: white;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            height: 100%;
        ">
            <h3 style="
                margin-top: 0; 
                color: #1f1f1f;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            ">
                🍽️ {display_name}
            </h3>
        """,
            unsafe_allow_html=True,
        )

        # Badges principaux
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("⏱️ Temps", f"{int(recipe['totalTime'])} min")
        with col2:
            st.metric("🥕 Ingrédients", int(recipe["ingredientCount"]))
        with col3:
            st.metric("🔥 Calories", f"{int(recipe['calories'])} kcal")

        # Ligne pour score nutritionnel et végétarien
        col_nutr, col_veg = st.columns([2, 1])

        with col_nutr:
            # Score nutritionnel avec couleur selon le grade
            if pd.notna(recipe.get("nutrition_score")) and pd.notna(recipe.get("nutrition_grade")):
                grade = recipe["nutrition_grade"]
                score = recipe["nutrition_score"]
                color = grade_colors.get(grade, "#666666")
                st.markdown(
                    f"""
                <div style="
                    display: inline-block;
                    padding: 0.5rem 1rem;
                    border-radius: 8px;
                    background-color: {color};
                    color: white;
                    font-weight: bold;
                    margin-top: 0.5rem;
                ">
                    Nutri-Score: {grade} ({score:.0f}/100)
                </div>
                """,
                    unsafe_allow_html=True,
                )

        with col_veg:
            # Badge végétarien
            if recipe.get("is_vegetarian", False):
                st.markdown(
                    """
                <div style="
                    display: inline-block;
                    padding: 0.5rem 1rem;
                    border-radius: 8px;
                    background-color: #85BB2F;
                    color: white;
                    font-weight: bold;
                    margin-top: 0.5rem;
                ">
                    🌱 Végétarien
                </div>
                """,
                    unsafe_allow_html=True,
                )

        # Score de similarité
        if show_similarity and similarity_score is not None:
            st.progress(similarity_score)
            st.caption(f"Similarité: {similarity_score:.1%}")

        # Boutons d'action
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("✨ Voir similaires", key=f"similar_{recipe['id']}", use_container_width=True):
                st.session_state.selected_recipe_id = recipe["id"]
                st.switch_page("pages/2_Recommandations.py")

        with col_btn2:
            # Toggle favoris
            if "favorites" not in st.session_state:
                st.session_state.favorites = set()

            is_favorite = recipe["id"] in st.session_state.favorites
            if st.button(
                "❤️ Retirer" if is_favorite else "🤍 Favoris", key=f"fav_{recipe['id']}", use_container_width=True
            ):
                if is_favorite:
                    st.session_state.favorites.remove(recipe["id"])
                else:
                    st.session_state.favorites.add(recipe["id"])
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


def render_recipe_grid(recipes_df: pd.DataFrame, show_similarity: bool = False):
    """
    Affiche une grille de cartes de recettes.

    Args:
        recipes_df: DataFrame contenant les recettes
        show_similarity: Afficher ou non les scores de similarité
    """
    if len(recipes_df) == 0:
        st.info("😕 Aucune recette ne correspond à vos critères. Essayez d'ajuster les filtres.")
        return

    # Affichage en colonnes (3 par ligne)
    n_cols = 3
    for i in range(0, len(recipes_df), n_cols):
        cols = st.columns(n_cols)
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(recipes_df):
                with col:
                    recipe = recipes_df.iloc[idx]
                    similarity = recipe.get("score", None) if show_similarity else None
                    render_recipe_card(recipe, show_similarity, similarity)
