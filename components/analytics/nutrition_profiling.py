"""
Section 1: Nutrition Grade Profiling
Analyzes distribution and patterns across nutrition grades A-E.
"""

import logging
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

logger = logging.getLogger(__name__)


def get_grade_distribution(df: pd.DataFrame, vegetarian: bool = None) -> pd.Series:
    """
    Get distribution of nutrition grades with optional vegetarian filter.
    
    Args:
        df: Recipe dataframe with nutrition_grade column
        vegetarian: None (all), True (veg only), False (non-veg only)
    
    Returns:
        Series with grade counts
    """
    filtered_df = df.copy()
    
    if vegetarian is not None:
        if 'vegetarian' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['vegetarian'] == vegetarian]
    
    grade_counts = filtered_df['nutrition_grade'].value_counts().sort_index()
    return grade_counts


def get_nutrient_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Spearman correlation matrix between nutrients.
    Uses %DV values from nutrition array.
    
    Args:
        df: Recipe dataframe with nutrition column
    
    Returns:
        Correlation matrix DataFrame
    """
    logger.info(f"Calculating nutrient correlation matrix for {len(df)} recipes")
    
    # Extract nutrients from nutrition array
    # Format: [calories, total_fat, sugar, sodium, protein, saturated_fat, carbs]
    
    # Parse nutrition data safely
    nutrition_lists = []
    for val in df['nutrition']:
        if isinstance(val, str):
            import ast
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
    
    # Add nutrition score
    nutrition_data['nutrition_score'] = df['nutrition_score'].values
    
    # Drop rows with NaN
    nutrition_data_clean = nutrition_data.dropna()
    logger.info(f"Cleaned data: {len(nutrition_data_clean)} rows (dropped {len(nutrition_data) - len(nutrition_data_clean)} NaN rows)")
    
    # Calculate Spearman correlation (better for non-linear relationships)
    corr_matrix = nutrition_data_clean.corr(method='spearman')
    logger.debug(f"Correlation matrix shape: {corr_matrix.shape}")
    
    return corr_matrix


def get_mean_nutrients_by_grade(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate mean nutrient %DV per nutrition grade.
    
    Args:
        df: Recipe dataframe
    
    Returns:
        DataFrame with mean nutrients by grade
    """
    # Extract nutrients safely
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
    nutrition_data['nutrition_grade'] = df['nutrition_grade'].values
    
    # Group by grade and calculate means
    mean_by_grade = nutrition_data.groupby('nutrition_grade').mean()
    
    return mean_by_grade


def create_grade_histogram(df: pd.DataFrame, vegetarian: bool = None) -> go.Figure:
    """
    Create histogram of nutrition grade distribution.
    
    Args:
        df: Recipe dataframe
        vegetarian: Filter by vegetarian status
    
    Returns:
        Plotly figure
    """
    grade_counts = get_grade_distribution(df, vegetarian)
    total = grade_counts.sum()
    percentages = (grade_counts / total * 100).round(1)
    
    # Grade colors
    colors = {
        'A': '#238B45',
        'B': '#85BB2F',
        'C': '#FECC00',
        'D': '#FF9500',
        'E': '#E63946'
    }
    
    fig = go.Figure(data=[
        go.Bar(
            x=grade_counts.index,
            y=grade_counts.values,
            marker_color=[colors.get(g, '#7f8c8d') for g in grade_counts.index],
            text=[f"{count:,}<br>({pct}%)" for count, pct in zip(grade_counts.values, percentages)],
            textposition='auto',
        )
    ])
    
    title_suffix = ""
    if vegetarian is True:
        title_suffix = " (Végétarien)"
    elif vegetarian is False:
        title_suffix = " (Non-végétarien)"
    
    fig.update_layout(
        title=f"Distribution des Grades Nutritionnels{title_suffix}<br><sub>Total: {total:,} recettes</sub>",
        xaxis_title="Grade",
        yaxis_title="Nombre de Recettes",
        template="plotly_white",
        height=450,
    )
    
    return fig


def create_correlation_heatmap(df: pd.DataFrame) -> go.Figure:
    """
    Create correlation heatmap between nutrients.
    
    Args:
        df: Recipe dataframe
    
    Returns:
        Plotly heatmap figure
    """
    corr_matrix = get_nutrient_correlation_matrix(df)
    
    # Rename columns for display
    display_names = {
        'calories': 'Calories',
        'total_fat_pdv': 'Lipides Total',
        'sugar_pdv': 'Sucres',
        'sodium_pdv': 'Sodium',
        'protein_pdv': 'Protéines',
        'saturated_fat_pdv': 'Graisses Sat.',
        'carbs_pdv': 'Glucides',
        'nutrition_score': 'Score'
    }
    
    corr_matrix_display = corr_matrix.rename(columns=display_names, index=display_names)
    
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix_display.values,
        x=corr_matrix_display.columns,
        y=corr_matrix_display.index,
        colorscale='RdBu_r',
        zmid=0,
        zmin=-1,
        zmax=1,
        text=np.round(corr_matrix_display.values, 2),
        texttemplate='%{text}',
        textfont={"size": 10},
        colorbar=dict(title="Corrélation<br>Spearman")
    ))
    
    fig.update_layout(
        title="Matrice de Corrélation entre Nutriments (Spearman)",
        template="plotly_white",
        height=600,
        xaxis={'side': 'bottom'},
    )
    
    return fig


def create_mean_nutrients_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create bar chart showing mean nutrient %DV per grade.
    
    Args:
        df: Recipe dataframe
    
    Returns:
        Plotly figure
    """
    mean_by_grade = get_mean_nutrients_by_grade(df)
    
    # Select nutrients to display (exclude calories)
    nutrients = [
        ('protein_pdv', 'Protéines'),
        ('total_fat_pdv', 'Lipides'),
        ('saturated_fat_pdv', 'Graisses Sat.'),
        ('sugar_pdv', 'Sucres'),
        ('sodium_pdv', 'Sodium'),
        ('carbs_pdv', 'Glucides'),
    ]
    
    fig = go.Figure()
    
    for nutrient_col, nutrient_name in nutrients:
        fig.add_trace(go.Bar(
            name=nutrient_name,
            x=mean_by_grade.index,
            y=mean_by_grade[nutrient_col],
            text=mean_by_grade[nutrient_col].round(1),
            textposition='auto',
        ))
    
    fig.update_layout(
        title="Moyenne des Nutriments (%DV) par Grade",
        xaxis_title="Grade Nutritionnel",
        yaxis_title="% Valeur Quotidienne Moyenne",
        barmode='group',
        template="plotly_white",
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig


def create_nutrient_boxplots(df: pd.DataFrame, vegetarian: bool = None) -> go.Figure:
    """
    Create box plots showing nutrient distributions by grade.
    
    Args:
        df: Recipe dataframe
        vegetarian: Filter by vegetarian status
    
    Returns:
        Plotly figure with subplots
    """
    filtered_df = df.copy()
    if vegetarian is not None and 'vegetarian' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['vegetarian'] == vegetarian]
    
    # Extract nutrients safely
    import ast
    nutrition_lists = []
    for val in filtered_df['nutrition']:
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
    nutrition_data['nutrition_grade'] = filtered_df['nutrition_grade'].values
    
    # Nutrients to plot
    nutrients = [
        ('protein_pdv', 'Protéines (%DV)'),
        ('total_fat_pdv', 'Lipides (%DV)'),
        ('saturated_fat_pdv', 'Graisses Sat. (%DV)'),
        ('sugar_pdv', 'Sucres (%DV)'),
        ('sodium_pdv', 'Sodium (%DV)'),
        ('carbs_pdv', 'Glucides (%DV)'),
    ]
    
    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=[name for _, name in nutrients],
        vertical_spacing=0.12,
        horizontal_spacing=0.1,
    )
    
    colors = ['#238B45', '#85BB2F', '#FECC00', '#FF9500', '#E63946']
    
    for idx, (nutrient_col, nutrient_name) in enumerate(nutrients):
        row = idx // 3 + 1
        col = idx % 3 + 1
        
        for grade_idx, grade in enumerate(['A', 'B', 'C', 'D', 'E']):
            grade_data = nutrition_data[nutrition_data['nutrition_grade'] == grade][nutrient_col]
            
            fig.add_trace(
                go.Box(
                    y=grade_data,
                    name=grade,
                    marker_color=colors[grade_idx],
                    showlegend=(idx == 0),  # Only show legend for first subplot
                    boxmean='sd'  # Show mean and std dev
                ),
                row=row, col=col
            )
    
    title_suffix = ""
    if vegetarian is True:
        title_suffix = " (Végétarien)"
    elif vegetarian is False:
        title_suffix = " (Non-végétarien)"
    
    fig.update_layout(
        title=f"Distribution des Nutriments par Grade{title_suffix}",
        template="plotly_white",
        height=800,
        showlegend=True,
    )
    
    return fig
