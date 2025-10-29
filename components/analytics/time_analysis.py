"""
Section 2: Time vs Health Analysis
Analyzes relationship between preparation time and nutrition score.
"""

import logging
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import spearmanr, pearsonr
import numpy as np

logger = logging.getLogger(__name__)


def get_time_categories(df: pd.DataFrame) -> pd.DataFrame:
    """
    Categorize recipes by preparation time.
    
    Args:
        df: Recipe dataframe with minutes column
    
    Returns:
        DataFrame with time_category column added
    """
    df = df.copy()
    
    def categorize_time(minutes):
        if pd.isna(minutes):
            return 'Unknown'
        if minutes <= 15:
            return 'Rapide (≤15 min)'
        elif minutes <= 30:
            return 'Moyen (15-30 min)'
        elif minutes <= 60:
            return 'Long (30-60 min)'
        else:
            return 'Très Long (>60 min)'
    
    df['time_category'] = df['minutes'].apply(categorize_time)
    return df


def analyze_time_vs_score(df: pd.DataFrame) -> dict:
    """
    Analyze correlation between time and nutrition score.
    
    Args:
        df: Recipe dataframe
    
    Returns:
        Dictionary with correlation statistics
    """
    logger.info(f"Analyzing time vs score correlation for {len(df)} recipes")
    
    # Clean data
    clean_df = df[['minutes', 'nutrition_score']].dropna()
    clean_df = clean_df[
        (clean_df['minutes'] > 0) & 
        (clean_df['minutes'] < 500)  # Remove extreme outliers
    ]
    
    logger.info(f"Cleaned data: {len(clean_df)} recipes (removed {len(df) - len(clean_df)} outliers/NaN)")
    
    if len(clean_df) < 10:
        logger.warning(f"Insufficient data for correlation analysis: {len(clean_df)} samples")
        return {}
    
    # Correlation tests
    pearson_r, pearson_p = pearsonr(clean_df['minutes'], clean_df['nutrition_score'])
    spearman_r, spearman_p = spearmanr(clean_df['minutes'], clean_df['nutrition_score'])
    
    logger.info(f"Correlation results - Pearson: r={pearson_r:.3f} (p={pearson_p:.3e}), Spearman: ρ={spearman_r:.3f} (p={spearman_p:.3e})")
    
    return {
        'pearson_r': pearson_r,
        'pearson_p': pearson_p,
        'spearman_r': spearman_r,
        'spearman_p': spearman_p,
        'n_samples': len(clean_df)
    }


def create_time_scatter(df: pd.DataFrame) -> go.Figure:
    """
    Create scatter plot of time vs nutrition score with trendline.
    
    Args:
        df: Recipe dataframe
    
    Returns:
        Plotly figure
    """
    # Clean data
    plot_df = df[['minutes', 'nutrition_score', 'nutrition_grade']].dropna()
    plot_df = plot_df[
        (plot_df['minutes'] > 0) & 
        (plot_df['minutes'] < 300)  # Limit to 5 hours for better viz
    ]
    
    # Sample if too many points (for performance)
    if len(plot_df) > 5000:
        plot_df = plot_df.sample(n=5000, random_state=42)
    
    # Get correlation
    stats = analyze_time_vs_score(df)
    
    grade_colors = {
        'A': '#238B45',
        'B': '#85BB2F',
        'C': '#FECC00',
        'D': '#FF9500',
        'E': '#E63946'
    }
    
    fig = px.scatter(
        plot_df,
        x='minutes',
        y='nutrition_score',
        color='nutrition_grade',
        color_discrete_map=grade_colors,
        opacity=0.5,
        title=f"Temps de Préparation vs Score Nutritionnel<br><sub>Corrélation Spearman: ρ={stats.get('spearman_r', 0):.3f} (p={stats.get('spearman_p', 1):.3e})</sub>",
        labels={'minutes': 'Temps de Préparation (minutes)', 'nutrition_score': 'Score Nutritionnel', 'nutrition_grade': 'Grade'}
    )
    
    # Add trendline
    from numpy.polynomial import Polynomial
    x = plot_df['minutes'].values
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


def create_grade_by_time_category(df: pd.DataFrame) -> go.Figure:
    """
    Create visualization of average grade per time category.
    
    Args:
        df: Recipe dataframe
    
    Returns:
        Plotly figure
    """
    df_with_cat = get_time_categories(df)
    
    # Calculate average score and grade distribution per category
    category_order = ['Rapide (≤15 min)', 'Moyen (15-30 min)', 'Long (30-60 min)', 'Très Long (>60 min)']
    
    stats_by_category = []
    for category in category_order:
        cat_data = df_with_cat[df_with_cat['time_category'] == category]
        if len(cat_data) > 0:
            stats_by_category.append({
                'Catégorie': category,
                'Score Moyen': cat_data['nutrition_score'].mean(),
                'Score Médian': cat_data['nutrition_score'].median(),
                'Std Dev': cat_data['nutrition_score'].std(),
                'Nombre': len(cat_data),
                'Grade Moyen': cat_data['nutrition_score'].mean()  # For coloring
            })
    
    stats_df = pd.DataFrame(stats_by_category)
    
    # Create grouped bar chart
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
        title="Score Nutritionnel par Catégorie de Temps",
        xaxis_title="Catégorie de Temps",
        yaxis_title="Score Nutritionnel",
        template="plotly_white",
        height=450,
        barmode='group',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig


def create_time_category_distribution(df: pd.DataFrame) -> go.Figure:
    """
    Create distribution of grades within each time category.
    
    Args:
        df: Recipe dataframe
    
    Returns:
        Plotly figure
    """
    df_with_cat = get_time_categories(df)
    
    category_order = ['Rapide (≤15 min)', 'Moyen (15-30 min)', 'Long (30-60 min)', 'Très Long (>60 min)']
    grade_colors = {
        'A': '#238B45',
        'B': '#85BB2F',
        'C': '#FECC00',
        'D': '#FF9500',
        'E': '#E63946'
    }
    
    fig = go.Figure()
    
    for grade in ['A', 'B', 'C', 'D', 'E']:
        grade_counts = []
        for category in category_order:
            cat_data = df_with_cat[df_with_cat['time_category'] == category]
            count = len(cat_data[cat_data['nutrition_grade'] == grade])
            percentage = (count / len(cat_data) * 100) if len(cat_data) > 0 else 0
            grade_counts.append(percentage)
        
        fig.add_trace(go.Bar(
            name=f'Grade {grade}',
            x=category_order,
            y=grade_counts,
            marker_color=grade_colors[grade],
            text=[f'{p:.1f}%' for p in grade_counts],
            textposition='inside',
        ))
    
    fig.update_layout(
        title="Distribution des Grades par Catégorie de Temps (%)",
        xaxis_title="Catégorie de Temps",
        yaxis_title="Pourcentage de Recettes",
        template="plotly_white",
        height=450,
        barmode='stack',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig
