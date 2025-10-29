"""
Section 3: Ingredient Health Index
Analyzes which ingredients are associated with healthy/unhealthy recipes.
"""

import logging
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import ast
from collections import Counter, defaultdict
import numpy as np
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
    except:
        return []


def calculate_ingredient_health_index(df: pd.DataFrame, min_frequency: int = 100) -> pd.DataFrame:
    """
    Calculate health index for each ingredient based on average recipe scores.
    
    Args:
        df: Recipe dataframe with ingredients and nutrition_score columns
        min_frequency: Minimum number of occurrences to include ingredient
    
    Returns:
        DataFrame with ingredient statistics
    """
    logger.info(f"Calculating ingredient health index for {len(df)} recipes (min_frequency={min_frequency})")
    
    ingredient_scores = defaultdict(list)
    ingredient_grades = defaultdict(list)
    
    # Parse all ingredients and collect scores
    for _, row in df.iterrows():
        if pd.notna(row['nutrition_score']):
            ingredients = parse_ingredients(row['ingredients'])
            for ingredient in ingredients:
                ingredient = ingredient.strip().lower()
                if ingredient:
                    ingredient_scores[ingredient].append(row['nutrition_score'])
                    ingredient_grades[ingredient].append(row['nutrition_grade'])
    
    logger.info(f"Found {len(ingredient_scores)} unique ingredients")
    
    # Calculate statistics
    ingredient_stats = []
    for ingredient, scores in ingredient_scores.items():
        if len(scores) >= min_frequency:
            scores_array = np.array(scores)
            ingredient_stats.append({
                'ingredient': ingredient,
                'avg_score': scores_array.mean(),
                'median_score': np.median(scores_array),
                'std_score': scores_array.std(),
                'frequency': len(scores),
                'consistency': 1 / (scores_array.std() + 0.1),  # Lower std = more consistent
            })
    
    stats_df = pd.DataFrame(ingredient_stats)
    stats_df = stats_df.sort_values('avg_score', ascending=False)
    
    return stats_df


def compare_sugar_vs_salt(df: pd.DataFrame) -> dict:
    """
    Compare the effect of sugar vs salt (sodium) on nutrition scores.
    
    Args:
        df: Recipe dataframe
    
    Returns:
        Dictionary with comparison statistics
    """
    # Extract sugar and sodium from nutrition array
    import ast
    nutrition_lists = []
    for val in df['nutrition']:
        if isinstance(val, str):
            try:
                nutrition_lists.append(ast.literal_eval(val))
            except:
                nutrition_lists.append([np.nan] * 7)
        elif isinstance(val, (list, tuple)):
            nutrition_lists.append(list(val))
        else:
            nutrition_lists.append([np.nan] * 7)
    
    nutrition_data = pd.DataFrame(
        nutrition_lists,
        columns=['calories', 'total_fat_pdv', 'sugar_pdv', 'sodium_pdv', 
                 'protein_pdv', 'saturated_fat_pdv', 'carbs_pdv']
    )
    nutrition_data['nutrition_score'] = df['nutrition_score'].values
    
    # Clean data
    clean_data = nutrition_data[['sugar_pdv', 'sodium_pdv', 'nutrition_score']].dropna()
    
    # Correlation analysis
    sugar_corr, sugar_p = spearmanr(clean_data['sugar_pdv'], clean_data['nutrition_score'])
    sodium_corr, sodium_p = spearmanr(clean_data['sodium_pdv'], clean_data['nutrition_score'])
    
    # Categorize into high/low
    sugar_median = clean_data['sugar_pdv'].median()
    sodium_median = clean_data['sodium_pdv'].median()
    
    high_sugar = clean_data[clean_data['sugar_pdv'] > sugar_median]
    low_sugar = clean_data[clean_data['sugar_pdv'] <= sugar_median]
    high_sodium = clean_data[clean_data['sodium_pdv'] > sodium_median]
    low_sodium = clean_data[clean_data['sodium_pdv'] <= sodium_median]
    
    return {
        'sugar_correlation': sugar_corr,
        'sugar_p_value': sugar_p,
        'sodium_correlation': sodium_corr,
        'sodium_p_value': sodium_p,
        'high_sugar_avg_score': high_sugar['nutrition_score'].mean(),
        'low_sugar_avg_score': low_sugar['nutrition_score'].mean(),
        'high_sodium_avg_score': high_sodium['nutrition_score'].mean(),
        'low_sodium_avg_score': low_sodium['nutrition_score'].mean(),
        'data': clean_data,
        'sugar_median': sugar_median,
        'sodium_median': sodium_median,
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
    top_ingredients = ingredient_stats.nlargest(top_n, 'frequency')
    
    fig = px.scatter(
        top_ingredients,
        x='frequency',
        y='avg_score',
        size='consistency',
        hover_data=['ingredient'],
        text='ingredient',
        title=f"Top {top_n} Ingrédients: Fréquence vs Score Nutritionnel Moyen",
        labels={
            'frequency': 'Fréquence (nombre de recettes)',
            'avg_score': 'Score Nutritionnel Moyen',
            'consistency': 'Consistance'
        }
    )
    
    fig.update_traces(textposition='top center', textfont_size=8)
    
    fig.update_layout(
        template="plotly_white",
        height=600,
        showlegend=False
    )
    
    return fig


def create_top_ingredients_table(df: pd.DataFrame, top_n: int = 20, sort_by: str = 'healthiest') -> pd.DataFrame:
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
    
    if sort_by == 'healthiest':
        top = ingredient_stats.nlargest(top_n, 'avg_score')
    else:
        top = ingredient_stats.nsmallest(top_n, 'avg_score')
    
    # Format for display
    display_df = top[['ingredient', 'avg_score', 'median_score', 'frequency']].copy()
    display_df.columns = ['Ingrédient', 'Score Moyen', 'Score Médian', 'Fréquence']
    display_df['Score Moyen'] = display_df['Score Moyen'].round(1)
    display_df['Score Médian'] = display_df['Score Médian'].round(1)
    display_df = display_df.reset_index(drop=True)
    
    return display_df


def create_sugar_salt_comparison(df: pd.DataFrame) -> tuple:
    """
    Create visualizations comparing sugar vs salt effects.
    
    Args:
        df: Recipe dataframe
    
    Returns:
        Tuple of (scatter_fig, box_fig, bar_fig)
    """
    comparison = compare_sugar_vs_salt(df)
    data = comparison['data']
    
    # 1. Scatter plot: Sugar vs Sodium colored by score
    fig_scatter = px.scatter(
        data.sample(n=min(5000, len(data)), random_state=42),
        x='sugar_pdv',
        y='sodium_pdv',
        color='nutrition_score',
        color_continuous_scale='RdYlGn',
        title=f"Sucres vs Sodium (%DV) - Coloré par Score<br><sub>Corrélation Sucres: ρ={comparison['sugar_correlation']:.3f}, Sodium: ρ={comparison['sodium_correlation']:.3f}</sub>",
        labels={
            'sugar_pdv': 'Sucres (%DV)',
            'sodium_pdv': 'Sodium (%DV)',
            'nutrition_score': 'Score'
        },
        opacity=0.5
    )
    fig_scatter.update_layout(template="plotly_white", height=500)
    
    # 2. Box plots: Score distribution for high/low sugar and sodium
    fig_box = go.Figure()
    
    sugar_high = data[data['sugar_pdv'] > comparison['sugar_median']]
    sugar_low = data[data['sugar_pdv'] <= comparison['sugar_median']]
    sodium_high = data[data['sodium_pdv'] > comparison['sodium_median']]
    sodium_low = data[data['sodium_pdv'] <= comparison['sodium_median']]
    
    fig_box.add_trace(go.Box(y=sugar_high['nutrition_score'], name='Sucres Élevés', marker_color='#E63946'))
    fig_box.add_trace(go.Box(y=sugar_low['nutrition_score'], name='Sucres Faibles', marker_color='#238B45'))
    fig_box.add_trace(go.Box(y=sodium_high['nutrition_score'], name='Sodium Élevé', marker_color='#FF9500'))
    fig_box.add_trace(go.Box(y=sodium_low['nutrition_score'], name='Sodium Faible', marker_color='#85BB2F'))
    
    fig_box.update_layout(
        title="Distribution des Scores: Sucres vs Sodium (Élevé vs Faible)",
        yaxis_title="Score Nutritionnel",
        template="plotly_white",
        height=450
    )
    
    # 3. Bar chart: Comparison of effects
    fig_bar = go.Figure()
    
    categories = ['Sucres Élevés', 'Sucres Faibles', 'Sodium Élevé', 'Sodium Faible']
    scores = [
        comparison['high_sugar_avg_score'],
        comparison['low_sugar_avg_score'],
        comparison['high_sodium_avg_score'],
        comparison['low_sodium_avg_score']
    ]
    colors = ['#E63946', '#238B45', '#FF9500', '#85BB2F']
    
    fig_bar.add_trace(go.Bar(
        x=categories,
        y=scores,
        marker_color=colors,
        text=[f'{s:.1f}' for s in scores],
        textposition='auto'
    ))
    
    fig_bar.update_layout(
        title="Score Nutritionnel Moyen: Comparaison Sucres vs Sodium",
        yaxis_title="Score Moyen",
        template="plotly_white",
        height=400
    )
    
    return fig_scatter, fig_box, fig_bar


def create_nutrient_impact_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create bar chart showing correlation between nutrient excess (vs recommended amounts)
    and nutrition score. Shows which nutrients have the most negative impact when in excess.
    
    Args:
        df: Recipe dataframe
    
    Returns:
        Plotly figure
    """
    logger.info(f"Creating nutrient impact chart for {len(df)} recipes")
    
    # Extract nutrients safely
    nutrition_lists = []
    for val in df['nutrition']:
        if isinstance(val, str):
            try:
                nutrition_lists.append(ast.literal_eval(val))
            except:
                nutrition_lists.append([np.nan] * 7)
        elif isinstance(val, (list, tuple)):
            nutrition_lists.append(list(val))
        else:
            nutrition_lists.append([np.nan] * 7)
    
    nutrition_data = pd.DataFrame(
        nutrition_lists,
        columns=['calories', 'total_fat_pdv', 'sugar_pdv', 'sodium_pdv', 
                 'protein_pdv', 'saturated_fat_pdv', 'carbs_pdv']
    )
    
    logger.debug(f"Parsed nutrition data: {len(nutrition_data)} rows")
    
    # Calculate excess (amount over 100% DV, or 0 if under)
    # For protein, we want high values (positive correlation with health)
    # For others, we want low values (negative correlation with health)
    excess_data = pd.DataFrame({
        'nutrition_score': df['nutrition_score'].values,
        'Excès Graisses Totales': np.maximum(nutrition_data['total_fat_pdv'] - 100, 0),
        'Excès Graisses Saturées': np.maximum(nutrition_data['saturated_fat_pdv'] - 100, 0),
        'Excès Sucres': np.maximum(nutrition_data['sugar_pdv'] - 100, 0),
        'Excès Sodium': np.maximum(nutrition_data['sodium_pdv'] - 100, 0),
        'Excès Glucides': np.maximum(nutrition_data['carbs_pdv'] - 100, 0),
        'Protéines (% VQ)': nutrition_data['protein_pdv']
    })
    
    # Calculate correlations with nutrition score
    correlations = []
    for col in excess_data.columns:
        if col != 'nutrition_score':
            clean_data = excess_data[[col, 'nutrition_score']].dropna()
            if len(clean_data) > 10:
                corr, p_val = spearmanr(clean_data[col], clean_data['nutrition_score'])
                correlations.append({
                    'Nutriment': col,
                    'Corrélation': corr,
                    'P_Value': p_val
                })
    
    corr_df = pd.DataFrame(correlations)
    corr_df = corr_df.sort_values('Corrélation')
    
    # Create bar chart
    colors = ['#E63946' if c < 0 else '#238B45' for c in corr_df['Corrélation']]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=corr_df['Nutriment'],
        x=corr_df['Corrélation'],
        orientation='h',
        marker_color=colors,
        text=[f'{c:.3f}' for c in corr_df['Corrélation']],
        textposition='auto',
        hovertemplate='<b>%{y}</b><br>Corrélation: %{x:.3f}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Impact des Nutriments sur le Score Nutritionnel<br><sub>Corrélation de Spearman entre l'excès de nutriments et le score</sub>",
        xaxis_title="Corrélation avec Score Nutritionnel",
        yaxis_title="",
        template="plotly_white",
        height=400,
        showlegend=False,
        xaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='black')
    )
    
    fig.add_annotation(
        text="← Impact négatif | Impact positif →",
        xref="paper", yref="paper",
        x=0.5, y=-0.15,
        showarrow=False,
        font=dict(size=10, color='gray')
    )
    
    return fig
