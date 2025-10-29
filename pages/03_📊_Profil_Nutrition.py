"""
📊 Profil Nutrition - Nutrition Profiling & Statistical Analysis

Comprehensive analysis of healthy recipe patterns including:
- Section 1: Nutrition grade distribution and correlations
- Section 2: Time vs health analysis
- Section 3: Ingredient health index
- Section 4: Complexity vs healthiness
"""

import logging
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Import analytics modules (must be after streamlit for proper module loading)
sys.path.insert(0, str(Path(__file__).parent.parent))

from components.analytics.complexity_analysis import (
    create_complexity_heatmap,
    create_complexity_scatter,
    create_individual_factors_chart,
)
from components.analytics.ingredient_health import (
    create_ingredient_scatter,
    create_nutrient_impact_chart,
    create_nutrition_popularity_scatter,
    create_nutrition_popularity_stats,
    create_sugar_salt_comparison,
    create_top_ingredients_table,
)
from components.analytics.nutrition_profiling import (
    create_correlation_heatmap,
    create_grade_histogram,
    create_mean_nutrients_chart,
    create_nutrient_boxplots,
)
from components.analytics.time_analysis import (
    create_grade_by_time_category,
    create_time_category_distribution,
    create_time_scatter,
)
from services.data_loader import load_recipes

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Profil Nutrition", page_icon="📊", layout="wide")


@st.cache_data
def load_data():
    """Load recipe data with caching."""
    return load_recipes()


def filter_dataset_for_viz(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter dataset to remove extreme outliers for better visualization.
    More aggressive filtering: 0.5%-99.5% percentile.
    """
    logger.info(f"Starting outlier filtering for {len(df)} recipes")
    df_filtered = df.copy()
    original_count = len(df_filtered)

    # Filter minutes (cooking time) - remove extreme values
    if "minutes" in df_filtered.columns:
        p05, p995 = df_filtered["minutes"].quantile([0.005, 0.995])
        before = len(df_filtered)
        df_filtered = df_filtered[(df_filtered["minutes"] >= p05) & (df_filtered["minutes"] <= p995)]
        logger.debug(f"Minutes filter: removed {before - len(df_filtered)} recipes (range: {p05:.1f}-{p995:.1f})")

    # Filter n_steps - remove extreme values
    if "n_steps" in df_filtered.columns:
        p05, p995 = df_filtered["n_steps"].quantile([0.005, 0.995])
        before = len(df_filtered)
        df_filtered = df_filtered[(df_filtered["n_steps"] >= p05) & (df_filtered["n_steps"] <= p995)]
        logger.debug(f"Steps filter: removed {before - len(df_filtered)} recipes (range: {p05:.0f}-{p995:.0f})")

    # Filter n_ingredients - remove extreme values
    if "n_ingredients" in df_filtered.columns:
        p05, p995 = df_filtered["n_ingredients"].quantile([0.005, 0.995])
        before = len(df_filtered)
        df_filtered = df_filtered[(df_filtered["n_ingredients"] >= p05) & (df_filtered["n_ingredients"] <= p995)]
        logger.debug(f"Ingredients filter: removed {before - len(df_filtered)} recipes (range: {p05:.0f}-{p995:.0f})")

    # Filter calories - remove extreme values
    if "calories" in df_filtered.columns:
        p05, p995 = df_filtered["calories"].quantile([0.005, 0.995])
        before = len(df_filtered)
        df_filtered = df_filtered[(df_filtered["calories"] >= p05) & (df_filtered["calories"] <= p995)]
        logger.debug(f"Calories filter: removed {before - len(df_filtered)} recipes (range: {p05:.0f}-{p995:.0f})")

    logger.info(
        f"Filtering complete: {len(df_filtered)} recipes remaining ({original_count - len(df_filtered)} filtered, {(original_count - len(df_filtered)) / original_count * 100:.1f}%)"
    )

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
        st.markdown(
            """
        **Filtrage automatique des valeurs extrêmes:**
        - Les valeurs en dehors du 1er et 99ème percentile sont filtrées pour améliorer la lisibilité
        - Cela améliore aussi significativement les performances de chargement
        - Environ **{}** recettes filtrées ({:.1f}% du total)
        - Les statistiques générales utilisent toutes les données, seules les visualisations sont filtrées
        """.format(len(df) - len(df_viz), (len(df) - len(df_viz)) / len(df) * 100)
        )

    # Create tabs for each section
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "📈 Profil Nutritionnel",
            "🥗 Ingrédients",
            "🌱 Végétarien/Végan",
            "⏱️ Temps vs Santé",
            "🧩 Complexité",
            "⭐ Nutrition vs Popularité",
        ]
    )

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
    # SECTION 2: INGREDIENT HEALTH
    # ========================================================================
    with tab2:
        st.header("🥗 Index Santé des Ingrédients")
        st.markdown("Analyse des ingrédients associés aux recettes saines/malsaines.")

        # 2.1 Ingredient scatter
        st.subheader("1. Fréquence vs Score Moyen des Ingrédients")
        st.markdown("**Top 30 ingrédients les plus fréquents** dans le dataset (apparaissant au moins 100 fois)")

        with st.spinner("Calcul de l'index santé..."):
            fig_ing_scatter = create_ingredient_scatter(df_viz, top_n=30)
            st.plotly_chart(fig_ing_scatter, use_container_width=True)

        st.markdown("---")

        # 2.2 Top ingredients tables
        st.subheader("2. Top 20 Ingrédients")

        st.markdown("**🟢 Top 20 Ingrédients les Plus Sains**")
        with st.spinner("Calcul..."):
            top_healthy = create_top_ingredients_table(df_viz, top_n=20, sort_by="healthiest")
            # Add index column
            top_healthy.insert(0, "#", range(1, len(top_healthy) + 1))

            # Display with custom column configuration
            st.dataframe(
                top_healthy,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "#": st.column_config.NumberColumn("#", width="small", help="Rang"),
                    "Ingrédient": st.column_config.TextColumn("Ingrédient", width="large"),
                    "Score Moyen": st.column_config.NumberColumn("Score Moyen", width="small", format="%.1f"),
                    "Variabilité": st.column_config.NumberColumn("Variabilité", width="small", format="%.1f"),
                    "Fréquence": st.column_config.NumberColumn("Fréquence", width="small", format="%d"),
                },
            )

        st.markdown("---")

        st.markdown("**🔴 Top 20 Ingrédients les Moins Sains**")
        with st.spinner("Calcul..."):
            top_unhealthy = create_top_ingredients_table(df_viz, top_n=20, sort_by="unhealthiest")
            # Add index column
            top_unhealthy.insert(0, "#", range(1, len(top_unhealthy) + 1))

            # Display with custom column configuration
            st.dataframe(
                top_unhealthy,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "#": st.column_config.NumberColumn("#", width="small", help="Rang"),
                    "Ingrédient": st.column_config.TextColumn("Ingrédient", width="large"),
                    "Score Moyen": st.column_config.NumberColumn("Score Moyen", width="small", format="%.1f"),
                    "Variabilité": st.column_config.NumberColumn("Variabilité", width="small", format="%.1f"),
                    "Fréquence": st.column_config.NumberColumn("Fréquence", width="small", format="%d"),
                },
            )

        st.markdown("---")

        # 2.2b Complete ingredient list (expandable)
        with st.expander("📋 Liste Complète des Ingrédients"):
            st.markdown("""
            Liste exhaustive de **tous les ingrédients** apparaissant au moins 100 fois dans le dataset (~1,840 ingrédients).  
            Triés par score nutritionnel (du meilleur au pire).
            """)

            with st.spinner("Chargement de la liste complète..."):
                # Load full ingredient list
                from components.analytics.ingredient_health import calculate_ingredient_health_index

                ingredient_stats = calculate_ingredient_health_index(df_viz, min_frequency=100)
                full_list = ingredient_stats[["ingredient", "avg_score", "std_score", "frequency"]].copy()
                full_list.columns = ["Ingrédient", "Score Moyen", "Variabilité", "Fréquence"]
                full_list = full_list.sort_values("Score Moyen", ascending=False).reset_index(drop=True)
                full_list.insert(0, "#", range(1, len(full_list) + 1))

                # Add search filter
                search = st.text_input("🔍 Rechercher un ingrédient", "", key="ingredient_search")

                if search:
                    filtered = full_list[full_list["Ingrédient"].str.contains(search, case=False, na=False)]
                    st.info(f"Trouvé {len(filtered)} ingrédient(s) correspondant à '{search}'")
                    display_list = filtered
                else:
                    display_list = full_list

                # Display with custom column configuration
                st.dataframe(
                    display_list,
                    use_container_width=True,
                    hide_index=True,
                    height=600,
                    column_config={
                        "#": st.column_config.NumberColumn("#", width="small", help="Rang par score"),
                        "Ingrédient": st.column_config.TextColumn("Ingrédient", width="large"),
                        "Score Moyen": st.column_config.NumberColumn("Score Moyen", width="small", format="%.1f"),
                        "Variabilité": st.column_config.NumberColumn("Variabilité", width="small", format="%.1f"),
                        "Fréquence": st.column_config.NumberColumn("Fréquence", width="small", format="%d"),
                    },
                )

        st.markdown("---")

        # 2.3 Nutrient Impact Analysis
        st.subheader("3. Impact des Nutriments sur la Santé")
        st.markdown("""
        **Valeurs Nutritionnelles de Référence (par portion)**  
        Selon les recommandations WHO/USDA/AHA/EFSA:
        
        | Nutriment | Limite Recommandée | Source |
        |-----------|-------------------|--------|
        | **Calories** | 2000 kcal/jour | USDA Dietary Guidelines |
        | **Lipides Totaux** | <65g/jour (<30% calories) | WHO |
        | **Lipides Saturés** | <20g/jour (<10% calories) | AHA/WHO |
        | **Sucres** | <50g/jour (<10% calories) | WHO |
        | **Sodium** | <2300mg/jour | USDA/AHA |
        | **Protéines** | 50g/jour (10-35% calories) | USDA |
        | **Glucides** | 275g/jour (45-65% calories) | USDA |
        
        *Note: Les pourcentages affichés représentent la Valeur Quotidienne (%VQ) par portion*
        """)

        st.markdown("**Corrélation entre l'excès de nutriments et le score nutritionnel**")

        with st.spinner("Analyse de l'impact des nutriments..."):
            fig_nutrient_impact = create_nutrient_impact_chart(df_viz)
            st.plotly_chart(fig_nutrient_impact, use_container_width=True)

        st.markdown("---")

        # 2.4 Sugar vs Salt comparison
        st.subheader("4. Comparaison: Sucres vs Sodium")
        st.markdown("Quel nutriment a le plus d'impact négatif sur le score ?")

        with st.spinner("Analyse comparative..."):
            fig_sugar_salt_scatter, fig_sugar_salt_box, fig_sugar_salt_bar = create_sugar_salt_comparison(df_viz)

            # Get the comparison data to show median reference points
            from components.analytics.ingredient_health import compare_sugar_vs_salt

            comparison_data = compare_sugar_vs_salt(df_viz)

            # Display reference points
            st.info(f"""
            📌 **Points de Référence** (valeurs médianes du dataset):
            - **Sucres**: {comparison_data["sugar_median"]:.1f}% VQ - Recettes au-dessus de cette valeur sont considérées "Élevées"
            - **Sodium**: {comparison_data["sodium_median"]:.1f}% VQ - Recettes au-dessus de cette valeur sont considérées "Élevé"
            
            Les catégories "Faible" et "Élevé" sont relatives à la médiane des recettes du dataset.
            """)

        # Show scatter plot (main visualization)
        st.plotly_chart(fig_sugar_salt_scatter, use_container_width=True)

        st.markdown("---")

        # Show horizontal box plot comparison
        # Make the box plot horizontal
        fig_sugar_salt_box.update_layout(xaxis_title="Score Nutritionnel", yaxis_title="Catégorie", height=400)
        # Swap x and y to make it horizontal
        fig_sugar_salt_box_horizontal = go.Figure()
        for trace in fig_sugar_salt_box.data:
            fig_sugar_salt_box_horizontal.add_trace(
                go.Box(
                    x=trace.y,  # Swap x and y
                    y=[trace.name] * len(trace.y) if hasattr(trace, "y") and trace.y is not None else None,
                    name=trace.name,
                    marker_color=trace.marker.color,
                    boxmean="sd",
                    orientation="h",  # Horizontal orientation
                )
            )

        fig_sugar_salt_box_horizontal.update_layout(
            title="Distribution des Scores: Sucres vs Sodium (Élevé vs Faible)",
            xaxis_title="Score Nutritionnel",
            yaxis_title="",
            template="plotly_white",
            height=400,
            showlegend=False,
        )

        st.plotly_chart(fig_sugar_salt_box_horizontal, use_container_width=True)

    # ========================================================================
    # SECTION 3: VEGETARIAN ANALYSIS
    # ========================================================================
    with tab3:
        st.header("🌱 Analyse Végétarien/Végan")
        st.markdown("Comparaison nutritionnelle des recettes végétariennes et non-végétariennes.")

        # Check if vegetarian column exists
        if "is_vegetarian" not in df_viz.columns:
            st.warning("⚠️ La colonne 'is_vegetarian' n'est pas disponible dans les données.")
        else:
            # 3.1 Distribution overview
            st.subheader("1. Distribution Végétarien vs Non-Végétarien")

            veg_count = df_viz["is_vegetarian"].sum()
            non_veg_count = len(df_viz) - veg_count
            veg_pct = (veg_count / len(df_viz)) * 100
            non_veg_pct = (non_veg_count / len(df_viz)) * 100

            # Calculate average scores
            veg_avg_score = df_viz[df_viz["is_vegetarian"]]["nutrition_score"].mean()
            non_veg_avg_score = df_viz[~df_viz["is_vegetarian"]]["nutrition_score"].mean()
            diff = veg_avg_score - non_veg_avg_score

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "🥬 Recettes Végétariennes",
                    f"{veg_count:,} ({veg_pct:.0f}%)",
                    f"Moy: {veg_avg_score:.1f}",
                )
            with col2:
                st.metric(
                    "🍖 Recettes Non-Végétariennes",
                    f"{non_veg_count:,} ({non_veg_pct:.0f}%)",
                    f"Moy: {non_veg_avg_score:.1f}",
                )
            with col3:
                st.metric("📊 Différence de Score", f"{diff:+.1f}")

            st.markdown("---")

            # 3.2 Score comparison box plot
            st.subheader("2. Comparaison des Scores Nutritionnels")

            veg_data = df_viz[df_viz["is_vegetarian"]]
            non_veg_data = df_viz[~df_viz["is_vegetarian"]]

            fig_veg_box = go.Figure()
            fig_veg_box.add_trace(
                go.Box(y=veg_data["nutrition_score"], name="Végétarien", marker_color="#85BB2F", boxmean="sd")
            )
            fig_veg_box.add_trace(
                go.Box(y=non_veg_data["nutrition_score"], name="Non-Végétarien", marker_color="#E63946", boxmean="sd")
            )

            fig_veg_box.update_layout(
                title="Distribution des Scores: Végétarien vs Non-Végétarien",
                yaxis_title="Score Nutritionnel",
                template="plotly_white",
                height=400,
                showlegend=True,
            )

            st.plotly_chart(fig_veg_box, use_container_width=True)

            st.markdown("---")

            # 3.3 Grade distribution comparison
            st.subheader("3. Distribution des Grades")

            veg_grades = (
                veg_data["nutrition_grade"]
                .value_counts(normalize=True)
                .reindex(["A", "B", "C", "D", "E"], fill_value=0)
                * 100
            )
            non_veg_grades = (
                non_veg_data["nutrition_grade"]
                .value_counts(normalize=True)
                .reindex(["A", "B", "C", "D", "E"], fill_value=0)
                * 100
            )

            fig_grades = go.Figure()
            fig_grades.add_trace(
                go.Bar(x=["A", "B", "C", "D", "E"], y=veg_grades.values, name="Végétarien", marker_color="#85BB2F")
            )
            fig_grades.add_trace(
                go.Bar(
                    x=["A", "B", "C", "D", "E"], y=non_veg_grades.values, name="Non-Végétarien", marker_color="#E63946"
                )
            )

            fig_grades.update_layout(
                title="Distribution des Grades (%)",
                xaxis_title="Grade Nutritionnel",
                yaxis_title="Pourcentage (%)",
                barmode="group",
                template="plotly_white",
                height=400,
            )

            st.plotly_chart(fig_grades, use_container_width=True)

            st.markdown("---")

            # 3.4 Nutrient comparison
            st.subheader("4. Comparaison Nutritionnelle Détaillée")

            # Get average nutrients
            veg_nutrients = [
                veg_data["calories"].mean(),
                veg_data["protein_pdv"].mean(),
                veg_data["total_fat_pdv"].mean(),
                veg_data["sugar_pdv"].mean(),
                veg_data["sodium_pdv"].mean(),
            ]

            non_veg_nutrients = [
                non_veg_data["calories"].mean(),
                non_veg_data["protein_pdv"].mean(),
                non_veg_data["total_fat_pdv"].mean(),
                non_veg_data["sugar_pdv"].mean(),
                non_veg_data["sodium_pdv"].mean(),
            ]

            nutrient_names = ["Calories", "Protéines (%VQ)", "Lipides (%VQ)", "Sucres (%VQ)", "Sodium (%VQ)"]

            fig_nutrients = go.Figure()
            fig_nutrients.add_trace(
                go.Bar(x=nutrient_names, y=veg_nutrients, name="Végétarien", marker_color="#85BB2F")
            )
            fig_nutrients.add_trace(
                go.Bar(x=nutrient_names, y=non_veg_nutrients, name="Non-Végétarien", marker_color="#E63946")
            )

            fig_nutrients.update_layout(
                title="Valeurs Nutritionnelles Moyennes: Végétarien vs Non-Végétarien",
                xaxis_title="Nutriment",
                yaxis_title="Valeur Moyenne",
                barmode="group",
                template="plotly_white",
                height=400,
            )

            st.plotly_chart(fig_nutrients, use_container_width=True)

    # ========================================================================
    # SECTION 4: TIME ANALYSIS
    # ========================================================================
    with tab4:
        st.header("⏱️ Temps de Préparation vs Santé")
        st.markdown("Analyse de la relation entre le temps de préparation et le score nutritionnel.")

        # 4.1 Scatter plot
        st.subheader("1. Corrélation Temps vs Score")
        with st.spinner("Analyse en cours..."):
            fig_time_scatter = create_time_scatter(df_viz)
            st.plotly_chart(fig_time_scatter, use_container_width=True)

        st.markdown("---")

        # 4.2 Average grade per time category
        st.subheader("2. Score par Catégorie")
        with st.spinner("Calcul..."):
            fig_time_cat = create_grade_by_time_category(df_viz)
            st.plotly_chart(fig_time_cat, use_container_width=True)

        st.markdown("---")

        # 4.3 Grade distribution per time category
        st.subheader("3. Distribution des Grades")
        with st.spinner("Calcul..."):
            fig_time_dist = create_time_category_distribution(df_viz)
            st.plotly_chart(fig_time_dist, use_container_width=True)

    # ========================================================================
    # SECTION 5: COMPLEXITY ANALYSIS
    # ========================================================================
    with tab5:
        st.header("🧩 Complexité vs Santé")
        st.markdown("Les recettes simples sont-elles plus saines ? Analyse de l'indice de complexité.")

        # 5.1 Complexity scatter (was 4.1)
        st.subheader("1. Indice de Complexité vs Score")
        st.markdown("Indice basé sur: nombre d'étapes (40%), nombre d'ingrédients (40%), temps (20%)")
        with st.spinner("Calcul..."):
            fig_complex_scatter = create_complexity_scatter(df_viz)
            st.plotly_chart(fig_complex_scatter, use_container_width=True)

        st.markdown("---")

        # 5.2 Individual factors
        st.subheader("2. Facteurs Individuels de Complexité")
        st.markdown(
            "Impact séparé du nombre d'étapes, d'ingrédients et du temps sur le score nutritionnel (basé sur la corrélation)"
        )
        with st.spinner("Calcul..."):
            fig_factors = create_individual_factors_chart(df_viz)
            st.plotly_chart(fig_factors, use_container_width=True)

        st.markdown("---")

        # 5.3 Complexity heatmap
        st.subheader("3. Score Moyen par Nombre d'Étapes et d'Ingrédients")
        with st.spinner("Génération de la heatmap..."):
            fig_heatmap = create_complexity_heatmap(df_viz)
            st.plotly_chart(fig_heatmap, use_container_width=True)

    # ========================================================================
    # SECTION 6: NUTRITION VS POPULARITY
    # ========================================================================
    with tab6:
        st.header("⭐ Nutrition vs Popularité")
        st.markdown(
            "Les recettes saines sont-elles plus populaires ? Analyse de la relation entre score nutritionnel et popularité."
        )

        # 6.1 Main scatter plot
        st.subheader("1. Score Nutritionnel vs Score de Popularité")
        st.markdown("Chaque point représente une recette, colorée par grade nutritionnel.")

        with st.spinner("Génération du graphique..."):
            fig_nutrition_popularity = create_nutrition_popularity_scatter(df_viz)
            st.plotly_chart(fig_nutrition_popularity, use_container_width=True)

        st.markdown("---")

        # 6.2 Statistics table
        st.subheader("2. Statistiques Clés")
        with st.spinner("Calcul des statistiques..."):
            stats_nutrition_popularity = create_nutrition_popularity_stats(df_viz)
            st.dataframe(
                stats_nutrition_popularity,
                use_container_width=True,
                hide_index=True,
                height=500,
                column_config={
                    "Métrique": st.column_config.TextColumn("Métrique", width="medium"),
                    "Score d'Engagement": st.column_config.NumberColumn(
                        "Score d'Engagement",
                        width="small",
                        format="%.2f",
                        help="Score basé sur le nombre d'évaluations et la note moyenne",
                    ),
                    "Note Moyenne": st.column_config.TextColumn("Note Moyenne", width="small"),
                    "Nombre de Recettes": st.column_config.TextColumn("Nombre de Recettes", width="medium"),
                },
            )

        st.markdown("---")

        # 6.3 Popularity by grade box plot
        st.subheader("3. Popularité par Grade")
        st.markdown("Distribution de la popularité pour chaque grade nutritionnel.")

        # Create box plot by grade
        with st.spinner("Génération..."):
            clean_df = df_viz[["nutrition_grade", "popularity_score", "nutrition_score"]].dropna()
            clean_df = clean_df[clean_df["popularity_score"] > 0]

            grade_colors = {"A": "#238B45", "B": "#85BB2F", "C": "#FECC00", "D": "#FF9500", "E": "#E63946"}

            fig_pop_by_grade = go.Figure()

            for grade in ["A", "B", "C", "D", "E"]:
                grade_data = clean_df[clean_df["nutrition_grade"] == grade]
                if len(grade_data) > 0:
                    fig_pop_by_grade.add_trace(
                        go.Box(
                            y=grade_data["popularity_score"],
                            name=f"Grade {grade}",
                            marker_color=grade_colors[grade],
                            boxmean="sd",
                        )
                    )

            fig_pop_by_grade.update_layout(
                title="Distribution de la Popularité par Grade",
                yaxis_title="Score de Popularité",
                xaxis_title="Grade Nutritionnel",
                template="plotly_white",
                height=400,
                showlegend=False,
            )

            st.plotly_chart(fig_pop_by_grade, use_container_width=True)

        st.markdown("---")

        # 6.3 Additional insights
        st.subheader("4. Insights")

        # Calculate correlation
        clean_df = df_viz[["nutrition_score", "popularity_score"]].dropna()
        clean_df = clean_df[clean_df["popularity_score"] > 0]

        from scipy.stats import spearmanr

        corr, p_val = spearmanr(clean_df["nutrition_score"], clean_df["popularity_score"])

        if corr > 0.1:
            interpretation = (
                "✅ **Tendance positive**: Les recettes plus saines tendent à être légèrement plus populaires."
            )
        elif corr < -0.1:
            interpretation = "⚠️ **Tendance négative**: Les recettes moins saines tendent à être plus populaires."
        else:
            interpretation = "➡️ **Pas de corrélation forte**: Le score nutritionnel a peu d'impact sur la popularité."

        st.info(f"""
        💡 **Analyse**:
        - Corrélation Spearman: **{corr:.3f}** (p-value: {p_val:.2e})
        - {interpretation}
        - La popularité dépend de nombreux facteurs: goût, facilité, tradition, etc.
        - Un faible score nutritionnel n'empêche pas une recette d'être populaire (et vice-versa).
        """)

    # Footer
    st.markdown("---")
    st.caption("💡 Données: Food.com (231K recettes) | Scoring: Algorithme basé sur WHO/USDA/AHA/EFSA")


if __name__ == "__main__":
    main()
