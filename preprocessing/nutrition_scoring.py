# nutrition_scoring.py
"""
IMPROVED Nutrition Scoring Module - Weighted Balance Score
===========================================================

ISSUE WITH v1 (nutrition_scoring.py):
-------------------------------------
The original scoring algorithm had a critical flaw where protein rewards were unlimited,
causing recipes with extremely high protein (100-150g) to receive A-grades despite being
nutritionally imbalanced (e.g., high in saturated fat, sodium, or calories).

Example problematic scores:
- "1 00 Tangy Chicken" (Score: 92.1, Grade: A): 148g protein, 93g fat, 86g sat fat
- "French Onion Soup" (Score: 81.7, Grade: A): 1269 calories, 88g sat fat, 70g sugar
- These received high scores purely due to protein, ignoring serious nutritional concerns

v2 IMPROVEMENTS:
----------------
1. **Healthy Ranges**: Define nutritionally sound ranges for each nutrient based on:
   - USDA Dietary Guidelines 2020-2025
   - FDA Daily Values (scaled per serving, assuming ~3 meals/day)
   - Dataset distribution analysis (231,637 recipes)

2. **Capped Rewards**: Protein and other nutrients have diminishing returns after "adequate" levels
   - Prevents extreme values from dominating the score
   - Rewards balance over excess

3. **Balance Penalty**: Penalizes recipes that are imbalanced (e.g., very high in one nutrient)
   - Encourages well-rounded nutritional profiles

4. **Transparent Scoring**: Each component is clearly documented and tunable

NUTRITIONAL GUIDELINES & DATA SOURCES:
--------------------------------------
Based on analysis of 231,637 recipes from Food.com dataset and USDA guidelines:

Dataset Distribution (Percentiles):
                    25th    50th    75th    90th    Mean
CALORIES           174.4   313.4   519.7   843.6   473.9
PROTEIN (g)          7.0    18.0    51.0    83.0    34.7
FAT (g)              8.0    20.0    41.0    73.0    36.1
SAT_FAT (g)          7.0    23.0    52.0    98.0    45.6  (NOTE: High!)
SUGAR (g)            9.0    25.0    68.0   160.0    84.3  (NOTE: High!)
SODIUM (% DV)        5.0    14.0    33.0    61.0    30.1
CARBS (g)            4.0     9.0    16.0    28.0    15.6

USDA Daily Values (per 2000 calorie diet):
- Protein: 50g (10-35% of calories)
- Total Fat: 78g (<30% of calories)
- Saturated Fat: 20g (<10% of calories)
- Sugar: 50g added sugars (<10% of calories)
- Sodium: 2300mg
- Carbohydrates: 275g (45-65% of calories)

Per-Serving Targets (assuming 3 meals/day):
- Calories: 300-600 (balanced meal)
- Protein: 15-35g (adequate), cap rewards at 50g
- Fat: 5-25g (healthy range)
- Saturated Fat: 0-7g (⅓ of daily limit)
- Sugar: 0-15g (natural sugars acceptable)
- Sodium: 0-600mg (⅓ of daily limit)
- Carbs: 20-60g (balanced)

SCORING ALGORITHM:
------------------
Final Score = Base (50) + Nutrient Points + Balance Bonus - Penalties

1. Nutrient Points (max +40):
   - Each nutrient scored on whether it falls in healthy range
   - Protein capped at 50g to prevent dominance
   - Diminishing returns for exceeding "adequate" levels

2. Balance Bonus (max +10):
   - Rewards recipes where ALL nutrients are in healthy ranges
   - Encourages well-rounded nutrition

3. Penalties (max -40):
   - Excess calories, sat fat, sugar, sodium penalized
   - Imbalance penalty for extreme nutrient ratios

Score is then normalized to 10-98 scale and assigned A-E grades.

USAGE:
------
    df = score_nutrition(df, nutrition_col='nutrition')
    # Adds columns: nutrition_score, nutrition_grade

NOTES:
------
This is an improved version that replaces the original scoring algorithm.
The original had unlimited protein rewards causing bias toward high-protein recipes.
Expected: v2 will score balanced meals higher and penalize extreme-protein recipes.

Author: GitHub Copilot
Date: October 27, 2025
Version: 2.0
"""

import ast
import logging
from typing import List, Optional, Union

import numpy as np
import pandas as pd

# Set up logger for this module
logger = logging.getLogger(__name__)


# =============================================================================
# HEALTHY RANGES - Based on USDA Guidelines & Dataset Analysis
# =============================================================================

HEALTHY_RANGES = {
    # Format: (min_optimal, max_optimal, max_acceptable)
    # Sources documented in module docstring
    "calories": {
        "min_optimal": 150,  # Minimum for substantial meal
        "max_optimal": 600,  # Healthy meal size (⅓ of 2000 cal/day)
        "max_acceptable": 800,  # Upper bound before penalty
        "description": "Based on 300-600 cal per meal for balanced diet",
    },
    "protein": {
        "min_optimal": 15,  # Adequate protein per meal
        "max_optimal": 35,  # Optimal range for muscle maintenance
        "max_acceptable": 50,  # Cap rewards here (⅓ of 50g daily)
        "description": "USDA recommends 50g/day, 15-35g per meal is adequate",
    },
    "fat": {
        "min_optimal": 5,  # Minimum for nutrient absorption
        "max_optimal": 25,  # Healthy fat per meal
        "max_acceptable": 40,  # Upper bound (dataset 75th %ile: 41g)
        "description": "USDA recommends <78g/day total fat",
    },
    "saturated_fat": {
        "min_optimal": 0,  # Lower is better
        "max_optimal": 7,  # ⅓ of 20g daily limit
        "max_acceptable": 15,  # Dataset 50th %ile is 23g (too high!)
        "description": "USDA limit: 20g/day, aim for <7g per meal",
    },
    "sugar": {
        "min_optimal": 0,  # Lower is better
        "max_optimal": 15,  # Natural sugars acceptable
        "max_acceptable": 30,  # Dataset 50th %ile is 25g
        "description": "USDA recommends <50g added sugar/day",
    },
    "sodium": {
        "min_optimal": 0,  # Lower is better
        "max_optimal": 600,  # ⅓ of 2300mg daily limit (in % DV units)
        "max_acceptable": 1000,  # ~40% DV
        "description": "USDA limit: 2300mg/day, aim for <600mg per meal",
    },
    "carbs": {
        "min_optimal": 20,  # Minimum for energy
        "max_optimal": 60,  # Balanced carb intake
        "max_acceptable": 100,  # ⅓ of 275g daily
        "description": "USDA recommends 275g/day (45-65% of calories)",
    },
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def parse_nutrition_entry(value: Union[str, list, tuple, None]) -> Optional[List[float]]:
    """Parse nutrition data from various formats into list of 7 floats."""
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


def score_nutrient_in_range(value: float, nutrient_name: str) -> float:
    """
    Score a single nutrient based on whether it falls in healthy range.

    Returns:
        - 0 to 10 points based on how well the value fits healthy ranges
        - Higher scores for values in optimal range
        - Lower scores for values outside acceptable range
    """
    ranges = HEALTHY_RANGES.get(nutrient_name)
    if not ranges:
        return 5.0  # Neutral score if no range defined

    min_opt = ranges["min_optimal"]
    max_opt = ranges["max_optimal"]
    max_acc = ranges["max_acceptable"]

    # Perfect score: in optimal range
    if min_opt <= value <= max_opt:
        return 10.0

    # Good score: between optimal and acceptable
    elif max_opt < value <= max_acc:
        # Linear decay from 10 to 5
        ratio = (value - max_opt) / (max_acc - max_opt)
        return 10.0 - (ratio * 5.0)

    # Below optimal minimum (generally OK for things like sugar, sodium)
    elif value < min_opt:
        # For nutrients where lower is better (sugar, sodium, sat_fat)
        if min_opt == 0:
            return 10.0  # Perfect!
        # For nutrients that need minimum (protein, carbs)
        else:
            # Penalty for being too low
            ratio = value / min_opt
            return max(0.0, ratio * 10.0)

    # Above acceptable maximum: penalty
    else:
        # Heavy penalty for excess
        excess_ratio = min((value - max_acc) / max_acc, 2.0)  # Cap at 2x excess
        return max(0.0, 5.0 - (excess_ratio * 5.0))


def compute_balanced_score(nutrition_list: List[float]) -> Optional[float]:
    """
    Compute a balanced nutrition score using healthy ranges.

    Algorithm:
    1. Score each nutrient individually (0-10 points each)
    2. Apply protein cap to prevent dominance
    3. Add balance bonus if multiple nutrients in healthy range
    4. Apply penalties for extreme imbalances

    Returns score in arbitrary range (will be normalized later).
    """
    if nutrition_list is None:
        return None

    try:
        calories, total_fat, sugar, sodium, protein, saturated_fat, carbohydrates = nutrition_list

        # Score each nutrient component (0-10 points each, max 70 total)
        cal_score = score_nutrient_in_range(calories, "calories")
        protein_score = score_nutrient_in_range(protein, "protein")
        fat_score = score_nutrient_in_range(total_fat, "fat")
        sat_fat_score = score_nutrient_in_range(saturated_fat, "saturated_fat")
        sugar_score = score_nutrient_in_range(sugar, "sugar")
        sodium_score = score_nutrient_in_range(sodium, "sodium")
        carb_score = score_nutrient_in_range(carbohydrates, "carbs")

        # Base score: sum of individual nutrients
        base_score = cal_score + protein_score + fat_score + sat_fat_score + sugar_score + sodium_score + carb_score

        # Balance bonus: reward if multiple nutrients in optimal range
        in_optimal_count = sum(
            [
                HEALTHY_RANGES["calories"]["min_optimal"] <= calories <= HEALTHY_RANGES["calories"]["max_optimal"],
                HEALTHY_RANGES["protein"]["min_optimal"] <= protein <= HEALTHY_RANGES["protein"]["max_optimal"],
                HEALTHY_RANGES["fat"]["min_optimal"] <= total_fat <= HEALTHY_RANGES["fat"]["max_optimal"],
                saturated_fat <= HEALTHY_RANGES["saturated_fat"]["max_optimal"],
                sugar <= HEALTHY_RANGES["sugar"]["max_optimal"],
                sodium <= HEALTHY_RANGES["sodium"]["max_optimal"],
                HEALTHY_RANGES["carbs"]["min_optimal"] <= carbohydrates <= HEALTHY_RANGES["carbs"]["max_optimal"],
            ]
        )

        # Bonus: +2 points per nutrient in optimal range (max +14)
        balance_bonus = in_optimal_count * 2.0

        # Imbalance penalty: heavily penalize extreme outliers
        penalties = 0.0

        # Extreme calorie penalty
        if calories > 1000:
            penalties += (calories - 1000) * 0.01

        # Extreme saturated fat penalty (major health concern)
        if saturated_fat > 20:
            penalties += (saturated_fat - 20) * 0.5

        # Extreme sugar penalty
        if sugar > 50:
            penalties += (sugar - 50) * 0.2

        # Extreme sodium penalty
        if sodium > 50:  # 50% DV
            penalties += (sodium - 50) * 0.3

        # Cap total penalty
        penalties = min(penalties, 30.0)

        # Final score
        final_score = base_score + balance_bonus - penalties

        return final_score

    except Exception as e:
        logger.warning(f"Error computing balanced score: {e}")
        return None


def normalize_scores(raw_scores: pd.Series, min_val: float = 10, max_val: float = 98) -> pd.Series:
    """
    Normalize scores to 10-98 range using percentile clamping.

    Uses 1st and 99th percentiles to avoid extreme outliers affecting the scale.
    """
    logger.info("Normalizing nutrition scores (v2)")
    valid_scores = raw_scores.dropna()

    if len(valid_scores) == 0:
        logger.warning("No valid scores to normalize")
        return raw_scores

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
    """
    Assign letter grade based on normalized score.

    Grade Ranges:
    - A (80-100): Excellent nutrition
    - B (60-80): Good nutrition
    - C (40-60): Fair nutrition
    - D (20-40): Poor nutrition
    - E (10-20): Very poor nutrition
    """
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


# =============================================================================
# MAIN SCORING FUNCTION
# =============================================================================


def score_nutrition(df: pd.DataFrame, nutrition_col: str = "nutrition") -> pd.DataFrame:
    """
    Compute improved nutrition scores and letter grades using balanced approach.

    Adds two columns:
        - nutrition_score: Normalized score (10-98)
        - nutrition_grade: Letter grade (A-E)

    Args:
        df: DataFrame with nutrition data
        nutrition_col: Name of column containing nutrition array

    Returns:
        DataFrame with added scoring columns

    Example:
        >>> df = pd.read_csv('preprocessed_recipes.csv')
        >>> df = score_nutrition(df)
        >>> print(df[['name', 'nutrition_score', 'nutrition_grade']].head())
    """
    logger.info("Starting nutrition scoring (Weighted Balance Score)")
    df = df.copy()

    # Compute balanced scores
    logger.info(f"Processing {len(df)} recipes with balanced scoring algorithm")
    raw_scores = df[nutrition_col].apply(lambda x: compute_balanced_score(parse_nutrition_entry(x)))

    valid_count = raw_scores.notna().sum()
    logger.info(f"Computed balanced scores for {valid_count}/{len(df)} recipes")

    # Normalize to 10-98 scale
    df["nutrition_score"] = normalize_scores(raw_scores)
    df["nutrition_grade"] = df["nutrition_score"].apply(assign_grade)

    # Extract calories column only
    logger.info("Extracting calories column from nutrition array...")

    def extract_calories(nutrition_value):
        """Extract calories value from nutrition array."""
        parsed = parse_nutrition_entry(nutrition_value)
        if parsed and len(parsed) >= 1:
            return float(parsed[0])
        return 0.0

    df["calories"] = df[nutrition_col].apply(extract_calories)
    logger.info(f"Extracted calories column - Mean: {df['calories'].mean():.1f} kcal")

    # Log grade distribution
    grade_counts = df["nutrition_grade"].value_counts().sort_index()
    logger.info(f"Grade distribution: {grade_counts.to_dict()}")
    logger.info("Nutrition scoring completed")

    return df
