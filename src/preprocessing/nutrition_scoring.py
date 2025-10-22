# nutrition_scoring.py
"""
Streamlined nutrition scoring module.
Computes normalized nutrition scores (10-98) and letter grades (A-E)
from the Food.com dataset without keeping intermediate columns.
"""

import ast
from typing import List, Optional, Union

import numpy as np
import pandas as pd


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
    valid_scores = raw_scores.dropna()
    p1, p99 = np.percentile(valid_scores, [1, 99])

    def scale(x):
        if pd.isna(x):
            return np.nan
        x_clamped = max(min(x, p99), p1)
        scaled = min_val + (x_clamped - p1) * ((max_val - min_val) / (p99 - p1))
        return round(scaled, 2)

    return raw_scores.apply(scale)


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
    df = df.copy()
    # parse and compute raw scores internally
    raw_scores = df[nutrition_col].apply(lambda x: compute_raw_score(parse_nutrition_entry(x)))
    df["nutrition_score"] = normalize_scores(raw_scores)
    df["nutrition_grade"] = df["nutrition_score"].apply(assign_grade)
    return df
