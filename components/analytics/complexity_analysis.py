"""
Section 4: Complexity vs Healthiness Analysis
Analyzes relationship between recipe complexity and nutrition scores.
"""

import logging
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from scipy.stats import spearmanr

logger = logging.getLogger(__name__)


def calculate_complexity_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate complexity index combining multiple factors.
    
    Args:
        df: Recipe dataframe with n_steps, n_ingredients, minutes columns
    
    Returns:
        DataFrame with complexity metrics added
    """
    logger.info(f"Calculating complexity index for {len(df)} recipes")
    
    df = df.copy()
    
    # Normalize each component to 0-1 scale
    if 'n_steps' in df.columns:
        df['steps_norm'] = (df['n_steps'] - df['n_steps'].min()) / (df['n_steps'].max() - df['n_steps'].min())
        logger.debug(f"Steps range: {df['n_steps'].min()}-{df['n_steps'].max()}")
    else:
        df['steps_norm'] = 0
        logger.warning("Column 'n_steps' not found")
    
    if 'n_ingredients' in df.columns:
        df['ingredients_norm'] = (df['n_ingredients'] - df['n_ingredients'].min()) / (df['n_ingredients'].max() - df['n_ingredients'].min())
        logger.debug(f"Ingredients range: {df['n_ingredients'].min()}-{df['n_ingredients'].max()}")
    else:
        df['ingredients_norm'] = 0
        logger.warning("Column 'n_ingredients' not found")
    
    if 'minutes' in df.columns:
        # Cap at 120 minutes for normalization
        df['minutes_capped'] = df['minutes'].clip(upper=120)
        df['time_norm'] = (df['minutes_capped'] - df['minutes_capped'].min()) / (df['minutes_capped'].max() - df['minutes_capped'].min())
        logger.debug(f"Minutes range: {df['minutes'].min()}-{df['minutes'].max()}")
    else:
        df['time_norm'] = 0
        logger.warning("Column 'minutes' not found")
    
    # Composite complexity index (weighted average)
    df['complexity_index'] = (
        0.4 * df['steps_norm'] +
        0.4 * df['ingredients_norm'] +
        0.2 * df['time_norm']
    ) * 100  # Scale to 0-100
    
    logger.info(f"Complexity index calculated - range: {df['complexity_index'].min():.1f}-{df['complexity_index'].max():.1f}")
    
    # Categorize complexity
    def categorize_complexity(complexity):
        if pd.isna(complexity):
            return 'Unknown'
        if complexity <= 33:
            return 'Simple'
        elif complexity <= 66:
            return 'Moyen'
        else:
            return 'Complexe'
    
    df['complexity_category'] = df['complexity_index'].apply(categorize_complexity)
    
    return df


def analyze_complexity_vs_health(df: pd.DataFrame) -> dict:
    """
    Analyze correlations between complexity metrics and health scores.
    
    Args:
        df: Recipe dataframe
    
    Returns:
        Dictionary with correlation statistics
    """
    df_complex = calculate_complexity_index(df)
    
    # Clean data
    analysis_cols = ['n_steps', 'n_ingredients', 'minutes', 'complexity_index', 'nutrition_score']
    clean_df = df_complex[analysis_cols].dropna()
    
    if len(clean_df) < 10:
        return {}
    
    # Calculate correlations
    correlations = {}
    for col in ['n_steps', 'n_ingredients', 'minutes', 'complexity_index']:
        corr, p_val = spearmanr(clean_df[col], clean_df['nutrition_score'])
        correlations[col] = {'correlation': corr, 'p_value': p_val}
    
    # Average scores by complexity category
    category_stats = df_complex.groupby('complexity_category')['nutrition_score'].agg(['mean', 'median', 'std', 'count'])
    
    return {
        'correlations': correlations,
        'category_stats': category_stats,
        'n_samples': len(clean_df)
    }


def create_complexity_scatter(df: pd.DataFrame) -> go.Figure:
    """
    Create scatter plot of complexity index vs nutrition score.
    
    Args:
        df: Recipe dataframe
    
    Returns:
        Plotly figure
    """
    df_complex = calculate_complexity_index(df)
    
    # Clean and sample data
    plot_df = df_complex[['complexity_index', 'nutrition_score', 'nutrition_grade', 'complexity_category']].dropna()
    if len(plot_df) > 5000:
        plot_df = plot_df.sample(n=5000, random_state=42)
    
    # Calculate correlation
    corr, p_val = spearmanr(plot_df['complexity_index'], plot_df['nutrition_score'])
    
    grade_colors = {
        'A': '#238B45',
        'B': '#85BB2F',
        'C': '#FECC00',
        'D': '#FF9500',
        'E': '#E63946'
    }
    
    fig = px.scatter(
        plot_df,
        x='complexity_index',
        y='nutrition_score',
        color='nutrition_grade',
        color_discrete_map=grade_colors,
        opacity=0.5,
        title=f"Indice de Complexité vs Score Nutritionnel<br><sub>Corrélation: ρ={corr:.3f} (p={p_val:.3e})</sub>",
        labels={
            'complexity_index': 'Indice de Complexité (0-100)',
            'nutrition_score': 'Score Nutritionnel',
            'nutrition_grade': 'Grade'
        }
    )
    
    # Add trendline
    from numpy.polynomial import Polynomial
    x = plot_df['complexity_index'].values
    y = plot_df['nutrition_score'].values
    p = Polynomial.fit(x, y, deg=1)
    x_trend = np.linspace(x.min(), x.max(), 100)
    y_trend = p(x_trend)
    
    fig.add_trace(go.Scatter(
        x=x_trend,
        y=y_trend,
        mode='lines',
        name='Tendance',
        line=dict(color='red', width=2, dash='dash')
    ))
    
    fig.update_layout(
        template="plotly_white",
        height=500,
    )
    
    return fig


def create_complexity_heatmap(df: pd.DataFrame) -> go.Figure:
    """
    Create heatmap showing avg score by n_steps x n_ingredients.
    
    Args:
        df: Recipe dataframe
    
    Returns:
        Plotly heatmap figure
    """
    # Bin steps and ingredients
    df_binned = df.copy()
    df_binned = df_binned[
        (df_binned['n_steps'] <= 30) &
        (df_binned['n_ingredients'] <= 20)
    ].dropna(subset=['n_steps', 'n_ingredients', 'nutrition_score'])
    
    # Create bins
    df_binned['steps_bin'] = pd.cut(df_binned['n_steps'], bins=[0, 5, 10, 15, 20, 30], labels=['1-5', '6-10', '11-15', '16-20', '21-30'])
    df_binned['ingredients_bin'] = pd.cut(df_binned['n_ingredients'], bins=[0, 5, 10, 15, 20], labels=['1-5', '6-10', '11-15', '16-20'])
    
    # Calculate average score for each bin combination
    heatmap_data = df_binned.groupby(['steps_bin', 'ingredients_bin'])['nutrition_score'].mean().unstack(fill_value=np.nan)
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale='RdYlGn',
        text=np.round(heatmap_data.values, 1),
        texttemplate='%{text}',
        textfont={"size": 10},
        colorbar=dict(title="Score<br>Moyen")
    ))
    
    fig.update_layout(
        title="Score Nutritionnel Moyen par Nombre d'Étapes et d'Ingrédients",
        xaxis_title="Nombre d'Ingrédients",
        yaxis_title="Nombre d'Étapes",
        template="plotly_white",
        height=500,
    )
    
    return fig


def create_complexity_category_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create chart showing score distribution by complexity category.
    
    Args:
        df: Recipe dataframe
    
    Returns:
        Plotly figure
    """
    df_complex = calculate_complexity_index(df)
    
    # Calculate stats per category
    categories = ['Simple', 'Moyen', 'Complexe']
    stats = []
    
    for cat in categories:
        cat_data = df_complex[df_complex['complexity_category'] == cat]['nutrition_score'].dropna()
        if len(cat_data) > 0:
            stats.append({
                'Catégorie': cat,
                'Score Moyen': cat_data.mean(),
                'Score Médian': cat_data.median(),
                'Std Dev': cat_data.std(),
                'Nombre': len(cat_data)
            })
    
    stats_df = pd.DataFrame(stats)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Score Moyen',
        x=stats_df['Catégorie'],
        y=stats_df['Score Moyen'],
        text=stats_df['Score Moyen'].round(1),
        textposition='auto',
        marker_color='#667eea',
        error_y=dict(type='data', array=stats_df['Std Dev'], visible=True)
    ))
    
    fig.add_trace(go.Bar(
        name='Score Médian',
        x=stats_df['Catégorie'],
        y=stats_df['Score Médian'],
        text=stats_df['Score Médian'].round(1),
        textposition='auto',
        marker_color='#764ba2'
    ))
    
    fig.update_layout(
        title="Score Nutritionnel par Catégorie de Complexité",
        xaxis_title="Complexité de la Recette",
        yaxis_title="Score Nutritionnel",
        template="plotly_white",
        height=450,
        barmode='group'
    )
    
    return fig


def create_individual_factors_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create chart comparing correlation of each complexity factor.
    
    Args:
        df: Recipe dataframe
    
    Returns:
        Plotly figure
    """
    analysis = analyze_complexity_vs_health(df)
    
    if not analysis:
        fig = go.Figure()
        fig.add_annotation(text="Données insuffisantes", showarrow=False)
        return fig
    
    correlations = analysis['correlations']
    
    factors = ['n_steps', 'n_ingredients', 'minutes', 'complexity_index']
    factor_names = ['Nombre d\'Étapes', 'Nombre d\'Ingrédients', 'Temps (min)', 'Indice de Complexité']
    corr_values = [correlations[f]['correlation'] for f in factors]
    p_values = [correlations[f]['p_value'] for f in factors]
    
    # Determine significance
    colors = ['#238B45' if p < 0.05 else '#7f8c8d' for p in p_values]
    
    fig = go.Figure(data=[
        go.Bar(
            x=factor_names,
            y=corr_values,
            marker_color=colors,
            text=[f'{c:.3f}' for c in corr_values],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title="Corrélation de Chaque Facteur avec le Score Nutritionnel<br><sub>Vert = significatif (p<0.05), Gris = non significatif</sub>",
        xaxis_title="Facteur de Complexité",
        yaxis_title="Corrélation Spearman (ρ)",
        template="plotly_white",
        height=450,
    )
    
    # Add reference line at 0
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    return fig
