# nutrition_scoring.py
"""
Streamlined nutrition scoring module.
Computes normalized nutrition scores (10-98) and letter grades (A-E)
from the Food.com dataset without keeping intermediate columns.
"""

import ast
import logging
from typing import List, Optional, Union

import numpy as np
import pandas as pd

# Set up logger for this module
logger = logging.getLogger(__name__)


def parse_nutrition_entry(value: Union[str, list, tuple, None]) -> Optional[List[float]]:
    if pd.isna(value):
        return None
    if isinstance(value, (list, tuple)) and len(value) == 7:
        if any(pd.isna(x) for x in value):
            return None
        return list(value)
    if isinstance(value, str):
        try:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, (list, tuple)) and len(parsed) == 7:
                if any(pd.isna(x) for x in parsed):
                    return None
                return list(parsed)
        except Exception:
            return None
    return None


def compute_raw_score(nutrition_list: List[float]) -> Optional[float]:
    if nutrition_list is None:
        return None
    try:
        calories, total_fat, sugar, sodium, protein, saturated_fat, carbohydrates = nutrition_list
        score = (
            (protein * 2)
            - (calories * 0.02)
            - (total_fat * 0.5)
            - (sugar * 0.3)
            - (sodium * 0.02)
            - (saturated_fat * 0.5)
        )
        return score
    except Exception:
        return None


def normalize_scores(raw_scores: pd.Series, min_val: float = 10, max_val: float = 98) -> pd.Series:
    logger.info("Normalizing nutrition scores")
    valid_scores = raw_scores.dropna()
    p1, p99 = np.percentile(valid_scores, [1, 99])

    logger.info(f"Score percentiles - p1: {p1:.2f}, p99: {p99:.2f}")

    def scale(x):
        if pd.isna(x):
            return np.nan
        x_clamped = max(min(x, p99), p1)
        scaled = min_val + (x_clamped - p1) * ((max_val - min_val) / (p99 - p1))
        return round(scaled, 2)

    normalized = raw_scores.apply(scale)
    logger.info(f"Normalized {len(valid_scores)} scores")
    return normalized


def assign_grade(score: float) -> Optional[str]:
    if pd.isna(score):
        return None
    elif score >= 80:
        return "A"
    elif score >= 60:
        return "B"
    elif score >= 40:
        return "C"
    elif score >= 20:
        return "D"
    else:
        return "E"


def score_nutrition(df: pd.DataFrame, nutrition_col: str = "nutrition") -> pd.DataFrame:
    """
    Compute normalized nutrition scores and letter grades for the DataFrame.

    Adds only two columns:
        - nutrition_score
        - nutrition_grade
    """
    logger.info("Starting nutrition scoring")
    df = df.copy()

    # parse and compute final scores internally
    logger.info(f"Processing {len(df)} recipes")
    raw_scores = df[nutrition_col].apply(lambda x: compute_raw_score(parse_nutrition_entry(x)))

    valid_count = raw_scores.notna().sum()
    logger.info(f"Computed final scores for {valid_count}/{len(df)} recipes")

    df["nutrition_score"] = normalize_scores(raw_scores)
    df["nutrition_grade"] = df["nutrition_score"].apply(assign_grade)

    # Log grade distribution
    grade_counts = df["nutrition_grade"].value_counts().sort_index()
    logger.info(f"Grade distribution: {grade_counts.to_dict()}")
    logger.info("Nutrition scoring completed")

    return df
