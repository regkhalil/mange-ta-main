"""
Module to extract individual nutrition columns from nutrition array.

This module provides functionality to parse nutrition data from the RAW dataset
and create separate columns for calories, protein, fat, sugar, etc.
"""

import ast
import logging

import pandas as pd

logger = logging.getLogger(__name__)


def extract_nutrition_columns(df: pd.DataFrame, nutrition_col: str = "nutrition") -> pd.DataFrame:
    """
    Extract individual nutrition columns (calories, protein, fat, etc.) from nutrition array.

    The nutrition array in the RAW dataset contains 7 values:
    [calories, total_fat, sugar, sodium, protein, saturated_fat, carbohydrates]

    Args:
        df: DataFrame with nutrition data
        nutrition_col: Name of column containing nutrition array (as string or list)

    Returns:
        DataFrame with added nutrition columns: calories, total_fat, sugar, sodium,
        protein, saturated_fat, carbohydrates

    Example:
        >>> df = pd.read_csv('RAW_recipes.csv')
        >>> df = extract_nutrition_columns(df)
        >>> print(df[['name', 'calories', 'protein', 'total_fat']].head())
    """
    logger.info("Extracting individual nutrition columns from nutrition array")
    df = df.copy()

    def extract_values(nutrition_value):
        """Extract nutrition values from parsed nutrition entry."""
        try:
            # Parse if string
            if isinstance(nutrition_value, str):
                nutrition_list = ast.literal_eval(nutrition_value)
            else:
                nutrition_list = nutrition_value

            # Extract values if valid list
            if isinstance(nutrition_list, (list, tuple)) and len(nutrition_list) >= 7:
                # Check if any value is NaN or if we can't convert to float
                try:
                    values = [float(x) for x in nutrition_list[:7]]
                    # If any value is NaN, return zeros
                    if any(pd.isna(v) for v in values):
                        raise ValueError("Contains NaN values")
                    
                    return pd.Series(
                        {
                            "calories": values[0],
                            "total_fat": values[1],
                            "sugar": values[2],
                            "sodium": values[3],
                            "protein": values[4],
                            "saturated_fat": values[5],
                            "carbohydrates": values[6],
                        }
                    )
                except (ValueError, TypeError):
                    pass  # Fall through to return zeros
        except (ValueError, SyntaxError, TypeError, IndexError) as e:
            logger.debug(f"Failed to parse nutrition value: {e}")

        # Return zeros if parsing fails
        return pd.Series(
            {
                "calories": 0.0,
                "total_fat": 0.0,
                "sugar": 0.0,
                "sodium": 0.0,
                "protein": 0.0,
                "saturated_fat": 0.0,
                "carbohydrates": 0.0,
            }
        )

    # Handle empty DataFrame case
    if len(df) == 0:
        # Create empty nutrition columns for empty DataFrame
        for col in ["calories", "total_fat", "sugar", "sodium", "protein", "saturated_fat", "carbohydrates"]:
            df[col] = pd.Series([], dtype=float)
        logger.info("Empty dataframe processed - created empty nutrition columns")
        return df

    nutrition_df = df[nutrition_col].apply(extract_values)
    df = pd.concat([df, nutrition_df], axis=1)

    # Check if nutrition_df is a DataFrame (not Series for empty data)
    if hasattr(nutrition_df, 'columns'):
        logger.info(f"Extracted nutrition columns: {nutrition_df.columns.tolist()}")
        if len(df) > 0:
            logger.info(
                f"Sample values - Calories mean: {df['calories'].mean():.1f}, Protein mean: {df['protein'].mean():.1f}g"
            )
    else:
        logger.info("Empty dataframe processed - no nutrition columns extracted")

    return df
