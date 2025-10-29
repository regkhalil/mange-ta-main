"""
📊 Profil Nutrition - Nutrition Profiling & Statistical Analysis

Comprehensive analysis of healthy recipe patterns including:
- Section 1: Nutrition grade distribution and correlations
- Section 2: Time vs health analysis  
- Section 3: Ingredient health index
- Section 4: Complexity vs healthiness
"""

import sys
from pathlib import Path
import logging

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from services.data_loader import load_recipes

logger = logging.getLogger(__name__)

# Import analytics modules
from components.analytics.nutrition_profiling import (
    create_grade_histogram,
    create_correlation_heatmap,
    create_mean_nutrients_chart,
    create_nutrient_boxplots,
)
from components.analytics.time_analysis import (
    create_time_scatter,
    create_grade_by_time_category,
    create_time_category_distribution,
)
from components.analytics.ingredient_health import (
    create_ingredient_scatter,
    create_top_ingredients_table,
    create_sugar_salt_comparison,
    create_nutrient_impact_chart,
)
from components.analytics.complexity_analysis import (
    create_complexity_scatter,
    create_complexity_heatmap,
    create_complexity_category_chart,
    create_individual_factors_chart,
)

st.set_page_config(page_title="Profil Nutrition", page_icon="📊", layout="wide")


@st.cache_data
def load_data():
    """Load recipe data with caching."""
    return load_recipes()


def filter_dataset_for_viz(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter dataset to remove extreme outliers for better visualization.
    Applies percentile-based filtering on key numeric columns.
    """
    logger.info(f"Starting outlier filtering for {len(df)} recipes")
    df_filtered = df.copy()
    original_count = len(df_filtered)
    
    # Filter minutes (cooking time) - remove extreme values
    if 'minutes' in df_filtered.columns:
        p1, p99 = df_filtered['minutes'].quantile([0.01, 0.99])
        before = len(df_filtered)
        df_filtered = df_filtered[(df_filtered['minutes'] >= p1) & (df_filtered['minutes'] <= p99)]
        logger.debug(f"Minutes filter: removed {before - len(df_filtered)} recipes (range: {p1:.1f}-{p99:.1f})")
    
    # Filter n_steps - remove extreme values
    if 'n_steps' in df_filtered.columns:
        p1, p99 = df_filtered['n_steps'].quantile([0.01, 0.99])
        before = len(df_filtered)
        df_filtered = df_filtered[(df_filtered['n_steps'] >= p1) & (df_filtered['n_steps'] <= p99)]
        logger.debug(f"Steps filter: removed {before - len(df_filtered)} recipes (range: {p1:.0f}-{p99:.0f})")
    
    # Filter n_ingredients - remove extreme values
    if 'n_ingredients' in df_filtered.columns:
        p1, p99 = df_filtered['n_ingredients'].quantile([0.01, 0.99])
        before = len(df_filtered)
        df_filtered = df_filtered[(df_filtered['n_ingredients'] >= p1) & (df_filtered['n_ingredients'] <= p99)]
        logger.debug(f"Ingredients filter: removed {before - len(df_filtered)} recipes (range: {p1:.0f}-{p99:.0f})")
    
    logger.info(f"Filtering complete: {len(df_filtered)} recipes remaining ({original_count - len(df_filtered)} filtered, {(original_count - len(df_filtered))/original_count*100:.1f}%)")
    
    return df_filtered


def main():
    st.title("📊 Profil des Recettes Saines")
    st.markdown("**Analyse statistique approfondie des patterns nutritionnels**")
    
    # Load data
    with st.spinner("Chargement des données..."):
        df = load_data()
        logger.info(f"Loaded {len(df) if df is not None else 0} recipes from data source")
    
    if df is None or len(df) == 0:
        logger.error("Failed to load recipe data or empty dataset")
        st.error("❌ Erreur lors du chargement des données")
        st.stop()
    
    # Apply outlier filtering for better visualizations
    with st.spinner("Filtrage des valeurs extrêmes..."):
        df_viz = filter_dataset_for_viz(df)
    
    logger.info(f"Data ready - Total: {len(df)}, Filtered for viz: {len(df_viz)}")
    st.success(f"✅ {len(df):,} recettes chargées ({len(df_viz):,} après filtrage des outliers)")
    
    # Info about filtering
    with st.expander("ℹ️ À propos du filtrage des données"):
        st.markdown("""
        **Filtrage automatique des valeurs extrêmes:**
        - Les valeurs en dehors du 1er et 99ème percentile sont filtrées pour améliorer la lisibilité
        - Cela améliore aussi significativement les performances de chargement
        - Environ **{}** recettes filtrées ({:.1f}% du total)
        - Les statistiques générales utilisent toutes les données, seules les visualisations sont filtrées
        """.format(len(df) - len(df_viz), (len(df) - len(df_viz)) / len(df) * 100))
    
    # Create tabs for each section
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Profil Nutritionnel",
        "⏱️ Temps vs Santé",
        "🥗 Ingrédients",
        "🧩 Complexité"
    ])
    
    # ========================================================================
    # SECTION 1: NUTRITION PROFILING
    # ========================================================================
    with tab1:
        st.header("📈 Profil Nutritionnel des Recettes")
        st.markdown("Distribution des grades, corrélations entre nutriments, et analyses par grade.")
        
        st.markdown("---")
        
        # 1.1 Grade Distribution
        st.subheader("1. Distribution des Grades Nutritionnels")
        with st.spinner("Génération du graphique..."):
            fig_hist = create_grade_histogram(df_viz, vegetarian=None)
            st.plotly_chart(fig_hist, use_container_width=True)
        
        st.markdown("---")
        
        # 1.2 Correlation Matrix
        st.subheader("2. Matrice de Corrélation entre Nutriments")
        st.markdown("Analyse des relations entre les différents nutriments (méthode de Spearman)")
        with st.spinner("Calcul des corrélations..."):
            fig_corr = create_correlation_heatmap(df_viz)
            st.plotly_chart(fig_corr, use_container_width=True)
        
        st.markdown("---")
        
        # 1.3 Mean Nutrients by Grade
        st.subheader("3. Moyenne des Nutriments par Grade")
        with st.spinner("Calcul des moyennes..."):
            fig_mean = create_mean_nutrients_chart(df_viz)
            st.plotly_chart(fig_mean, use_container_width=True)
        
        st.markdown("---")
        
        # 1.4 Boxplots
        st.subheader("4. Distribution des Nutriments par Grade")
        st.markdown("Box plots montrant la distribution de chaque nutriment pour chaque grade.")
        with st.spinner("Génération des box plots..."):
            fig_box = create_nutrient_boxplots(df_viz, vegetarian=None)
            st.plotly_chart(fig_box, use_container_width=True)
    
    # ========================================================================
    # SECTION 2: TIME ANALYSIS
    # ========================================================================
    with tab2:
        st.header("⏱️ Temps de Préparation vs Santé")
        st.markdown("Analyse de la relation entre le temps de préparation et le score nutritionnel.")
        
        # 2.1 Scatter plot
        st.subheader("1. Corrélation Temps vs Score")
        with st.spinner("Analyse en cours..."):
            fig_time_scatter = create_time_scatter(df_viz)
            st.plotly_chart(fig_time_scatter, use_container_width=True)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        # 2.2 Average grade per time category
        with col1:
            st.subheader("2. Score par Catégorie")
            with st.spinner("Calcul..."):
                fig_time_cat = create_grade_by_time_category(df_viz)
                st.plotly_chart(fig_time_cat, use_container_width=True)
        
        # 2.3 Grade distribution per time category
        with col2:
            st.subheader("3. Distribution des Grades")
            with st.spinner("Calcul..."):
                fig_time_dist = create_time_category_distribution(df_viz)
                st.plotly_chart(fig_time_dist, use_container_width=True)
        
        # Insights
        st.markdown("---")
        st.info("""
        💡 **Insights**: 
        - Les recettes rapides (≤15 min) ont-elles de meilleurs scores ?
        - Y a-t-il une corrélation significative entre temps et santé ?
        - Quelle catégorie de temps a la plus forte proportion de grades A ?
        """)
    
    # ========================================================================
    # SECTION 3: INGREDIENT HEALTH
    # ========================================================================
    with tab3:
        st.header("🥗 Index Santé des Ingrédients")
        st.markdown("Analyse des ingrédients associés aux recettes saines/malsaines.")
        
        # 3.1 Ingredient scatter
        st.subheader("1. Fréquence vs Score Moyen des Ingrédients")
        col1, col2 = st.columns([3, 1])
        with col2:
            top_n = st.slider("Nombre d'ingrédients", 20, 100, 50, step=10)
        
        with st.spinner("Calcul de l'index santé..."):
            fig_ing_scatter = create_ingredient_scatter(df_viz, top_n=top_n)
            st.plotly_chart(fig_ing_scatter, use_container_width=True)
        
        st.markdown("---")
        
        # 3.2 Top ingredients tables
        st.subheader("2. Top Ingrédients")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🟢 Top 20 Ingrédients les Plus Sains**")
            with st.spinner("Calcul..."):
                top_healthy = create_top_ingredients_table(df_viz, top_n=20, sort_by='healthiest')
                st.dataframe(top_healthy, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("**🔴 Top 20 Ingrédients les Moins Sains**")
            with st.spinner("Calcul..."):
                top_unhealthy = create_top_ingredients_table(df_viz, top_n=20, sort_by='unhealthiest')
                st.dataframe(top_unhealthy, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # 3.3 Nutrient Impact Analysis
        st.subheader("3. Impact des Nutriments sur la Santé")
        st.markdown("Corrélation entre l'excès de nutriments (vs quantités recommandées) et le score nutritionnel")
        
        with st.spinner("Analyse de l'impact des nutriments..."):
            fig_nutrient_impact = create_nutrient_impact_chart(df_viz)
            st.plotly_chart(fig_nutrient_impact, use_container_width=True)
        
        st.markdown("---")
        
        # 3.4 Sugar vs Salt comparison
        st.subheader("4. Comparaison: Sucres vs Sodium")
        st.markdown("Quel nutriment a le plus d'impact négatif sur le score ?")
        
        with st.spinner("Analyse comparative..."):
            fig_sugar_salt_scatter, fig_sugar_salt_box, fig_sugar_salt_bar = create_sugar_salt_comparison(df_viz)
        
        st.plotly_chart(fig_sugar_salt_scatter, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_sugar_salt_box, use_container_width=True)
        with col2:
            st.plotly_chart(fig_sugar_salt_bar, use_container_width=True)
    
    # ========================================================================
    # SECTION 4: COMPLEXITY ANALYSIS
    # ========================================================================
    with tab4:
        st.header("🧩 Complexité vs Santé")
        st.markdown("Les recettes simples sont-elles plus saines ? Analyse de l'indice de complexité.")
        
        # 4.1 Complexity scatter
        st.subheader("1. Indice de Complexité vs Score")
        st.markdown("Indice basé sur: nombre d'étapes (40%), nombre d'ingrédients (40%), temps (20%)")
        with st.spinner("Calcul..."):
            fig_complex_scatter = create_complexity_scatter(df_viz)
            st.plotly_chart(fig_complex_scatter, use_container_width=True)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        # 4.2 Complexity category chart
        with col1:
            st.subheader("2. Score par Complexité")
            with st.spinner("Calcul..."):
                fig_complex_cat = create_complexity_category_chart(df_viz)
                st.plotly_chart(fig_complex_cat, use_container_width=True)
        
        # 4.3 Individual factors
        with col2:
            st.subheader("3. Facteurs Individuels")
            with st.spinner("Calcul..."):
                fig_factors = create_individual_factors_chart(df_viz)
                st.plotly_chart(fig_factors, use_container_width=True)
        
        st.markdown("---")
        
        # 4.4 Complexity heatmap
        st.subheader("4. Score Moyen par Nombre d'Étapes et d'Ingrédients")
        with st.spinner("Génération de la heatmap..."):
            fig_heatmap = create_complexity_heatmap(df_viz)
            st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.caption("💡 Données: Food.com (231K recettes) | Scoring: Algorithme basé sur WHO/USDA/AHA/EFSA")


if __name__ == "__main__":
    main()
