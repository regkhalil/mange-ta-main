"""
Composant d'en-tête de métriques pour Streamlit.
"""

import streamlit as st


def render_metrics_header(stats: dict):
    """
    Affiche un en-tête avec les métriques principales.

    Args:
        stats: Dictionnaire contenant les statistiques à afficher
            - total_recipes: Nombre total de recettes
            - median_prep_time: Temps de préparation médian
            - avg_calories: Calories moyennes
            - vegetarian_percentage: Pourcentage de recettes végétariennes
    """
    st.markdown(
        """
    <style>
    .metric-container {
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        margin-bottom: 2rem;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="📚 Recettes totales", value=f"{stats.get('total_recipes', 0):,}")

    with col2:
        st.metric(label="⏱️ Temps médian", value=f"{stats.get('median_prep_time', 0):.0f} min")

    with col3:
        st.metric(label="🔥 Calories moyennes", value=f"{stats.get('avg_calories', 0):.0f} kcal")

    with col4:
        st.metric(label="🌱 Végétarien", value=f"{stats.get('vegetarian_percentage', 0):.1f}%")
