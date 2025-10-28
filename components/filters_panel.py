"""
Composant de panneau de filtres pour Streamlit.
"""

import streamlit as st


def render_filters_panel(in_sidebar=True):
    """
    Affiche le panneau de filtres dans la sidebar ou dans la page principale.

    Args:
        in_sidebar: Si True, affiche dans la sidebar. Si False, affiche dans la page.

    Returns:
        Dictionnaire avec les valeurs des filtres sélectionnés
    """
    # Choisir le conteneur (sidebar ou page)
    container = st.sidebar if in_sidebar else st

    if in_sidebar:
        container.header("Filtres")
    else:
        container.markdown("### 🎯 Filtres")
        container.markdown("---")

    # Initialiser les valeurs dans session_state si nécessaire
    if "filters" not in st.session_state:
        st.session_state.filters = {
            "prep": [0, 300],
            "ingredients": [1, 45],
            "calories": [0, 2000],
            "vegetarian_only": False,
            "nutrition_grades": [],
        }
    
    # Initialiser les valeurs par défaut des widgets si elles n'existent pas
    if "prep_slider" not in st.session_state:
        st.session_state.prep_slider = (0, 300)
    if "ingredients_slider" not in st.session_state:
        st.session_state.ingredients_slider = (1, 45)
    if "calories_slider" not in st.session_state:
        st.session_state.calories_slider = (0, 2000)
    if "vegetarian_checkbox" not in st.session_state:
        st.session_state.vegetarian_checkbox = False
    if "nutrition_grades_select" not in st.session_state:
        st.session_state.nutrition_grades_select = []

    # Créer 2 colonnes pour les filtres si dans la page
    if not in_sidebar:
        col1, col2 = container.columns(2)

    # Temps de préparation
    filter_col = col1 if not in_sidebar else container
    filter_col.subheader("⏱️ Temps de préparation")

    # Slider avec deux bornes (min et max)
    prep_range = filter_col.slider(
        "Minutes",
        min_value=0,
        max_value=300,
        value=st.session_state.prep_slider,
        step=5,
        key="prep_slider",
        help="Sélectionnez la plage de temps de préparation",
    )
    st.session_state.filters["prep"] = list(prep_range)

    # Nombre d'ingrédients
    filter_col.subheader("🥕 Nombre d'ingrédients")

    # Slider avec deux bornes (min et max)
    ing_range = filter_col.slider(
        "Nombre d'ingrédients",
        min_value=1,
        max_value=45,
        value=st.session_state.ingredients_slider,
        step=1,
        key="ingredients_slider",
        help="Sélectionnez la plage du nombre d'ingrédients",
    )
    st.session_state.filters["ingredients"] = list(ing_range)

    # Calories
    filter_col2 = col2 if not in_sidebar else container
    filter_col2.subheader("🔥 Calories")

    # Slider avec deux bornes (min et max)
    cal_range = filter_col2.slider(
        "Calories (kcal)",
        min_value=0,
        max_value=2000,
        value=st.session_state.calories_slider,
        step=50,
        key="calories_slider",
        help="Sélectionnez la plage de calories",
    )
    st.session_state.filters["calories"] = list(cal_range)

    # Score nutritionnel (Nutri-Score)
    filter_col2.subheader("🍎 Nutri-Score")
    filter_col2.caption("Filtre par grade nutritionnel")

    # Afficher l'échelle visuelle
    grade_info = {
        "A": ("🟢", "#238B45", "Excellent"),
        "B": ("🟡", "#85BB2F", "Bon"),
        "C": ("🟠", "#FECC00", "Acceptable"),
        "D": ("🟠", "#FF9500", "Mauvais"),
        "E": ("🔴", "#E63946", "Très mauvais"),
    }

    # Multiselect pour les grades
    nutrition_grades = filter_col2.multiselect(
        "Grades acceptés",
        options=["A", "B", "C", "D", "E"],
        default=st.session_state.nutrition_grades_select,
        format_func=lambda x: f"{grade_info[x][0]} Grade {x} - {grade_info[x][2]}",
        key="nutrition_grades_select",
    )
    st.session_state.filters["nutrition_grades"] = nutrition_grades

    # Afficher l'échelle visuelle si rien n'est sélectionné
    if not nutrition_grades:
        grade_html = '<div style="display: flex; gap: 2px; margin: 8px 0;">'
        for grade, (emoji, color, label) in grade_info.items():
            # noqa: E501
            grade_html += (
                f'<div style="background-color: {color}; color: white; font-weight: bold; '
                f"padding: 6px 10px; border-radius: 4px; font-size: 12px; text-align: center; "
                f'flex: 1; cursor: default;" title="{label}">{grade}</div>'
            )
        grade_html += "</div>"
        filter_col2.markdown(grade_html, unsafe_allow_html=True)

    # Végétarien
    veg_col = container if in_sidebar else filter_col2
    veg_col.subheader("🌱 Options")
    vegetarian = veg_col.checkbox(
        "Végétarien uniquement",
        value=st.session_state.vegetarian_checkbox,
        key="vegetarian_checkbox",
        help="Afficher uniquement les recettes végétariennes",
    )
    st.session_state.filters["vegetarian_only"] = vegetarian

    # Bouton de réinitialisation
    if veg_col.button("🔄 Réinitialiser les filtres", type="primary", use_container_width=True):
        # Réinitialiser les valeurs par défaut des widgets
        st.session_state.prep_slider = (0, 300)
        st.session_state.ingredients_slider = (1, 45)
        st.session_state.calories_slider = (0, 2000)
        st.session_state.vegetarian_checkbox = False
        st.session_state.nutrition_grades_select = []
        
        # Réinitialiser les filtres
        st.session_state.filters = {
            "prep": [0, 300],
            "ingredients": [1, 45],
            "calories": [0, 2000],
            "vegetarian_only": False,
            "nutrition_grades": [],
        }
        st.rerun()

    if not in_sidebar:
        container.markdown("---")

    return st.session_state.filters
