"""
📊 Analyse des données - Page d'analyse statistique des recettes Food.com

Cette page fournit des visualisations interactives et des statistiques
sur les recettes et les interactions utilisateurs.
"""

# Importer les fonctions centralisées de chargement de données
import sys
from pathlib import Path
from typing import List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from services.data_loader import load_recipes

# Configuration de la page
st.set_page_config(page_title="Analyse des données", page_icon="📊", layout="wide")


@st.cache_data
def load_data() -> Optional[pd.DataFrame]:
    """
    Charge les données des recettes depuis les fichiers CSV.
    Utilise les fonctions centralisées du module data_loader.

    Returns:
        Optional[pd.DataFrame]: DataFrame des recettes ou None si erreur
    """
    try:
        # Utiliser les fonctions centralisées
        recipes_df = load_recipes()

        # Nettoyer et convertir les colonnes numériques
        numeric_cols = [
            "minutes",
            "n_steps",
            "n_ingredients",
            "calories",
            "total_fat",
            "sugar",
            "sodium",
            "protein",
            "saturated_fat",
            "carbohydrates",
        ]

        for col in numeric_cols:
            if col in recipes_df.columns:
                recipes_df[col] = pd.to_numeric(recipes_df[col], errors="coerce")

        # Supprimer les doublons
        recipes_df = recipes_df.drop_duplicates(subset=["id"])

        return recipes_df

    except FileNotFoundError as e:
        st.error(f"❌ Fichier introuvable: {e}")
        st.info("💡 Assurez-vous que le fichier preprocessed_recipes.csv est dans le dossier data/")
        return None
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des données: {str(e)}")
        return None


def parse_tags(recipes_df: pd.DataFrame) -> List[str]:
    """
    Parse et extrait les tags uniques des recettes.

    Args:
        recipes_df: DataFrame des recettes

    Returns:
        List[str]: Liste des tags uniques, triés par fréquence
    """
    if "tags" not in recipes_df.columns:
        return []

    all_tags = []
    for tags_str in recipes_df["tags"].dropna():
        if isinstance(tags_str, str):
            # Supporter plusieurs formats: ['tag1', 'tag2'] ou tag1|tag2
            tags_str = tags_str.strip("[]").replace("'", "").replace('"', "")
            if "|" in tags_str:
                tags = [t.strip() for t in tags_str.split("|")]
            else:
                tags = [t.strip() for t in tags_str.split(",")]
            all_tags.extend(tags)

    # Compter et trier par fréquence
    from collections import Counter

    tag_counts = Counter(all_tags)
    top_tags = [tag for tag, _ in tag_counts.most_common(30)]

    return top_tags


def categorize_recipe(tags_str: str) -> str:
    """
    Catégorise une recette basée sur ses tags.

    Args:
        tags_str: String des tags

    Returns:
        str: Catégorie (main, dessert, vegan, other)
    """
    if pd.isna(tags_str):
        return "other"

    tags_lower = str(tags_str).lower()

    if any(word in tags_lower for word in ["dessert", "cake", "cookie", "pie", "sweet"]):
        return "dessert"
    elif any(word in tags_lower for word in ["vegan", "vegetarian"]):
        return "vegan"
    elif any(word in tags_lower for word in ["main", "dinner", "lunch", "entree"]):
        return "main"
    else:
        return "other"


def apply_filters(
    recipes_df: pd.DataFrame, selected_tags: List[str], min_rating: float, max_minutes: int
) -> pd.DataFrame:
    """
    Applique les filtres sélectionnés aux recettes.

    Args:
        recipes_df: DataFrame des recettes
        selected_tags: Liste des tags sélectionnés
        min_rating: Note minimum
        max_minutes: Temps maximum en minutes

    Returns:
        pd.DataFrame: Recettes filtrées
    """
    filtered_df = recipes_df.copy()

    # Filtre par tags
    if selected_tags:
        mask = filtered_df["tags"].apply(
            lambda x: any(tag in str(x) for tag in selected_tags) if pd.notna(x) else False
        )
        filtered_df = filtered_df[mask]

    # Filtre par note (seulement si avg_rating existe et n'est pas NaN)
    if "avg_rating" in filtered_df.columns:
        filtered_df = filtered_df[(filtered_df["avg_rating"] >= min_rating) | (filtered_df["avg_rating"].isna())]

    # Filtre par temps
    if "minutes" in filtered_df.columns:
        filtered_df = filtered_df[(filtered_df["minutes"] <= max_minutes) | (filtered_df["minutes"].isna())]

    return filtered_df


def create_ingredients_histogram(df: pd.DataFrame) -> go.Figure:
    """Crée un histogramme de la distribution des ingrédients."""
    fig = go.Figure()

    if "n_ingredients" not in df.columns or df["n_ingredients"].isna().all():
        fig.add_annotation(text="Données non disponibles", showarrow=False)
        return fig

    valid_ingredients = df["n_ingredients"].dropna()

    # Histogramme
    fig.add_trace(go.Histogram(x=valid_ingredients, nbinsx=30, name="Recettes", marker_color="#667eea", opacity=0.75))

    # Lignes pour moyenne et médiane
    mean_val = valid_ingredients.mean()
    median_val = valid_ingredients.median()

    fig.add_vline(x=mean_val, line_dash="dash", line_color="red", annotation_text=f"Moyenne: {mean_val:.1f}")
    fig.add_vline(x=median_val, line_dash="dash", line_color="green", annotation_text=f"Médiane: {median_val:.0f}")

    fig.update_layout(
        title="Distribution du Nombre d'Ingrédients par Recette",
        xaxis_title="Nombre d'ingrédients",
        yaxis_title="Nombre de recettes",
        showlegend=False,
        template="plotly_white",
        height=400,
        margin=dict(l=60, r=30, t=80, b=60),
    )

    return fig


def create_time_vs_rating_scatter(df: pd.DataFrame) -> go.Figure:
    """Crée un scatter plot temps vs note avec catégories."""
    fig = go.Figure()

    if "minutes" not in df.columns or "avg_rating" not in df.columns:
        fig.add_annotation(text="Données non disponibles", showarrow=False)
        return fig

    # Ajouter catégorie
    df_plot = df[df["avg_rating"].notna() & df["minutes"].notna()].copy()
    df_plot["category"] = df_plot["tags"].apply(categorize_recipe)

    # Limiter à 2000 points pour la performance
    if len(df_plot) > 2000:
        df_plot = df_plot.sample(n=2000, random_state=42)

    # Scatter avec couleur par catégorie
    fig = px.scatter(
        df_plot,
        x="minutes",
        y="avg_rating",
        color="category",
        title="Temps de préparation vs Note moyenne",
        labels={"minutes": "Temps (min)", "avg_rating": "Note moyenne", "category": "Catégorie"},
        opacity=0.6,
        trendline="lowess",
        color_discrete_map={"main": "#667eea", "dessert": "#f093fb", "vegan": "#85BB2F", "other": "#7f8c8d"},
    )

    fig.update_layout(template="plotly_dark")

    return fig


def create_top_recipes_bar(df: pd.DataFrame) -> go.Figure:
    """Crée un bar chart des top 10 recettes par note."""
    fig = go.Figure()

    if "avg_rating" not in df.columns or "rating_count" not in df.columns:
        fig.add_annotation(text="Données non disponibles", showarrow=False)
        return fig

    # Filtrer recettes avec au moins 30 interactions
    top_recipes = df[df["rating_count"] >= 30].nlargest(10, "avg_rating")

    if top_recipes.empty:
        fig.add_annotation(text="Aucune recette avec ≥30 évaluations", showarrow=False)
        return fig

    # Tronquer les noms longs
    top_recipes["short_name"] = top_recipes["name"].str[:40] + "..."

    fig.add_trace(
        go.Bar(
            y=top_recipes["short_name"],
            x=top_recipes["avg_rating"],
            orientation="h",
            marker_color="#764ba2",
            text=top_recipes["avg_rating"].round(2),
            textposition="auto",
            customdata=top_recipes[["minutes", "n_ingredients", "calories"]],
            hovertemplate="<b>%{y}</b><br>Note: %{x:.2f}<br>Temps: %{customdata[0]:.0f} min<br>Ingrédients: %{customdata[1]:.0f}<br>Calories: %{customdata[2]:.0f}<extra></extra>",
        )
    )

    fig.update_layout(
        title="Top 10 recettes par note moyenne (≥30 évaluations)",
        xaxis_title="Note moyenne",
        yaxis_title="",
        template="plotly_dark",
        height=500,
    )

    return fig


def create_correlation_heatmap(df: pd.DataFrame) -> go.Figure:
    """Crée une heatmap de corrélation des variables numériques."""
    fig = go.Figure()

    numeric_cols = ["minutes", "n_steps", "n_ingredients", "calories", "protein", "total_fat", "sugar", "avg_rating"]

    # Filtrer les colonnes existantes
    available_cols = [col for col in numeric_cols if col in df.columns]

    if len(available_cols) < 2:
        fig.add_annotation(text="Pas assez de données numériques", showarrow=False)
        return fig

    # Calculer la corrélation de Spearman
    corr_matrix = df[available_cols].corr(method="spearman")

    # Créer la heatmap
    fig = go.Figure(
        data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale="RdBu",
            zmid=0,
            text=corr_matrix.values.round(2),
            texttemplate="%{text}",
            textfont={"size": 10},
            colorbar=dict(title="Corrélation<br>Spearman"),
        )
    )

    fig.update_layout(title="Matrice de corrélation (Spearman)", template="plotly_dark", height=600)

    return fig


def create_time_histogram(df: pd.DataFrame) -> go.Figure:
    """Crée un histogramme de la distribution du temps de préparation (filtré pour outliers)."""
    fig = go.Figure()

    if "minutes" not in df.columns or df["minutes"].isna().all():
        fig.add_annotation(text="Données non disponibles", showarrow=False)
        return fig

    # Filtrer les outliers (garder 95% des données)
    valid_times = df["minutes"].dropna()
    p95 = valid_times.quantile(0.95)
    filtered_times = valid_times[valid_times <= p95]

    # Histogramme
    fig.add_trace(go.Histogram(x=filtered_times, nbinsx=40, name="Recettes", marker_color="#667eea", opacity=0.75))

    # Lignes pour moyenne et médiane
    mean_val = filtered_times.mean()
    median_val = filtered_times.median()

    fig.add_vline(x=mean_val, line_dash="dash", line_color="red", annotation_text=f"Moyenne: {mean_val:.0f} min")
    fig.add_vline(x=median_val, line_dash="dash", line_color="green", annotation_text=f"Médiane: {median_val:.0f} min")

    fig.update_layout(
        title=f"Distribution du Temps de Préparation (95% des recettes, ≤{p95:.0f} min)",
        xaxis_title="Temps de préparation (minutes)",
        yaxis_title="Nombre de recettes",
        showlegend=False,
        template="plotly_white",
        height=400,
        margin=dict(l=60, r=30, t=80, b=60),
    )

    return fig


def create_review_distribution(df: pd.DataFrame) -> go.Figure:
    """Crée un histogramme de la distribution des évaluations par recette."""
    fig = go.Figure()

    if "review_count" not in df.columns or df["review_count"].isna().all():
        fig.add_annotation(text="Données 'review_count' non disponibles", showarrow=False)
        return fig

    valid_reviews = df["review_count"].dropna()

    if len(valid_reviews) == 0:
        fig.add_annotation(text="Aucune donnée d'évaluation disponible", showarrow=False)
        return fig

    # Filtrer pour la visualisation (95% des données)
    p95 = valid_reviews.quantile(0.95)
    filtered_reviews = valid_reviews[valid_reviews <= p95]

    # Histogramme
    fig.add_trace(go.Histogram(x=filtered_reviews, nbinsx=50, name="Recettes", marker_color="#f093fb", opacity=0.75))

    # Statistiques
    mean_val = valid_reviews.mean()
    median_val = valid_reviews.median()

    fig.add_vline(x=mean_val, line_dash="dash", line_color="red", annotation_text=f"Moyenne: {mean_val:.0f}")
    fig.add_vline(x=median_val, line_dash="dash", line_color="green", annotation_text=f"Médiane: {median_val:.0f}")

    # Annotation avec stats supplémentaires
    no_reviews = (valid_reviews == 0).sum()
    pct_no_reviews = (no_reviews / len(valid_reviews)) * 100

    fig.add_annotation(
        text=f"Recettes sans évaluation: {no_reviews:,} ({pct_no_reviews:.1f}%)",
        xref="paper",
        yref="paper",
        x=0.98,
        y=0.98,
        showarrow=False,
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="gray",
        borderwidth=1,
        xanchor="right",
        yanchor="top",
    )

    fig.update_layout(
        title=f"Distribution du Nombre d'Évaluations par Recette (95% des données, ≤{p95:.0f} évaluations)",
        xaxis_title="Nombre d'évaluations par recette",
        yaxis_title="Nombre de recettes",
        showlegend=False,
        template="plotly_white",
        height=400,
        margin=dict(l=60, r=30, t=80, b=60),
    )

    return fig


def create_complexity_pie_chart(df: pd.DataFrame) -> go.Figure:
    """Crée un pie chart de la répartition par niveau de complexité."""

    # Calculate complexity index for recipes
    df_copy = df.copy()

    # Normalize components to 0-1 scale
    if "n_steps" in df_copy.columns:
        steps_min, steps_max = df_copy["n_steps"].min(), df_copy["n_steps"].max()
        df_copy["steps_norm"] = (
            (df_copy["n_steps"] - steps_min) / (steps_max - steps_min) if steps_max > steps_min else 0
        )
    else:
        df_copy["steps_norm"] = 0

    if "n_ingredients" in df_copy.columns:
        ing_min, ing_max = df_copy["n_ingredients"].min(), df_copy["n_ingredients"].max()
        df_copy["ingredients_norm"] = (
            (df_copy["n_ingredients"] - ing_min) / (ing_max - ing_min) if ing_max > ing_min else 0
        )
    else:
        df_copy["ingredients_norm"] = 0

    if "minutes" in df_copy.columns:
        time_min, time_max = df_copy["minutes"].min(), df_copy["minutes"].max()
        df_copy["time_norm"] = (df_copy["minutes"] - time_min) / (time_max - time_min) if time_max > time_min else 0
    else:
        df_copy["time_norm"] = 0

    # Calculate complexity index (0-100)
    df_copy["complexity_index"] = (
        0.4 * df_copy["steps_norm"] + 0.4 * df_copy["ingredients_norm"] + 0.2 * df_copy["time_norm"]
    ) * 100

    # Categorize complexity
    def categorize_complexity(complexity):
        if pd.isna(complexity):
            return "Inconnu"
        if complexity <= 33:
            return "Simple"
        elif complexity <= 66:
            return "Moyen"
        else:
            return "Complexe"

    df_copy["complexity_category"] = df_copy["complexity_index"].apply(categorize_complexity)

    # Count recipes per category
    category_counts = df_copy["complexity_category"].value_counts()

    # Define colors
    colors = {
        "Simple": "#85BB2F",  # Green
        "Moyen": "#FECC00",  # Yellow
        "Complexe": "#FF9500",  # Orange
        "Inconnu": "#CCCCCC",  # Gray
    }

    # Order categories
    category_order = ["Simple", "Moyen", "Complexe", "Inconnu"]
    category_counts = category_counts.reindex([cat for cat in category_order if cat in category_counts.index])

    fig = go.Figure(
        data=[
            go.Pie(
                labels=category_counts.index,
                values=category_counts.values,
                marker=dict(colors=[colors.get(cat, "#CCCCCC") for cat in category_counts.index]),
                textinfo="label+percent",
                textfont=dict(size=14),
                hole=0.3,  # Donut chart
            )
        ]
    )

    fig.update_layout(
        title="Répartition par Niveau de Complexité<br><sub>Basé sur: nombre d'étapes (40%), ingrédients (40%), temps (20%)</sub>",
        template="plotly_white",
        height=450,
        showlegend=True,
        margin=dict(l=60, r=60, t=100, b=60),
    )

    return fig


def create_nutrition_grade_bar(df: pd.DataFrame) -> go.Figure:
    """Crée un bar chart de la distribution des grades nutritionnels avec score moyen."""
    fig = go.Figure()

    if "nutrition_grade" not in df.columns or df["nutrition_grade"].isna().all():
        fig.add_annotation(text="Données 'nutrition_grade' non disponibles", showarrow=False)
        return fig

    # Compter les grades
    grade_counts = df["nutrition_grade"].value_counts().reindex(["A", "B", "C", "D", "E"], fill_value=0)
    grade_pct = (grade_counts / len(df) * 100).round(1)

    # Calculer le score moyen et médian par grade
    grade_avg_scores = {}
    grade_median_scores = {}
    for grade in ["A", "B", "C", "D", "E"]:
        grade_data = df[df["nutrition_grade"] == grade]
        if len(grade_data) > 0 and "nutrition_score" in df.columns:
            grade_avg_scores[grade] = grade_data["nutrition_score"].mean()
            grade_median_scores[grade] = grade_data["nutrition_score"].median()
        else:
            grade_avg_scores[grade] = 0
            grade_median_scores[grade] = 0

    # Couleurs par grade
    grade_colors = {"A": "#238B45", "B": "#85BB2F", "C": "#FECC00", "D": "#FF9500", "E": "#E63946"}

    colors = [grade_colors[grade] for grade in grade_counts.index]

    # Bar chart
    fig.add_trace(
        go.Bar(
            x=grade_counts.index,
            y=grade_counts.values,
            marker_color=colors,
            text=[
                f"{count:,}<br>({pct}%)<br>Moy: {grade_avg_scores[grade]:.1f}<br>Méd: {grade_median_scores[grade]:.1f}"
                for count, pct, grade in zip(grade_counts.values, grade_pct.values, grade_counts.index)
            ],
            textposition="auto",
            textfont=dict(size=10),
            hovertemplate="<b>Grade %{x}</b><br>Recettes: %{y:,}<br>Pourcentage: %{text}<extra></extra>",
        )
    )

    fig.update_layout(
        title="Distribution des Grades Nutritionnels (A = Excellent, E = À Améliorer)",
        xaxis_title="Grade Nutritionnel",
        yaxis_title="Nombre de recettes",
        showlegend=False,
        template="plotly_white",
        height=450,
        margin=dict(l=60, r=30, t=80, b=60),
    )

    return fig


def filter_outliers_for_overview(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter dataset to remove extreme outliers for better visualizations.
    More aggressive filtering: 0.5%-99.5% percentile.
    """
    df_filtered = df.copy()

    # Filter minutes (cooking time) - remove extreme values
    if "minutes" in df_filtered.columns:
        p05, p995 = df_filtered["minutes"].quantile([0.005, 0.995])
        df_filtered = df_filtered[(df_filtered["minutes"] >= p05) & (df_filtered["minutes"] <= p995)]

    # Filter n_steps - remove extreme values
    if "n_steps" in df_filtered.columns:
        p05, p995 = df_filtered["n_steps"].quantile([0.005, 0.995])
        df_filtered = df_filtered[(df_filtered["n_steps"] >= p05) & (df_filtered["n_steps"] <= p995)]

    # Filter n_ingredients - remove extreme values
    if "n_ingredients" in df_filtered.columns:
        p05, p995 = df_filtered["n_ingredients"].quantile([0.005, 0.995])
        df_filtered = df_filtered[(df_filtered["n_ingredients"] >= p05) & (df_filtered["n_ingredients"] <= p995)]

    # Filter calories - remove extreme values
    if "calories" in df_filtered.columns:
        p05, p995 = df_filtered["calories"].quantile([0.005, 0.995])
        df_filtered = df_filtered[(df_filtered["calories"] >= p05) & (df_filtered["calories"] <= p995)]

    return df_filtered


def main():
    """Fonction principale de la page d'analyse."""

    st.title("📊 Analyse des Données")

    # Introduction Section
    st.markdown("""
    ### Vue d'ensemble du Dataset Food.com
    
    Ce dataset contient **231,637 recettes** collectées sur Food.com entre 1999 et 2018, 
    accompagnées de **1,132,367 évaluations** d'utilisateurs. Chaque recette inclut des informations 
    détaillées sur les ingrédients, le temps de préparation, les étapes, et les valeurs nutritionnelles.
    
    **Source**: Kaggle - Food.com Recipes and User Interactions  
    **Période**: 1999-2018  
    **Traitement**: Scores nutritionnels calculés selon standards WHO/USDA/AHA/EFSA
    """)

    st.markdown("---")

    # Charger les données avec spinner
    with st.spinner("Chargement des données..."):
        recipes_df = load_data()

    # Vérifier si les données sont chargées
    if recipes_df is None:
        st.stop()

    # Apply outlier filtering
    with st.spinner("Filtrage des valeurs extrêmes..."):
        filtered_df = filter_outliers_for_overview(recipes_df)

    outliers_removed = len(recipes_df) - len(filtered_df)
    outliers_pct = (outliers_removed / len(recipes_df)) * 100

    outliers_removed = len(recipes_df) - len(filtered_df)
    outliers_pct = (outliers_removed / len(recipes_df)) * 100

    # KPIs - Updated with 4 metrics including mode and average review
    st.subheader("📊 Statistiques Clés du Dataset")

    # Show filtering info
    st.info(
        f"✅ {len(recipes_df):,} recettes chargées | {len(filtered_df):,} après filtrage des outliers ({outliers_removed:,} recettes extrêmes retirées, {outliers_pct:.1f}%)"
    )

    # Row 1: 3 main metrics
    kpi1, kpi2, kpi3 = st.columns(3)

    with kpi1:
        st.metric("🍽️ Total Recettes", f"{len(filtered_df):,}")

    with kpi2:
        if "nutrition_grade" in filtered_df.columns:
            mode_grade = (
                filtered_df["nutrition_grade"].mode()[0] if len(filtered_df["nutrition_grade"].mode()) > 0 else "N/A"
            )
            st.metric("🏆 Grade le Plus Commun", mode_grade)
        else:
            st.metric("🏆 Grade le Plus Commun", "N/A")

    with kpi3:
        if "minutes" in filtered_df.columns:
            median_time = filtered_df["minutes"].median()
            st.metric("⏱️ Temps Médian", f"{median_time:.0f} min" if not pd.isna(median_time) else "N/A")
        else:
            st.metric("⏱️ Temps Médian", "N/A")

    # Row 2: Nutrition and rating metrics
    kpi4, kpi5, kpi6 = st.columns(3)

    with kpi4:
        if "nutrition_score" in filtered_df.columns:
            mean_nutrition_score = filtered_df["nutrition_score"].mean()
            st.metric(
                "📊 Score Nutritionnel Moy.",
                f"{mean_nutrition_score:.1f}" if not pd.isna(mean_nutrition_score) else "N/A",
            )
        else:
            st.metric("📊 Score Nutritionnel Moy.", "N/A")

    with kpi5:
        if "nutrition_score" in filtered_df.columns:
            median_nutrition_score = filtered_df["nutrition_score"].median()
            st.metric(
                "📊 Score Nutritionnel Méd.",
                f"{median_nutrition_score:.1f}" if not pd.isna(median_nutrition_score) else "N/A",
            )
        else:
            st.metric("📊 Score Nutritionnel Méd.", "N/A")

    with kpi6:
        if "average_rating" in filtered_df.columns:
            avg_user_rating = filtered_df["average_rating"].mean()
            st.metric("⭐ Note Utilisateur Moy.", f"{avg_user_rating:.2f}" if not pd.isna(avg_user_rating) else "N/A")
        else:
            st.metric("⭐ Note Utilisateur Moy.", "N/A")

    st.markdown("---")

    # Section des graphiques
    st.subheader("� Visualisations du Dataset")

    # Chart 1: Distribution des ingrédients
    st.markdown("#### 1. Distribution du Nombre d'Ingrédients")
    with st.container():
        fig = create_ingredients_histogram(filtered_df)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Chart 2: Distribution du temps de préparation
    st.markdown("#### 2. Distribution du Temps de Préparation")
    with st.container():
        fig_time = create_time_histogram(filtered_df)
        st.plotly_chart(fig_time, use_container_width=True)

    st.markdown("---")

    # Chart 3: Distribution des avis utilisateurs (NOUVEAU)
    st.markdown("#### 3. Distribution des Évaluations par Recette")
    with st.container():
        fig_reviews = create_review_distribution(filtered_df)
        st.plotly_chart(fig_reviews, use_container_width=True)

    st.markdown("---")

    # Chart 4: Complexity pie chart
    st.markdown("#### 4. Répartition par Niveau de Complexité")
    with st.container():
        fig_complexity = create_complexity_pie_chart(filtered_df)
        st.plotly_chart(fig_complexity, use_container_width=True)

    st.markdown("---")

    # Footer
    st.caption("💡 Données: Food.com Recipes and User Interactions (Kaggle) | 231,637 recettes | 1999-2018")


# Function for nutrition score histogram


def create_nutrition_score_histogram(df: pd.DataFrame) -> go.Figure:
    """Crée un histogramme de la distribution des scores nutritionnels."""
    if "nutrition_score" not in df.columns:
        fig = go.Figure()
        fig.add_annotation(
            text="Colonne 'nutrition_score' non trouvée", x=0.5, y=0.5, showarrow=False, font=dict(size=16, color="red")
        )
        fig.update_layout(title="Distribution des scores nutritionnels - Données manquantes", template="plotly_dark")
        return fig

    valid_scores = df["nutrition_score"].dropna()
    if len(valid_scores) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="Aucune donnée disponible", x=0.5, y=0.5, showarrow=False, font=dict(size=16, color="orange")
        )
        fig.update_layout(title="Distribution des scores nutritionnels - Aucune donnée", template="plotly_dark")
        return fig

    fig = go.Figure()
    fig.add_trace(go.Histogram(x=valid_scores, nbinsx=30, marker_color="#f093fb", opacity=0.7))

    mean_score = valid_scores.mean()
    median_score = valid_scores.median()

    fig.add_vline(x=mean_score, line_dash="dash", line_color="yellow", annotation_text=f"Moyenne: {mean_score:.1f}")
    fig.add_vline(x=median_score, line_dash="dot", line_color="orange", annotation_text=f"Médiane: {median_score:.1f}")

    fig.update_layout(
        title=f"Distribution des scores nutritionnels (n={len(valid_scores):,})",
        xaxis_title="Score nutritionnel",
        yaxis_title="Nombre de recettes",
        template="plotly_dark",
        showlegend=False,
    )
    return fig


if __name__ == "__main__":
    main()
