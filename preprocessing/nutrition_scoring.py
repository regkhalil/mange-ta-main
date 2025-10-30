# nutrition_scoring.py
"""
Evidence-Based Nutrition Scoring Module - Weighted Balance Score
=================================================================

SCORING ALGORITHM OVERVIEW:
---------------------------
This module implements a scientifically-grounded nutrition scoring system based on
WHO, USDA, AHA, and EFSA dietary guidelines. The algorithm prioritizes nutrients with
the strongest evidence for health impacts.

KEY FEATURES:
-------------
1. **Evidence-Based Weighting**: Nutrients weighted by health impact
   - Saturated Fat: 25% (highest - direct CVD risk, WHO/AHA #1 priority)
   - Protein: 20% (essential macronutrient, muscle maintenance)
   - Sodium: 15% (direct hypertension/stroke risk)
   - Total Fat: 13% (context-dependent, quality matters)
   - Sugar: 12% (indirect metabolic harm, inflammation)
   - Calories: 10% (energy balance foundation)
   - Carbs: 5% (lowest - quality matters more than quantity)

2. **Corrected %DV Units**: All nutrients use Percent Daily Value format
   - Fixes critical unit errors from previous version
   - Sodium optimal: 0-20% DV (was incorrectly 0-600% DV!)
   - Protein, fat, sugar, carbs: All converted from grams to %DV
   - Calories remain in kcal (not %DV)

3. **Healthy Ranges**: WHO/USDA/AHA/EFSA evidence-based optimal ranges
   - Optimal range: Maximum 10/10 score + balance bonus (+2 points)
   - Acceptable range: Gradual decay 5-10/10 score
   - Extreme outliers: Extra penalties (e.g., sodium >50% DV)

4. **Balance Bonus**: Rewards nutritionally well-rounded recipes
   - +2 points per nutrient in optimal range (max +14 points)
   - Encourages multi-nutrient balance, not single-nutrient optimization

NUTRITIONAL GUIDELINES & DATA SOURCES:
--------------------------------------
Dataset: 231,637 recipes from Food.com (Kaggle)
Format: [calories (#), total_fat (PDV), sugar (PDV), sodium (PDV),
         protein (PDV), saturated_fat (PDV), carbohydrates (PDV)]

Daily Values (DV):
- Protein: 50g | Total Fat: 78g | Saturated Fat: 20g | Sugar: 50g
- Sodium: 2300mg | Carbohydrates: 275g | Calories: 2000kcal
- Sugar: 50g added sugars (<10% of calories)
- Sodium: 2300mg
- Carbohydrates: 275g (45-65% of calories)

Optimal Ranges per Meal (assuming ~3 meals/day):
- Calories: 150-600 kcal (substantial meal size)
- Protein: 30-70% DV (15-35g per meal)
- Total Fat: 6-32% DV (5-25g per meal)
- Saturated Fat: 0-35% DV (0-7g per meal, <10% kcal - AHA)
- Sugar: 0-30% DV (0-15g per meal, <10% kcal - WHO)
- Sodium: 0-20% DV (0-460mg per meal, <2000mg/day - WHO)
- Carbohydrates: 7-22% DV (20-60g per meal, 45-65% kcal)

Extreme Penalty Thresholds (WHO/EFSA safety limits):
- Calories: >1000 kcal (~50% of daily intake)
- Protein: >150% DV (>75g, kidney stress risk)
- Total Fat: >70% DV (>55g, exceeds WHO <30% kcal)
- Saturated Fat: >100% DV (>20g/day, atherogenic - AHA)
- Sugar: >80% DV (>40g, exceeds WHO <10% kcal)
- Sodium: >50% DV (>1150mg, hypertension risk - WHO)
- Carbohydrates: >50% DV (>135g, glycemic spike risk)

SCORING ALGORITHM:
------------------
Final Score = (Weighted Base Score × 10) + Balance Bonus - Penalties

1. Weighted Base Score (0-10 points per nutrient):
   - Each nutrient scored 0-10 based on optimal/acceptable ranges
   - Scores weighted by health impact (sat_fat 25%, protein 20%, etc.)
   - Total weighted sum: 0-100 points after scaling

2. Balance Bonus (max +10 points):
   - +2 points per nutrient in optimal range (capped at +10)
   - Rewards well-rounded nutritional profiles

3. Extreme Penalties (max -30 points):
   - Additional penalties for dangerously high levels
   - Based on WHO/EFSA safety thresholds

Score is normalized to 10-98 scale and assigned A-E grades:
- A (85-98): Excellent nutrition
- B (70-84): Good nutrition
- C (55-69): Acceptable
- D (40-54): Poor
- E (10-39): Very poor

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
    # All nutrients in %DV (Percent Daily Value) EXCEPT calories (kcal)
    # Daily Values: Protein 50g, Total Fat 78g, Sat Fat 20g, Sugar 50g,
    #               Sodium 2300mg, Carbs 275g, Calories 2000kcal
    # Based on WHO, USDA, AHA, and EFSA recommendations
    "calories": {
        "min_optimal": 150,  # kcal - Minimum for substantial meal
        "max_optimal": 600,  # kcal - Healthy meal size (~⅓ of 2000 cal/day)
        "max_acceptable": 800,  # kcal - Upper bound before penalty
        "description": "Based on 300-600 kcal per meal for balanced diet (USDA)",
    },
    "protein": {
        "min_optimal": 30,  # %DV - 15g ÷ 50g DV = 30%
        "max_optimal": 70,  # %DV - 35g ÷ 50g DV = 70%
        "max_acceptable": 100,  # %DV - 50g ÷ 50g DV = 100%
        "description": "USDA recommends 50g/day, 30-70% DV (15-35g) per meal",
    },
    "total_fat": {
        "min_optimal": 6,  # %DV - 5g ÷ 78g DV = 6%
        "max_optimal": 32,  # %DV - 25g ÷ 78g DV = 32%
        "max_acceptable": 51,  # %DV - 40g ÷ 78g DV = 51%
        "description": "WHO recommends <30% kcal from fat, 6-32% DV (5-25g) per meal",
    },
    "saturated_fat": {
        "min_optimal": 0,  # %DV - Lower is always better
        "max_optimal": 35,  # %DV - 7g ÷ 20g DV = 35%
        "max_acceptable": 75,  # %DV - 15g ÷ 20g DV = 75%
        "description": "AHA limit: 20g/day (<10% kcal), 0-35% DV (0-7g) per meal",
    },
    "sugar": {
        "min_optimal": 0,  # %DV - Lower is always better
        "max_optimal": 30,  # %DV - 15g ÷ 50g DV = 30%
        "max_acceptable": 60,  # %DV - 30g ÷ 50g DV = 60%
        "description": "WHO recommends <10% kcal from sugar, 0-30% DV (0-15g) per meal",
    },
    "sodium": {
        "min_optimal": 0,  # %DV - Lower is always better
        "max_optimal": 20,  # %DV - 460mg ÷ 2300mg DV = 20%
        "max_acceptable": 35,  # %DV - 805mg ÷ 2300mg DV = 35%
        "description": "WHO limit: <2000mg/day, 0-20% DV (0-460mg) per meal",
    },
    "carbs": {
        "min_optimal": 7,  # %DV - 20g ÷ 275g DV = 7%
        "max_optimal": 22,  # %DV - 60g ÷ 275g DV = 22%
        "max_acceptable": 36,  # %DV - 100g ÷ 275g DV = 36%
        "description": "USDA recommends 275g/day (45-65% kcal), 7-22% DV (20-60g) per meal",
    },
}

# Nutrient importance weights based on WHO, AHA, and EFSA evidence
# Priority: saturated_fat > protein > sodium > total_fat > sugar > calories > carbs
_NUTRIENT_WEIGHTS_RAW = {
    "saturated_fat": 0.25,  # 25% - Highest priority: Direct CVD risk (WHO/AHA)
    "protein": 0.20,  # 20% - Essential macronutrient, muscle maintenance
    "sodium": 0.15,  # 15% - Direct hypertension/stroke risk (WHO)
    "total_fat": 0.13,  # 13% - Context-dependent (quality matters)
    "sugar": 0.12,  # 12% - Indirect metabolic harm, inflammation
    "calories": 0.10,  # 10% - Energy balance foundation
    "carbs": 0.05,  # 5% - Quality (whole grain vs refined) matters more than quantity
}

# Normalize weights to ensure exact sum of 1.00
NUTRIENT_WEIGHTS = {k: v / sum(_NUTRIENT_WEIGHTS_RAW.values()) for k, v in _NUTRIENT_WEIGHTS_RAW.items()}
# Verified total: 1.00 (100%)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def parse_nutrition_entry(value: Union[str, list, tuple, None]) -> Optional[List[float]]:
    """Parse nutrition data from various formats into list of 7 floats."""
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        if len(value) == 7:
            if any(pd.isna(x) for x in value):
                return None
            return list(value)
        return None
    if isinstance(value, str):
        try:
            parsed = ast.literal_eval(value)
            if isinstance(parsed, (list, tuple)) and len(parsed) == 7:
                if any(pd.isna(x) for x in parsed):
                    return None
                return list(parsed)
        except Exception:
            return None
    # Check if it's a scalar that pandas considers NaN
    try:
        if pd.isna(value):
            return None
    except (ValueError, TypeError):
        # If pd.isna fails, it's not a simple scalar
        pass
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
        fat_score = score_nutrient_in_range(total_fat, "total_fat")
        sat_fat_score = score_nutrient_in_range(saturated_fat, "saturated_fat")
        sugar_score = score_nutrient_in_range(sugar, "sugar")
        sodium_score = score_nutrient_in_range(sodium, "sodium")
        carb_score = score_nutrient_in_range(carbohydrates, "carbs")

        # Base score: weighted sum of individual nutrients (0-100 points)
        # Apply evidence-based weights: sat_fat 25%, protein 20%, sodium 15%, etc.
        base_score = (
            cal_score * NUTRIENT_WEIGHTS["calories"]
            + protein_score * NUTRIENT_WEIGHTS["protein"]
            + fat_score * NUTRIENT_WEIGHTS["total_fat"]
            + sat_fat_score * NUTRIENT_WEIGHTS["saturated_fat"]
            + sugar_score * NUTRIENT_WEIGHTS["sugar"]
            + sodium_score * NUTRIENT_WEIGHTS["sodium"]
            + carb_score * NUTRIENT_WEIGHTS["carbs"]
        ) * 10  # Scale to 0-100 range

        # Balance bonus: reward if multiple nutrients in optimal range
        in_optimal_count = sum(
            [
                HEALTHY_RANGES["calories"]["min_optimal"] <= calories <= HEALTHY_RANGES["calories"]["max_optimal"],
                HEALTHY_RANGES["protein"]["min_optimal"] <= protein <= HEALTHY_RANGES["protein"]["max_optimal"],
                HEALTHY_RANGES["total_fat"]["min_optimal"] <= total_fat <= HEALTHY_RANGES["total_fat"]["max_optimal"],
                saturated_fat <= HEALTHY_RANGES["saturated_fat"]["max_optimal"],
                sugar <= HEALTHY_RANGES["sugar"]["max_optimal"],
                sodium <= HEALTHY_RANGES["sodium"]["max_optimal"],
                HEALTHY_RANGES["carbs"]["min_optimal"] <= carbohydrates <= HEALTHY_RANGES["carbs"]["max_optimal"],
            ]
        )

        # Bonus: +2 points per nutrient in optimal range (max +10 to prevent over-inflation)
        balance_bonus = min(in_optimal_count * 2.0, 10.0)

        # Imbalance penalty: heavily penalize extreme outliers based on WHO/EFSA thresholds
        penalties = 0.0

        # Extreme calorie penalty (>1000 kcal = ~50% of daily intake)
        if calories > 1000:
            penalties += (calories - 1000) * 0.01

        # Extreme protein penalty (>150% DV = >75g, can stress kidneys - EFSA)
        if protein > 150:  # 150% DV
            penalties += (protein - 150) * 0.3

        # Extreme total fat penalty (>70% DV = >55g/meal, exceeds WHO <30% kcal)
        if total_fat > 70:  # 70% DV
            penalties += (total_fat - 70) * 0.2

        # Extreme saturated fat penalty (>100% DV = >20g/day, atherogenic - AHA)
        if saturated_fat > 100:  # 100% DV (was 20g, now corrected)
            penalties += (saturated_fat - 100) * 0.5

        # Extreme sugar penalty (>80% DV = >40g, exceeds WHO <10% kcal)
        if sugar > 80:  # 80% DV (was 50g, now corrected)
            penalties += (sugar - 80) * 0.2

        # Extreme sodium penalty (>50% DV = >1150mg, strongly linked to hypertension - WHO)
        if sodium > 50:  # 50% DV (already correct)
            penalties += (sodium - 50) * 0.3

        # Extreme carbs penalty (>50% DV = >135g, excess glycemic load - EFSA)
        if carbohydrates > 50:  # 50% DV
            penalties += (carbohydrates - 50) * 0.15

        # Cap total penalty
        penalties = min(penalties, 30.0)

        # Final score (clamped to reasonable range before normalization)
        # Base (0-100) + Bonus (0-10) - Penalties (0-30) = theoretical range [-20, 110]
        # Clamp to [0, 110] to ensure normalization works correctly
        final_score = base_score + balance_bonus - penalties
        final_score = max(0.0, min(final_score, 110.0))

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
        # Hard boundary enforcement: ensure score is strictly within [10, 98]
        scaled = max(min_val, min(scaled, max_val))
        return round(scaled, 2)

    normalized = raw_scores.apply(scale)
    logger.info(f"Normalized {len(valid_scores)} scores")
    return normalized


def assign_grade(score: float) -> Optional[str]:
    """
    Assign letter grade based on normalized score.

    Grade Ranges:
    - A (85-98): Excellent nutrition
    - B (70-84): Good nutrition
    - C (55-69): Acceptable
    - D (40-54): Poor
    - E (10-39): Very poor nutrition
    """
    if pd.isna(score):
        return None
    elif score >= 85:
        return "A"
    elif score >= 70:
        return "B"
    elif score >= 55:
        return "C"
    elif score >= 40:
        return "D"
    else:
        return "E"


# =============================================================================
# ANALYTICS PRECOMPUTATION FUNCTIONS
# =============================================================================


def extract_nutrient_columns(df: pd.DataFrame, nutrition_col: str = "nutrition") -> pd.DataFrame:
    """
    Extract individual nutrients from nutrition array into separate columns.
    This eliminates the need for runtime parsing in Streamlit analytics.

    Adds columns:
        - total_fat_pdv: Total fat % daily value
        - sugar_pdv: Sugar % daily value
        - sodium_pdv: Sodium % daily value
        - protein_pdv: Protein % daily value
        - saturated_fat_pdv: Saturated fat % daily value
        - carbs_pdv: Carbohydrates % daily value

    Args:
        df: DataFrame with nutrition column
        nutrition_col: Name of column containing nutrition array

    Returns:
        DataFrame with added nutrient columns
    """
    logger.info("Extracting individual nutrient columns...")

    nutrition_parsed = df[nutrition_col].apply(parse_nutrition_entry)

    df["total_fat_pdv"] = nutrition_parsed.apply(lambda x: float(x[1]) if x and len(x) > 1 else None)
    df["sugar_pdv"] = nutrition_parsed.apply(lambda x: float(x[2]) if x and len(x) > 2 else None)
    df["sodium_pdv"] = nutrition_parsed.apply(lambda x: float(x[3]) if x and len(x) > 3 else None)
    df["protein_pdv"] = nutrition_parsed.apply(lambda x: float(x[4]) if x and len(x) > 4 else None)
    df["saturated_fat_pdv"] = nutrition_parsed.apply(lambda x: float(x[5]) if x and len(x) > 5 else None)
    df["carbs_pdv"] = nutrition_parsed.apply(lambda x: float(x[6]) if x and len(x) > 6 else None)

    logger.info("Individual nutrient columns extracted successfully")
    return df


def calculate_complexity_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    Precompute complexity index for all recipes.

    Adds columns:
        - complexity_index: 0-100 composite score (steps 40%, ingredients 40%, time 20%)
        - complexity_category: "Simple" (0-33), "Moyen" (34-66), or "Complexe" (67-100)

    Args:
        df: DataFrame with n_steps, n_ingredients, minutes columns

    Returns:
        DataFrame with added complexity columns
    """
    logger.info("Calculating complexity index...")

    # Normalize each factor to 0-1 scale
    steps_min, steps_max = df["n_steps"].min(), df["n_steps"].max()
    ingr_min, ingr_max = df["n_ingredients"].min(), df["n_ingredients"].max()
    time_min, time_max = df["minutes"].min(), df["minutes"].max()

    df["_steps_norm"] = (df["n_steps"] - steps_min) / (steps_max - steps_min)
    df["_ingr_norm"] = (df["n_ingredients"] - ingr_min) / (ingr_max - ingr_min)
    df["_time_norm"] = (df["minutes"] - time_min) / (time_max - time_min)

    # Weighted composite index (steps 40%, ingredients 40%, time 20%)
    df["complexity_index"] = (df["_steps_norm"] * 0.4 + df["_ingr_norm"] * 0.4 + df["_time_norm"] * 0.2) * 100

    # Categorize
    df["complexity_category"] = pd.cut(
        df["complexity_index"], bins=[0, 33, 66, 100], labels=["Simple", "Moyen", "Complexe"], include_lowest=True
    )

    # Drop temporary columns
    df.drop(columns=["_steps_norm", "_ingr_norm", "_time_norm"], inplace=True)

    logger.info(f"Complexity index calculated - Mean: {df['complexity_index'].mean():.1f}")
    return df


def calculate_time_categories(df: pd.DataFrame) -> pd.DataFrame:
    """
    Precompute time categories for all recipes.

    Adds column:
        - time_category: "Rapide (≤15min)", "Moyen (15-30min)", "Long (30-60min)", "Très long (>60min)"

    Args:
        df: DataFrame with minutes column

    Returns:
        DataFrame with added time_category column
    """
    logger.info("Calculating time categories...")

    df["time_category"] = pd.cut(
        df["minutes"],
        bins=[0, 15, 30, 60, float("inf")],
        labels=["Rapide (≤15min)", "Moyen (15-30min)", "Long (30-60min)", "Très long (>60min)"],
        include_lowest=True,
    )

    category_counts = df["time_category"].value_counts()
    logger.info(f"Time categories: {category_counts.to_dict()}")
    return df


def precompute_ingredient_health_index(
    df: pd.DataFrame, output_path: str = "data/ingredient_health_index.csv", min_frequency: int = 100
) -> pd.DataFrame:
    """
    Precompute ingredient health index and save as separate CSV.
    This runs once during preprocessing and loads instantly in Streamlit.

    Calculates average nutrition score for each ingredient that appears
    in at least min_frequency recipes. Results are saved to a CSV file
    for fast loading in the analytics dashboard.

    Args:
        df: Recipe dataframe with nutrition_score and ingredients columns
        output_path: Path to save ingredient stats CSV
        min_frequency: Minimum times ingredient must appear to be included

    Returns:
        DataFrame with ingredient statistics
    """
    logger.info(f"Precomputing ingredient health index (min_frequency={min_frequency})...")

    # ==========================================================================
    # NEW IMPLEMENTATION: Pandas aggregation (v2 - replaces manual loops)
    # ==========================================================================
    # To revert to old implementation: Search for "OLD IMPLEMENTATION" below
    # and uncomment that section while removing this block
    # ==========================================================================

    # Step 1: Explode ingredients into rows (one row per ingredient-recipe pair)
    logger.info("Exploding ingredients into individual rows...")
    df_exploded = df[["nutrition_score", "ingredients"]].copy()

    # Parse and clean ingredients
    df_exploded["ingredients"] = df_exploded["ingredients"].apply(
        lambda x: [ing.strip().lower() for ing in ast.literal_eval(x)] if pd.notna(x) else []
    )

    # Explode to get one row per ingredient-recipe combination
    df_exploded = df_exploded.explode("ingredients")

    # Remove empty ingredients and null scores
    df_exploded = df_exploded[
        (df_exploded["ingredients"].notna())
        & (df_exploded["ingredients"] != "")
        & (df_exploded["nutrition_score"].notna())
    ]

    logger.info(f"Exploded to {len(df_exploded)} ingredient-recipe pairs")

    # Step 2: Aggregate using pandas groupby (type-safe, much faster)
    logger.info("Aggregating ingredient statistics using pandas groupby...")
    ingredient_df = (
        df_exploded.groupby("ingredients")["nutrition_score"]
        .agg(
            avg_score="mean",
            median_score="median",
            frequency="count",  # ALWAYS returns int64 (type-safe)
            std_score="std",
            min_score="min",
            max_score="max",
        )
        .reset_index()
    )

    # Rename column
    ingredient_df.rename(columns={"ingredients": "ingredient"}, inplace=True)

    # Calculate consistency
    ingredient_df["consistency"] = 1 / (ingredient_df["std_score"] + 0.1)

    logger.info(f"Calculated stats for {len(ingredient_df)} unique ingredients")

    # Step 3: Filter by minimum frequency
    ingredient_df = ingredient_df[ingredient_df["frequency"] >= min_frequency]

    # Step 4: Sort by average score (healthiest first)
    ingredient_df = ingredient_df.sort_values("avg_score", ascending=False)

    # ==========================================================================
    # OLD IMPLEMENTATION (commented out - for easy revert)
    # ==========================================================================
    # ingredient_scores = {}
    # ingredient_counts = {}
    #
    # # Parse ingredients and aggregate scores
    # for idx, row in df.iterrows():
    #     try:
    #         ingredients_list = ast.literal_eval(row["ingredients"])
    #         score = row["nutrition_score"]
    #
    #         if pd.notna(score):
    #             for ingredient in ingredients_list:
    #                 ingredient = ingredient.strip().lower()
    #                 if ingredient:
    #                     if ingredient not in ingredient_scores:
    #                         ingredient_scores[ingredient] = []
    #                         ingredient_counts[ingredient] = 0
    #                     ingredient_scores[ingredient].append(score)
    #                     ingredient_counts[ingredient] += 1
    #     except Exception:
    #         continue
    #
    # logger.info(f"Found {len(ingredient_scores)} unique ingredients")
    #
    # # Calculate statistics
    # ingredient_stats = []
    # for ingredient, scores in ingredient_scores.items():
    #     if ingredient_counts[ingredient] >= min_frequency:
    #         scores_array = np.array(scores)
    #         ingredient_stats.append(
    #             {
    #                 "ingredient": ingredient,
    #                 "avg_score": np.mean(scores_array),
    #                 "median_score": np.median(scores_array),
    #                 "frequency": ingredient_counts[ingredient],
    #                 "std_score": np.std(scores_array),
    #                 "min_score": np.min(scores_array),
    #                 "max_score": np.max(scores_array),
    #                 "consistency": 1 / (np.std(scores_array) + 0.1),
    #             }
    #         )
    #
    # # Sort by average score (healthiest first)
    # ingredient_df = pd.DataFrame(ingredient_stats)
    #
    # # DEFENSIVE FIX: Force numeric conversion - handles any edge cases
    # ingredient_df["frequency"] = pd.to_numeric(ingredient_df["frequency"], errors="coerce")
    #
    # # Drop any non-numeric rows (removes bad data instead of filling with defaults)
    # ingredient_df = ingredient_df.dropna(subset=["frequency"])
    #
    # ingredient_df = ingredient_df.sort_values("avg_score", ascending=False)
    # ==========================================================================

    # Step 5: Ensure proper dtypes before saving to CSV
    # Note: frequency is already int64 from .count(), convert to float64 for consistency
    ingredient_df = ingredient_df.astype(
        {
            "ingredient": str,
            "avg_score": "float64",
            "median_score": "float64",
            "frequency": "float64",  # CRITICAL: Explicitly set dtype to prevent object type in production
            "std_score": "float64",
            "min_score": "float64",
            "max_score": "float64",
            "consistency": "float64",
        }
    )

    # Save to CSV with explicit float_format to ensure clean numeric output
    ingredient_df.to_csv(output_path, index=False, float_format="%.10g")
    logger.info(f"Saved {len(ingredient_df)} ingredient stats to {output_path}")

    return ingredient_df


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

    # Extract calories column
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

    # === PRECOMPUTE ANALYTICS FOR STREAMLIT PERFORMANCE ===
    logger.info("Precomputing analytics for Streamlit performance...")

    # Extract individual nutrient columns
    df = extract_nutrient_columns(df, nutrition_col)

    # Calculate complexity metrics
    df = calculate_complexity_index(df)

    # Calculate time categories
    df = calculate_time_categories(df)

    # Precompute ingredient health index (saved separately)
    precompute_ingredient_health_index(df, output_path="data/ingredient_health_index.csv", min_frequency=100)

    logger.info("Nutrition scoring and analytics precomputation completed")

    return df
