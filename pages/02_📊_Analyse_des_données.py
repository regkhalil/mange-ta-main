"""
📊 Analyse des données - Page d'analyse statistique des recettes Food.com

Cette page fournit des visualisations interactives et des statistiques
sur les recettes et les interactions utilisateurs.
"""

# Importer les fonctions centralisées de chargement de données
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from services.data_loader import load_recipes, read_raw_interactions

# Configuration de la page
st.set_page_config(page_title="Analyse des données", page_icon="📊", layout="wide")


@st.cache_data
def load_data() -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """
    Charge les données des recettes et des interactions depuis les fichiers CSV.
    Utilise les fonctions centralisées du module data_loader.

    Returns:
        Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        (recipes_df, interactions_df) ou (None, None) si erreur
    """
    try:
        # Utiliser les fonctions centralisées
        recipes_df = load_recipes()
        interactions_df = read_raw_interactions()

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

        # Nettoyer les interactions (déjà chargé par read_raw_interactions)
        interactions_df["rating"] = pd.to_numeric(interactions_df["rating"], errors="coerce")
        interactions_df = interactions_df.dropna(subset=["recipe_id", "user_id"])

        return recipes_df, interactions_df

    except FileNotFoundError as e:
        st.error(f"❌ Fichier introuvable: {e}")
        st.info(
            "💡 Assurez-vous que les fichiers preprocessed_recipes.csv et RAW_interactions.csv sont dans le dossier data/"
        )
        return None, None
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des données: {str(e)}")
        return None, None


def compute_avg_rating(recipes_df: pd.DataFrame, interactions_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule la note moyenne pour chaque recette à partir des interactions.

    Args:
        recipes_df: DataFrame des recettes
        interactions_df: DataFrame des interactions

    Returns:
        pd.DataFrame: Recettes avec la colonne avg_rating ajoutée
    """
    # Filtrer les ratings valides (1-5)
    valid_ratings = interactions_df[(interactions_df["rating"] >= 1) & (interactions_df["rating"] <= 5)].copy()

    # Calculer les statistiques par recette
    rating_stats = valid_ratings.groupby("recipe_id").agg({"rating": ["mean", "count"]}).reset_index()

    rating_stats.columns = ["id", "avg_rating", "rating_count"]

    # Joindre avec les recettes
    recipes_with_ratings = recipes_df.merge(rating_stats, on="id", how="left")

    # Remplir les valeurs manquantes
    recipes_with_ratings["avg_rating"] = recipes_with_ratings["avg_rating"].fillna(np.nan)
    recipes_with_ratings["rating_count"] = recipes_with_ratings["rating_count"].fillna(0).astype(int)

    return recipes_with_ratings


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

    # Histogramme
    fig.add_trace(go.Histogram(x=df["n_ingredients"].dropna(), nbinsx=30, name="Recettes", marker_color="#667eea"))

    # Lignes pour moyenne et médiane
    mean_val = df["n_ingredients"].mean()
    median_val = df["n_ingredients"].median()

    fig.add_vline(x=mean_val, line_dash="dash", line_color="red", annotation_text=f"Moyenne: {mean_val:.1f}")
    fig.add_vline(x=median_val, line_dash="dash", line_color="green", annotation_text=f"Médiane: {median_val:.1f}")

    fig.update_layout(
        title="Distribution du nombre d'ingrédients",
        xaxis_title="Nombre d'ingrédients",
        yaxis_title="Nombre de recettes",
        showlegend=False,
        template="plotly_dark",
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


def create_user_activity_charts(interactions_df: pd.DataFrame) -> Tuple[go.Figure, go.Figure]:
    """Crée les charts d'activité utilisateurs."""
    # Chart 1: Top 10 users par nombre d'interactions
    user_counts = interactions_df.groupby("user_id").size().nlargest(10).reset_index()
    user_counts.columns = ["user_id", "count"]

    fig1 = go.Figure(
        data=[
            go.Bar(
                x=user_counts["user_id"].astype(str),
                y=user_counts["count"],
                marker_color="#667eea",
                text=user_counts["count"],
                textposition="auto",
            )
        ]
    )

    fig1.update_layout(
        title="Top 10 utilisateurs par nombre d'interactions",
        xaxis_title="User ID",
        yaxis_title="Nombre d'interactions",
        template="plotly_dark",
    )

    # Chart 2: Note moyenne donnée par ces utilisateurs
    top_users = user_counts["user_id"].tolist()
    user_avg_rating = (
        interactions_df[
            (interactions_df["user_id"].isin(top_users))
            & (interactions_df["rating"] >= 1)
            & (interactions_df["rating"] <= 5)
        ]
        .groupby("user_id")["rating"]
        .mean()
        .reset_index()
    )

    fig2 = go.Figure(
        data=[
            go.Bar(
                x=user_avg_rating["user_id"].astype(str),
                y=user_avg_rating["rating"],
                marker_color="#f093fb",
                text=user_avg_rating["rating"].round(2),
                textposition="auto",
            )
        ]
    )

    fig2.update_layout(
        title="Note moyenne donnée par les top utilisateurs",
        xaxis_title="User ID",
        yaxis_title="Note moyenne",
        template="plotly_dark",
    )

    return fig1, fig2


def main():
    """Fonction principale de la page d'analyse."""

    st.title("📊 Analyse des données")
    st.markdown("**Analyse statistique des recettes Food.com**")

    # Charger les données avec spinner
    with st.spinner("Chargement des données..."):
        recipes_df, interactions_df = load_data()

    # Vérifier si les données sont chargées
    if recipes_df is None or interactions_df is None:
        st.stop()

    # Calculer les notes moyennes
    with st.spinner("Calcul des statistiques..."):
        recipes_df = compute_avg_rating(recipes_df, interactions_df)
        available_tags = parse_tags(recipes_df)

    # Layout: 2 colonnes pour filtres et KPIs
    col_filters, col_kpis = st.columns([2, 1])

    with col_filters:
        st.subheader("🎛️ Filtres")

        # Filtres en colonnes
        fcol1, fcol2, fcol3 = st.columns(3)

        with fcol1:
            selected_tags = st.multiselect("Tags (top 30)", options=available_tags, default=[], key="tag_filter")

        with fcol2:
            min_rating = st.slider(
                "Note minimum", min_value=0.0, max_value=5.0, value=3.0, step=0.5, key="rating_filter"
            )

        with fcol3:
            max_minutes = st.slider(
                "Temps max (min)", min_value=10, max_value=300, value=120, step=10, key="time_filter"
            )

        # Bouton de réinitialisation
        if st.button("♻️ Réinitialiser les filtres"):
            st.session_state.tag_filter = []
            st.session_state.rating_filter = 3.0
            st.session_state.time_filter = 120
            st.rerun()

    # Appliquer les filtres
    filtered_df = apply_filters(recipes_df, selected_tags, min_rating, max_minutes)

    # KPIs
    with col_kpis:
        st.subheader("📈 Métriques")

        kpi1, kpi2, kpi3 = st.columns(1)

        with kpi1:
            st.metric("🍽️ Recettes", f"{len(filtered_df):,}")

        if "avg_rating" in filtered_df.columns:
            avg_rating_val = filtered_df["avg_rating"].mean()
            st.metric("⭐ Note moyenne", f"{avg_rating_val:.2f}" if not pd.isna(avg_rating_val) else "N/A")

        if "minutes" in filtered_df.columns:
            median_time = filtered_df["minutes"].median()
            st.metric("⏱️ Temps médian", f"{median_time:.0f} min" if not pd.isna(median_time) else "N/A")

    # Message d'information sur le filtrage
    st.info(f"📊 **{len(filtered_df):,} recettes** correspondent à vos critères")

    # Gestion du cas où il n'y a pas de résultats
    if len(filtered_df) == 0:
        st.warning("😕 Aucune recette trouvée. Voulez-vous revenir à la page d'accueil ?")

        bcol1, bcol2 = st.columns(2)
        with bcol1:
            if st.button("✅ Oui, revenir à l'accueil"):
                st.switch_page("app.py")
        with bcol2:
            if st.button("❌ Non, garder les filtres"):
                st.rerun()

        st.stop()

    st.markdown("---")

    # Section des graphiques
    st.subheader("📊 Visualisations")

    # Chart 1: Distribution des ingrédients
    with st.container():
        fig = create_ingredients_histogram(filtered_df)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Chart 2: Distribution des scores nutritionnels
    with st.container():
        fig_nutrition = create_nutrition_score_histogram(filtered_df)
        st.plotly_chart(fig_nutrition, use_container_width=True)

    st.markdown("---")

    # Chart 3: Temps vs Note
    with st.container():
        fig = create_time_vs_rating_scatter(filtered_df)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Chart 3: Top recettes
    with st.container():
        fig = create_top_recipes_bar(filtered_df)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Chart 4: Corrélations
    with st.container():
        fig = create_correlation_heatmap(filtered_df)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Chart 5: Activité utilisateurs (dans des onglets)
    st.subheader("👥 Activité des utilisateurs")

    tab1, tab2 = st.tabs(["📊 Nombre d'interactions", "⭐ Notes moyennes"])

    fig1, fig2 = create_user_activity_charts(interactions_df)

    with tab1:
        st.plotly_chart(fig1, use_container_width=True)

    with tab2:
        st.plotly_chart(fig2, use_container_width=True)

    # Footer
    st.markdown("---")
    st.caption("💡 Données provenant de Kaggle: Food.com Recipes and User Interactions")


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
    # std_score = valid_scores.std()

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
