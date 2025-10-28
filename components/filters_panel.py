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

    # Compteur pour forcer recréation des widgets
    if "filter_key_suffix" not in st.session_state:
        st.session_state.filter_key_suffix = 0

    # DEBUG - afficher le compteur actuel
    container.caption(f"🔧 Version des filtres : {st.session_state.filter_key_suffix}")

    # Créer 2 colonnes pour les filtres si dans la page
    if not in_sidebar:
        col1, col2 = container.columns(2)

    # Temps de préparation
    filter_col = col1 if not in_sidebar else container
    filter_col.subheader("⏱️ Temps de préparation")

    prep_range = filter_col.slider(
        "Minutes",
        min_value=0,
        max_value=300,
        value=(0, 300),
        step=5,
        key=f"prep_{st.session_state.filter_key_suffix}",
        help="Sélectionnez la plage de temps de préparation",
    )

    # Nombre d'ingrédients
    filter_col.subheader("🥕 Nombre d'ingrédients")

    ing_range = filter_col.slider(
        "Nombre d'ingrédients",
        min_value=1,
        max_value=45,
        value=(1, 45),
        step=1,
        key=f"ing_{st.session_state.filter_key_suffix}",
        help="Sélectionnez la plage du nombre d'ingrédients",
    )

    # Calories
    filter_col2 = col2 if not in_sidebar else container
    filter_col2.subheader("🔥 Calories")

    cal_range = filter_col2.slider(
        "Calories (kcal)",
        min_value=0,
        max_value=2000,
        value=(0, 2000),
        step=50,
        key=f"cal_{st.session_state.filter_key_suffix}",
        help="Sélectionnez la plage de calories",
    )

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
        default=[],
        key=f"nutri_{st.session_state.filter_key_suffix}",
        format_func=lambda x: f"{grade_info[x][0]} Grade {x} - {grade_info[x][2]}",
    )

    # Afficher l'échelle visuelle si rien n'est sélectionné
    if not nutrition_grades:
        grade_html = '<div style="display: flex; gap: 2px; margin: 8px 0;">'
        for grade, (emoji, color, label) in grade_info.items():
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
        value=False,
        key=f"veg_{st.session_state.filter_key_suffix}",
        help="Afficher uniquement les recettes végétariennes",
    )

    # Stocker les filtres
    filters = {
        "prep": list(prep_range),
        "ingredients": list(ing_range),
        "calories": list(cal_range),
        "vegetarian_only": vegetarian,
        "nutrition_grades": nutrition_grades,
    }

    if not in_sidebar:
        container.markdown("---")

    return filters
