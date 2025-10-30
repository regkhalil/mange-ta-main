"""
Section 3: Ingredient Health Index
Analyzes which ingredients are associated with healthy/unhealthy recipes.
"""

import ast
import logging

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import spearmanr

logger = logging.getLogger(__name__)


def parse_ingredients(ingredients_str):
    """Parse ingredient list from string format."""
    if pd.isna(ingredients_str):
        return []
    try:
        if isinstance(ingredients_str, str):
            return ast.literal_eval(ingredients_str)
        return list(ingredients_str)
    except Exception:
        return []


def calculate_ingredient_health_index(df: pd.DataFrame, min_frequency: int = 100) -> pd.DataFrame:
    """
    Load precomputed ingredient health index and add calculated metrics.

    Loads base statistics from preprocessing. Median and consistency are
    calculated directly from precomputed stats for performance.

    Args:
        df: Recipe dataframe (unused, kept for backward compatibility)
        min_frequency: Minimum number of occurrences (unused, kept for backward compatibility)

    Returns:
        DataFrame with ingredient statistics including calculated metrics
    """
    logger.info("Loading precomputed ingredient health index from CSV")

    # Import data_loader for standardized CSV reading (supports both local and Google Drive)
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from services.data_loader import read_csv_file

    # Load using centralized data loader with explicit dtypes
    # This handles both local and production (Google Drive) workflows
    try:
        stats_df = read_csv_file(
            "ingredient_health_index.csv",
            dtype={
                "ingredient": str,
                "avg_score": float,
                "median_score": float,
                "frequency": float,  # CRITICAL: Read as float, not object
                "std_score": float,
                "min_score": float,
                "max_score": float,
                "consistency": float,
            },
        )
    except FileNotFoundError:
        logger.error("Precomputed ingredient health index not found")
        return pd.DataFrame(columns=["ingredient", "avg_score", "frequency", "std_score", "min_score", "max_score"])
    except (ValueError, TypeError) as e:
        # Fallback: If dtype specification fails, read naturally and force conversion
        logger.warning(f"Failed to read CSV with explicit dtypes: {e}. Falling back to natural read + conversion.")
        stats_df = read_csv_file("ingredient_health_index.csv")
        
        # Force numeric conversion for all numeric columns
        numeric_cols = ["avg_score", "median_score", "frequency", "std_score", "min_score", "max_score", "consistency"]
        for col in numeric_cols:
            if col in stats_df.columns:
                stats_df[col] = pd.to_numeric(stats_df[col], errors="coerce")
        
        # Drop any rows with non-numeric frequency
        stats_df = stats_df.dropna(subset=["frequency"])

    # Clean and format ingredient names for display
    stats_df["ingredient"] = stats_df["ingredient"].str.strip().str.title()

    # Filter by minimum frequency
    stats_df = stats_df[stats_df["frequency"] >= min_frequency]

    logger.info(
        f"Loaded {len(stats_df)} ingredients from precomputed index (frequency dtype: {stats_df['frequency'].dtype})"
    )

    return stats_df


def compare_sugar_vs_salt(df: pd.DataFrame) -> dict:
    """
    Compare the effect of sugar vs salt (sodium) on nutrition scores.

    Args:
        df: Recipe dataframe with precomputed nutrient columns

    Returns:
        Dictionary with comparison statistics
    """
    # Use precomputed nutrient columns directly
    nutrition_data = df[["sugar_pdv", "sodium_pdv", "nutrition_score"]].copy()

    # Clean data
    clean_data = nutrition_data.dropna()

    # Correlation analysis
    sugar_corr, sugar_p = spearmanr(clean_data["sugar_pdv"], clean_data["nutrition_score"])
    sodium_corr, sodium_p = spearmanr(clean_data["sodium_pdv"], clean_data["nutrition_score"])

    # Categorize into high/low
    sugar_median = clean_data["sugar_pdv"].median()
    sodium_median = clean_data["sodium_pdv"].median()

    high_sugar = clean_data[clean_data["sugar_pdv"] > sugar_median]
    low_sugar = clean_data[clean_data["sugar_pdv"] <= sugar_median]
    high_sodium = clean_data[clean_data["sodium_pdv"] > sodium_median]
    low_sodium = clean_data[clean_data["sodium_pdv"] <= sodium_median]

    return {
        "sugar_correlation": sugar_corr,
        "sugar_p_value": sugar_p,
        "sodium_correlation": sodium_corr,
        "sodium_p_value": sodium_p,
        "high_sugar_avg_score": high_sugar["nutrition_score"].mean(),
        "low_sugar_avg_score": low_sugar["nutrition_score"].mean(),
        "high_sodium_avg_score": high_sodium["nutrition_score"].mean(),
        "low_sodium_avg_score": low_sodium["nutrition_score"].mean(),
        "data": clean_data,
        "sugar_median": sugar_median,
        "sodium_median": sodium_median,
    }


def create_ingredient_scatter(df: pd.DataFrame, top_n: int = 50) -> go.Figure:
    """
    Create scatter plot of ingredient frequency vs average score.

    Args:
        df: Recipe dataframe
        top_n: Number of top ingredients to show

    Returns:
        Plotly figure
    """
    ingredient_stats = calculate_ingredient_health_index(df, min_frequency=100)

    # Take top N by frequency
    top_ingredients = ingredient_stats.nlargest(top_n, "frequency")

    fig = px.scatter(
        top_ingredients,
        x="frequency",
        y="avg_score",
        size="std_score",
        hover_data=["ingredient", "std_score"],
        text="ingredient",
        title=f"Top {top_n} Ingrédients: Fréquence vs Score Nutritionnel Moyen",
        labels={
            "frequency": "Fréquence (nombre de recettes)",
            "avg_score": "Score Nutritionnel Moyen",
            "std_score": "Écart-type",
        },
    )

    fig.update_traces(textposition="top center", textfont_size=8)

    fig.update_layout(template="plotly_white", height=600, showlegend=False)

    return fig


def create_top_ingredients_table(df: pd.DataFrame, top_n: int = 20, sort_by: str = "healthiest") -> pd.DataFrame:
    """
    Create table of top healthiest/unhealthiest ingredients.

    Args:
        df: Recipe dataframe
        top_n: Number of ingredients to show
        sort_by: 'healthiest' or 'unhealthiest'

    Returns:
        DataFrame for display
    """
    ingredient_stats = calculate_ingredient_health_index(df, min_frequency=100)

    if sort_by == "healthiest":
        top = ingredient_stats.nlargest(top_n, "avg_score")
    else:
        top = ingredient_stats.nsmallest(top_n, "avg_score")

    # Format for display - show avg_score, std_score (variability), and frequency
    display_df = top[["ingredient", "avg_score", "std_score", "frequency"]].copy()
    display_df.columns = ["Ingrédient", "Score Moyen", "Variabilité", "Fréquence"]
    display_df["Score Moyen"] = display_df["Score Moyen"].round(1)
    display_df["Variabilité"] = display_df["Variabilité"].round(1)
    display_df = display_df.reset_index(drop=True)

    return display_df


def create_nutrition_popularity_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create table showing relationship between nutrition scores and popularity.

    Args:
        df: Recipe dataframe with nutrition_score, nutrition_grade, and popularity_score

    Returns:
        DataFrame with statistics for display
    """
    logger.info(f"Calculating nutrition vs popularity statistics for {len(df)} recipes")

    # Clean data
    clean_df = df[["nutrition_score", "nutrition_grade", "popularity_score", "average_rating"]].dropna()
    clean_df = clean_df[clean_df["popularity_score"] > 0]  # Remove recipes with no popularity data

    stats = []

    # Stats by nutrition grade - easier to understand than correlation
    for grade in ["A", "B", "C", "D", "E"]:
        grade_data = clean_df[clean_df["nutrition_grade"] == grade]
        if len(grade_data) > 0:
            avg_pop = grade_data["popularity_score"].mean()
            avg_rating = grade_data["average_rating"].mean()
            count = len(grade_data)
            pct_of_total = (count / len(clean_df)) * 100

            stats.append(
                {
                    "Métrique": f"Grade {grade}",
                    "Score d'Engagement": f"{avg_pop:.2f}",
                    "Note Moyenne": f"{avg_rating:.2f}/5",
                    "Nombre de Recettes": f"{count:,} ({pct_of_total:.1f}%)",
                }
            )

    # Add separator
    stats.append({"Métrique": "—", "Score d'Engagement": "—", "Note Moyenne": "—", "Nombre de Recettes": "—"})

    # Top 10% healthiest vs bottom 10%
    top_10_threshold = clean_df["nutrition_score"].quantile(0.9)
    bottom_10_threshold = clean_df["nutrition_score"].quantile(0.1)

    top_10_data = clean_df[clean_df["nutrition_score"] >= top_10_threshold]
    bottom_10_data = clean_df[clean_df["nutrition_score"] <= bottom_10_threshold]

    top_10_pop = top_10_data["popularity_score"].mean()
    bottom_10_pop = bottom_10_data["popularity_score"].mean()

    top_10_rating = top_10_data["average_rating"].mean()
    bottom_10_rating = bottom_10_data["average_rating"].mean()

    stats.append(
        {
            "Métrique": f"Top 10% Plus Saines (score ≥{top_10_threshold:.0f})",
            "Score d'Engagement": f"{top_10_pop:.2f}",
            "Note Moyenne": f"{top_10_rating:.2f}/5",
            "Nombre de Recettes": f"{len(top_10_data):,}",
        }
    )

    stats.append(
        {
            "Métrique": f"Bottom 10% Moins Saines (score ≤{bottom_10_threshold:.0f})",
            "Score d'Engagement": f"{bottom_10_pop:.2f}",
            "Note Moyenne": f"{bottom_10_rating:.2f}/5",
            "Nombre de Recettes": f"{len(bottom_10_data):,}",
        }
    )

    # Calculate percentage difference
    pop_diff_pct = ((top_10_pop - bottom_10_pop) / bottom_10_pop) * 100
    rating_diff = top_10_rating - bottom_10_rating

    stats.append(
        {
            "Métrique": "Différence (Top vs Bottom)",
            "Score d'Engagement": f"{pop_diff_pct:+.1f}%",
            "Note Moyenne": f"{rating_diff:+.2f}",
            "Nombre de Recettes": "—",
        }
    )

    stats_df = pd.DataFrame(stats)

    logger.info(f"Generated {len(stats_df)} popularity statistics")

    return stats_df


def create_nutrition_popularity_scatter(df: pd.DataFrame, sample_size: int = 5000) -> go.Figure:
    """
    Create scatter plot showing relationship between nutrition score and popularity.

    Args:
        df: Recipe dataframe with nutrition_score, nutrition_grade, and popularity_score
        sample_size: Number of recipes to sample for visualization (for performance)

    Returns:
        Plotly figure
    """
    logger.info("Creating nutrition vs popularity scatter plot")

    # Clean data
    clean_df = df[["nutrition_score", "nutrition_grade", "popularity_score", "name"]].dropna()
    clean_df = clean_df[clean_df["popularity_score"] > 0]  # Remove recipes with no popularity data

    # Sample for performance
    if len(clean_df) > sample_size:
        plot_df = clean_df.sample(n=sample_size, random_state=42)
    else:
        plot_df = clean_df

    # Define grade colors
    grade_colors = {"A": "#238B45", "B": "#85BB2F", "C": "#FECC00", "D": "#FF9500", "E": "#E63946"}

    fig = px.scatter(
        plot_df,
        x="nutrition_score",
        y="popularity_score",
        color="nutrition_grade",
        color_discrete_map=grade_colors,
        hover_data=["name"],
        title="Score Nutritionnel vs Popularité des Recettes",
        labels={
            "nutrition_score": "Score Nutritionnel",
            "popularity_score": "Score de Popularité",
            "nutrition_grade": "Grade",
            "name": "Recette",
        },
        category_orders={"nutrition_grade": ["A", "B", "C", "D", "E"]},
        opacity=0.5,
    )

    # Add trend line
    from scipy.stats import linregress

    slope, intercept, r_value, p_value, std_err = linregress(plot_df["nutrition_score"], plot_df["popularity_score"])

    x_range = np.array([plot_df["nutrition_score"].min(), plot_df["nutrition_score"].max()])
    y_trend = slope * x_range + intercept

    fig.add_trace(
        go.Scatter(
            x=x_range,
            y=y_trend,
            mode="lines",
            name=f"Tendance (R²={r_value**2:.3f})",
            line=dict(color="black", dash="dash", width=2),
            showlegend=True,
        )
    )

    fig.update_layout(
        template="plotly_white",
        height=500,
        xaxis=dict(title="Score Nutritionnel (10-98)", range=[0, 100]),
        yaxis=dict(title="Score de Popularité"),
        legend=dict(title="Grade Nutritionnel", orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
    )

    fig.update_traces(marker=dict(size=5))

    logger.info(f"Created scatter plot with {len(plot_df)} recipes")

    return fig


def create_sugar_salt_comparison(df: pd.DataFrame) -> tuple:
    """
    Create visualizations comparing sugar vs salt effects.

    Args:
        df: Recipe dataframe

    Returns:
        Tuple of (scatter_fig, box_fig, bar_fig)
    """
    comparison = compare_sugar_vs_salt(df)
    data = comparison["data"]

    # 1. Scatter plot: Sugar vs Sodium colored by score
    fig_scatter = px.scatter(
        data.sample(n=min(5000, len(data)), random_state=42),
        x="sugar_pdv",
        y="sodium_pdv",
        color="nutrition_score",
        color_continuous_scale="RdYlGn",
        title=f"Sucres vs Sodium (%DV) - Coloré par Score<br><sub>Corrélation Sucres: ρ={comparison['sugar_correlation']:.3f}, Sodium: ρ={comparison['sodium_correlation']:.3f}</sub>",
        labels={"sugar_pdv": "Sucres (%DV)", "sodium_pdv": "Sodium (%DV)", "nutrition_score": "Score"},
        opacity=0.5,
    )
    fig_scatter.update_layout(template="plotly_white", height=500)

    # 2. Box plots: Score distribution for high/low sugar and sodium
    fig_box = go.Figure()

    sugar_high = data[data["sugar_pdv"] > comparison["sugar_median"]]
    sugar_low = data[data["sugar_pdv"] <= comparison["sugar_median"]]
    sodium_high = data[data["sodium_pdv"] > comparison["sodium_median"]]
    sodium_low = data[data["sodium_pdv"] <= comparison["sodium_median"]]

    fig_box.add_trace(go.Box(y=sugar_high["nutrition_score"], name="Sucres Élevés", marker_color="#E63946"))
    fig_box.add_trace(go.Box(y=sugar_low["nutrition_score"], name="Sucres Faibles", marker_color="#238B45"))
    fig_box.add_trace(go.Box(y=sodium_high["nutrition_score"], name="Sodium Élevé", marker_color="#FF9500"))
    fig_box.add_trace(go.Box(y=sodium_low["nutrition_score"], name="Sodium Faible", marker_color="#85BB2F"))

    fig_box.update_layout(
        title="Distribution des Scores: Sucres vs Sodium (Élevé vs Faible)",
        yaxis_title="Score Nutritionnel",
        template="plotly_white",
        height=450,
    )

    # 3. Bar chart: Comparison of effects
    fig_bar = go.Figure()

    categories = ["Sucres Élevés", "Sucres Faibles", "Sodium Élevé", "Sodium Faible"]
    scores = [
        comparison["high_sugar_avg_score"],
        comparison["low_sugar_avg_score"],
        comparison["high_sodium_avg_score"],
        comparison["low_sodium_avg_score"],
    ]
    colors = ["#E63946", "#238B45", "#FF9500", "#85BB2F"]

    fig_bar.add_trace(
        go.Bar(x=categories, y=scores, marker_color=colors, text=[f"{s:.1f}" for s in scores], textposition="auto")
    )

    fig_bar.update_layout(
        title="Score Nutritionnel Moyen: Comparaison Sucres vs Sodium",
        yaxis_title="Score Moyen",
        template="plotly_white",
        height=400,
    )

    return fig_scatter, fig_box, fig_bar


def create_nutrient_impact_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create bar chart showing correlation between nutrient excess (vs recommended amounts)
    and nutrition score. Shows which nutrients have the most negative impact when in excess.

    Args:
        df: Recipe dataframe with precomputed nutrient columns

    Returns:
        Plotly figure
    """
    logger.info(f"Creating nutrient impact chart for {len(df)} recipes")

    # Use precomputed nutrient columns directly
    nutrition_data = df[
        [
            "total_fat_pdv",
            "saturated_fat_pdv",
            "sugar_pdv",
            "sodium_pdv",
            "carbs_pdv",
            "protein_pdv",
            "nutrition_score",
        ]
    ].copy()

    logger.debug(f"Parsed nutrition data: {len(nutrition_data)} rows")

    # Calculate excess (amount over 100% DV, or 0 if under)
    # For protein, we want high values (positive correlation with health)
    # For others, we want low values (negative correlation with health)
    excess_data = pd.DataFrame(
        {
            "nutrition_score": nutrition_data["nutrition_score"],
            "Excès Graisses Totales": np.maximum(nutrition_data["total_fat_pdv"] - 100, 0),
            "Excès Graisses Saturées": np.maximum(nutrition_data["saturated_fat_pdv"] - 100, 0),
            "Excès Sucres": np.maximum(nutrition_data["sugar_pdv"] - 100, 0),
            "Excès Sodium": np.maximum(nutrition_data["sodium_pdv"] - 100, 0),
            "Excès Glucides": np.maximum(nutrition_data["carbs_pdv"] - 100, 0),
            "Protéines (% VQ)": nutrition_data["protein_pdv"],
        }
    )

    # Calculate correlations with nutrition score
    correlations = []
    for col in excess_data.columns:
        if col != "nutrition_score":
            clean_data = excess_data[[col, "nutrition_score"]].dropna()
            if len(clean_data) > 10:
                corr, p_val = spearmanr(clean_data[col], clean_data["nutrition_score"])
                correlations.append({"Nutriment": col, "Corrélation": corr, "P_Value": p_val})

    corr_df = pd.DataFrame(correlations)
    corr_df = corr_df.sort_values("Corrélation")

    # Create bar chart
    colors = ["#E63946" if c < 0 else "#238B45" for c in corr_df["Corrélation"]]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            y=corr_df["Nutriment"],
            x=corr_df["Corrélation"],
            orientation="h",
            marker_color=colors,
            text=[f"{c:.3f}" for c in corr_df["Corrélation"]],
            textposition="auto",
            hovertemplate="<b>%{y}</b><br>Corrélation: %{x:.3f}<extra></extra>",
        )
    )

    fig.update_layout(
        title="Impact des Nutriments sur le Score Nutritionnel<br><sub>Corrélation de Spearman entre l'excès de nutriments et le score</sub>",
        xaxis_title="Corrélation avec Score Nutritionnel",
        yaxis_title="",
        template="plotly_white",
        height=400,
        showlegend=False,
        xaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor="black"),
    )

    fig.add_annotation(
        text="← Impact négatif | Impact positif →",
        xref="paper",
        yref="paper",
        x=0.5,
        y=-0.15,
        showarrow=False,
        font=dict(size=10, color="gray"),
    )

    return fig
