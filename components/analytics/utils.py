"""
Utility functions for analytics modules.
"""

import pandas as pd
import numpy as np


def filter_outliers_iqr(df: pd.DataFrame, columns: list, multiplier: float = 1.5) -> pd.DataFrame:
    """
    Filter outliers using IQR method.
    
    Args:
        df: DataFrame to filter
        columns: List of column names to apply filtering
        multiplier: IQR multiplier (default 1.5 for moderate filtering)
    
    Returns:
        Filtered DataFrame
    """
    df_filtered = df.copy()
    
    for col in columns:
        if col not in df_filtered.columns:
            continue
        
        Q1 = df_filtered[col].quantile(0.25)
        Q3 = df_filtered[col].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - multiplier * IQR
        upper_bound = Q3 + multiplier * IQR
        
        df_filtered = df_filtered[
            (df_filtered[col] >= lower_bound) & 
            (df_filtered[col] <= upper_bound)
        ]
    
    return df_filtered


def filter_outliers_percentile(df: pd.DataFrame, columns: list, 
                                lower_pct: float = 0.01, 
                                upper_pct: float = 0.99) -> pd.DataFrame:
    """
    Filter outliers using percentile method.
    
    Args:
        df: DataFrame to filter
        columns: List of column names to apply filtering
        lower_pct: Lower percentile (default 1st percentile)
        upper_pct: Upper percentile (default 99th percentile)
    
    Returns:
        Filtered DataFrame
    """
    df_filtered = df.copy()
    
    for col in columns:
        if col not in df_filtered.columns:
            continue
        
        lower_bound = df_filtered[col].quantile(lower_pct)
        upper_bound = df_filtered[col].quantile(upper_pct)
        
        df_filtered = df_filtered[
            (df_filtered[col] >= lower_bound) & 
            (df_filtered[col] <= upper_bound)
        ]
    
    return df_filtered


def sample_large_dataset(df: pd.DataFrame, max_size: int = 5000, 
                         random_state: int = 42) -> pd.DataFrame:
    """
    Sample dataset if it exceeds max_size for performance.
    
    Args:
        df: DataFrame to sample
        max_size: Maximum number of rows to keep
        random_state: Random seed for reproducibility
    
    Returns:
        Sampled DataFrame (or original if smaller than max_size)
    """
    if len(df) > max_size:
        return df.sample(n=max_size, random_state=random_state)
    return df
