"""
Composants UI améliorés pour l'affichage des recettes.
"""

import pandas as pd
import streamlit as st

from services.search_engine import format_description, format_recipe_title


def render_recipe_card_enhanced(recipe: pd.Series, show_similar_button: bool = True):
    """
    Affiche une carte de recette améliorée avec tous les détails.

    Args:
        recipe: Série pandas de la recette
        show_similar_button: Afficher le bouton "Voir similaires"
    """
    # Titre de la recette
    title = format_recipe_title(recipe)
    description = format_description(recipe, max_length=180)

    # Grade nutritionnel et couleur
    grade_colors = {
        "A": "#038141",  # Vert foncé
        "B": "#85BB2F",  # Vert clair
        "C": "#FECB02",  # Jaune
        "D": "#EE8100",  # Orange
        "E": "#E63E11",  # Rouge
    }

    grade = recipe.get("nutrition_grade", None)
    nutrition_score = recipe.get("nutrition_score", None)

    # Créer la carte
    with st.container():
        # Header avec titre cliquable
        col_title, col_health = st.columns([3, 1])

        with col_title:
            if st.button(f"📖 {title}", key=f"title_{recipe['id']}", use_container_width=True):
                st.session_state.selected_recipe_id = recipe["id"]
                st.session_state.show_recipe_detail = True
                st.rerun()

        with col_health:
            # Health score badge
            if pd.notna(nutrition_score) and pd.notna(grade):
                color = grade_colors.get(grade, "#666666")
                st.markdown(
                    f"""
                <div style="
                    padding: 0.5rem;
                    border-radius: 8px;
                    background-color: {color};
                    color: white;
                    font-weight: bold;
                    text-align: center;
                    font-size: 0.9rem;
                ">
                    💚 {grade} ({nutrition_score:.0f})
                </div>
                """,
                    unsafe_allow_html=True,
                )

        # Description
        st.markdown(
            f"<p style='font-size: 0.9rem; color: #666; margin-top: 0.5rem;'>{description}</p>", unsafe_allow_html=True
        )

        # Badges d'info (temps, ingrédients, calories)
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(
                f"""
            <div style='text-align: center; padding: 0.5rem; background: #f0f2f6; border-radius: 6px;'>
                <div style='font-size: 1.2rem;'>⏱️</div>
                <div style='font-size: 0.85rem; font-weight: bold;'>{int(recipe["minutes"])} min</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                f"""
            <div style='text-align: center; padding: 0.5rem; background: #f0f2f6; border-radius: 6px;'>
                <div style='font-size: 1.2rem;'>🥕</div>
                <div style='font-size: 0.85rem; font-weight: bold;'>{int(recipe.get("n_ingredients", 0))}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col3:
            st.markdown(
                f"""
            <div style='text-align: center; padding: 0.5rem; background: #f0f2f6; border-radius: 6px;'>
                <div style='font-size: 1.2rem;'>🔥</div>
                <div style='font-size: 0.85rem; font-weight: bold;'>{int(recipe["calories"])} kcal</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col4:
            # Badge végétarien
            if recipe.get("is_vegetarian", False):
                st.markdown(
                    """
                <div style='text-align: center; padding: 0.5rem; background: #85BB2F; border-radius: 6px; color: white;'>
                    <div style='font-size: 1.2rem;'>🌱</div>
                    <div style='font-size: 0.75rem; font-weight: bold;'>Végé</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

        # Bouton "Voir similaires"
        if show_similar_button:
            if st.button("✨ Voir similaires", key=f"similar_{recipe['id']}", use_container_width=True):
                st.session_state.selected_recipe_id = recipe["id"]
                st.session_state.show_similar = True
                st.rerun()

        st.markdown("---")


def render_recipe_detail(recipe: pd.Series, recommender=None):
    """
    Affiche le détail complet d'une recette dans un expander ou modal.

    Args:
        recipe: Série pandas de la recette
        recommender: Instance du recommender pour les recettes similaires
    """
    title = format_recipe_title(recipe)

    # Modal header
    col_close, col_title = st.columns([1, 5])

    with col_close:
        if st.button("✖️ Fermer", key="close_detail"):
            st.session_state.show_recipe_detail = False
            st.rerun()

    with col_title:
        st.markdown(f"## 🍽️ {title}")

    st.markdown("---")

    # Health score en grand
    if pd.notna(recipe.get("nutrition_score")):
        col_score, col_badges = st.columns([1, 2])

        with col_score:
            st.markdown("### 💚 Health Score")
            score = recipe["nutrition_score"]
            st.progress(score / 100)
            st.markdown(f"**{score:.0f}/100** - Grade {recipe.get('nutrition_grade', 'N/A')}")

        with col_badges:
            st.markdown("### 📊 Informations")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("⏱️ Temps", f"{int(recipe['totalTime'])} min")
            with col2:
                st.metric("🥕 Ingrédients", int(recipe.get("n_ingredients", 0)))
            with col3:
                st.metric("🔥 Calories", f"{int(recipe['calories'])} kcal")

    st.markdown("---")

    # Ingrédients
    st.markdown("### 🥬 Ingrédients")
    if "ingredient_tokens" in recipe:
        ingredients = recipe["ingredient_tokens"]
        # Afficher en 2 colonnes
        col1, col2 = st.columns(2)
        mid = len(ingredients) // 2

        with col1:
            for ing in ingredients[:mid]:
                st.markdown(f"• {ing}")

        with col2:
            for ing in ingredients[mid:]:
                st.markdown(f"• {ing}")

    st.markdown("---")

    # Étapes de préparation
    st.markdown("### 📝 Préparation")
    if "steps_tokens" in recipe:
        steps = recipe["steps_tokens"]
        description = " ".join([str(t) for t in steps])
        st.markdown(description)

    st.markdown("---")

    # Recettes similaires
    if recommender:
        st.markdown("### ✨ Recettes similaires")

        with st.spinner("Recherche de recettes similaires..."):
            recommendations = recommender.get_similar_recipes(recipe["id"], k=6)

        if recommendations:
            cols = st.columns(3)
            for idx, (rec, score) in enumerate(recommendations):
                with cols[idx % 3]:
                    rec_title = format_recipe_title(rec)
                    if st.button(f"📖 {rec_title}", key=f"sim_{rec['id']}", use_container_width=True):
                        st.session_state.selected_recipe_id = rec["id"]
                        st.rerun()

                    st.caption(f"Similarité: {score:.1%}")
                    st.markdown(f"⏱️ {int(rec['totalTime'])}min | 🥕 {int(rec.get('n_ingredients', 0))}")


def render_search_bar():
    """
    Affiche la barre de recherche principale.

    Returns:
        Tuple (query, search_clicked)
    """
    st.markdown("## 🔍 Rechercher une recette")

    col_search, col_button = st.columns([4, 1])

    with col_search:
        query = st.text_input(
            "Rechercher", placeholder="Ex: poulet, pâtes, salade...", key="search_query", label_visibility="collapsed"
        )

    with col_button:
        search_clicked = st.button("🔍 Rechercher", use_container_width=True, type="primary")

    return query, search_clicked


def render_filters_sidebar():
    """
    Affiche les filtres dans la sidebar.

    Returns:
        dict: Dictionnaire des filtres sélectionnés
    """
    st.sidebar.markdown("## 🎛️ Filtres")

    # Temps de préparation
    st.sidebar.markdown("### ⏱️ Temps de préparation")
    prep_time_max = st.sidebar.slider(
        "Maximum (minutes)", min_value=5, max_value=180, value=180, step=5, key="prep_time_filter"
    )

    # Nombre d'ingrédients
    st.sidebar.markdown("### 🥕 Nombre d'ingrédients")
    ingredients_max = st.sidebar.slider(
        "Maximum", min_value=1, max_value=30, value=30, step=1, key="ingredients_filter"
    )

    # Calories
    st.sidebar.markdown("### 🔥 Calories")
    calories_max = st.sidebar.slider(
        "Maximum (kcal)", min_value=0, max_value=1000, value=1000, step=50, key="calories_filter"
    )

    # Végétarien
    st.sidebar.markdown("### 🌱 Options")
    vegetarian_only = st.sidebar.checkbox("Végétarien uniquement", key="vegetarian_filter")

    # Grade nutritionnel
    st.sidebar.markdown("### 📊 Score nutritionnel")
    nutrition_grades = st.sidebar.multiselect(
        "Grades acceptés",
        options=["A", "B", "C", "D", "E"],
        default=[],
        key="nutrition_grades_filter",
        format_func=lambda x: f"{'🟢' if x == 'A' else '🟡' if x == 'B' else '🟠' if x == 'C' else '🟤' if x == 'D' else '🔴'} Grade {x}",
    )

    # Tri
    st.sidebar.markdown("### 🔀 Tri")
    sort_by = st.sidebar.selectbox(
        "Trier par",
        options=["relevance", "health_score", "prep_time"],
        format_func=lambda x: {
            "relevance": "🎯 Pertinence",
            "health_score": "💚 Health Score",
            "prep_time": "⏱️ Temps de préparation",
        }[x],
        key="sort_filter",
    )

    # Bouton appliquer
    apply_clicked = st.sidebar.button("✅ Appliquer les filtres", type="primary", use_container_width=True)

    # Bouton réinitialiser
    if st.sidebar.button("🔄 Réinitialiser", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    return {
        "prep_time_max": prep_time_max,
        "ingredients_max": ingredients_max,
        "calories_max": calories_max,
        "vegetarian_only": vegetarian_only,
        "nutrition_grades": nutrition_grades,
        "sort_by": sort_by,
        "apply_clicked": apply_clicked,
    }


def render_pagination(current_page: int, total_pages: int, total_results: int):
    """
    Affiche les contrôles de pagination.

    Args:
        current_page: Page actuelle
        total_pages: Nombre total de pages
        total_results: Nombre total de résultats

    Returns:
        int: Nouvelle page sélectionnée
    """
    st.markdown("---")

    col1, col2, col3 = st.columns([2, 2, 2])

    with col1:
        st.markdown(f"**{total_results} recettes trouvées** (Page {current_page}/{total_pages})")

    with col2:
        # Boutons de navigation
        nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)

        new_page = current_page

        with nav_col1:
            if st.button("⏮️", key="page_first", disabled=(current_page == 1)):
                new_page = 1

        with nav_col2:
            if st.button("◀️", key="page_prev", disabled=(current_page == 1)):
                new_page = current_page - 1

        with nav_col3:
            if st.button("▶️", key="page_next", disabled=(current_page == total_pages)):
                new_page = current_page + 1

        with nav_col4:
            if st.button("⏭️", key="page_last", disabled=(current_page == total_pages)):
                new_page = total_pages

    with col3:
        # Sélecteur de page
        selected_page = st.number_input(
            "Aller à la page", min_value=1, max_value=total_pages, value=current_page, key="page_selector"
        )
        if selected_page != current_page:
            new_page = selected_page

    return new_page
