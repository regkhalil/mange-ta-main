import logging
from collections import Counter

import pandas as pd


def prepare_vegetarian_classification(df: pd.DataFrame) -> pd.DataFrame:
    """
    Classify recipes as vegetarian or non-vegetarian based on their ingredients.

    Args:
        df (pd.DataFrame): DataFrame containing recipe data with an 'ingredients' column

    Returns:
        pd.DataFrame: DataFrame with added 'is_vegetarian' column
    """
    logging.info("Starting vegetarian classification process...")

    # Extract all unique ingredients from the dataset
    all_ingredients = []
    for ingredients_str in df["ingredients"].dropna():
        # Parse the ingredients string (assuming it's in list format like "['ingredient1', 'ingredient2']")
        try:
            # Remove brackets and quotes, split by comma
            ingredients_clean = str(ingredients_str).strip("[]").replace("'", "").replace('"', "")
            ingredients_list = [ing.strip() for ing in ingredients_clean.split(",")]
            all_ingredients.extend(ingredients_list)
        except Exception:
            continue

    # Count frequency of all ingredients
    ingredient_counts = Counter(all_ingredients)
    logging.info(f"Found {len(ingredient_counts)} unique ingredients in dataset")

    # Define potential non-vegetarian keywords to search for
    non_veg_keywords = [
        # Meat
        "beef",
        "pork",
        "lamb",
        "veal",
        "venison",
        "mutton",
        "goat",
        # Poultry
        "chicken",
        "turkey",
        "duck",
        "goose",
        "quail",
        # Seafood
        "fish",
        "salmon",
        "tuna",
        "cod",
        "halibut",
        "trout",
        "bass",
        "snapper",
        "shrimp",
        "prawn",
        "crab",
        "lobster",
        "clam",
        "mussel",
        "oyster",
        "scallop",
        "anchovy",
        "sardine",
        "mackerel",
        "herring",
        # Processed meats
        "bacon",
        "ham",
        "sausage",
        "pepperoni",
        "salami",
        "chorizo",
        "prosciutto",
        "pancetta",
        "mortadella",
        "bratwurst",
        "kielbasa",
        "hot dog",
        "frankfurter",
        # Ground meats
        "ground beef",
        "ground pork",
        "ground turkey",
        "ground chicken",
        "ground lamb",
        # Other animal products
        "gelatin",
        "lard",
        "tallow",
        "suet",
        "bone",
        "marrow",
        # Broths and stocks
        "chicken broth",
        "beef broth",
        "chicken stock",
        "beef stock",
        "bone broth",
        # General terms
        "meat",
        "steak",
        "roast",
        "cutlet",
        "fillet",
        "wing",
        "thigh",
        "breast",
    ]

    # Find actual non-vegetarian ingredients in the dataset
    dataset_non_veg_ingredients = []
    for ingredient, count in ingredient_counts.items():
        ingredient_lower = ingredient.lower()
        for keyword in non_veg_keywords:
            if keyword in ingredient_lower:
                dataset_non_veg_ingredients.append(ingredient)
                break

    # Remove duplicates and sort
    dataset_non_veg_ingredients = sorted(list(set(dataset_non_veg_ingredients)))
    logging.info(f"Identified {len(dataset_non_veg_ingredients)} non-vegetarian ingredients")

    # Create the final list for filtering
    non_veg_ingredients_lower = [ing.lower() for ing in dataset_non_veg_ingredients]

    def is_vegetarian(ingredients_str):
        """Check if a recipe is vegetarian based on its ingredients."""
        if pd.isna(ingredients_str):
            return False

        ingredients_lower = str(ingredients_str).lower()
        return not any(ingredient in ingredients_lower for ingredient in non_veg_ingredients_lower)

    # Add a new column to the DataFrame to specify if recipe is vegetarian
    df_copy = df.copy()
    df_copy["is_vegetarian"] = df_copy["ingredients"].apply(is_vegetarian)

    vegetarian_count = df_copy["is_vegetarian"].sum()
    total_count = len(df_copy)
    veg_percentage = vegetarian_count / total_count * 100
    logging.info(
        f"Classification complete: {vegetarian_count}/{total_count} recipes "
        f"classified as vegetarian ({veg_percentage:.1f}%)"
    )

    return df_copy


def filter_vegetarian_recipes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter DataFrame to return only vegetarian recipes.

    Args:
        df (pd.DataFrame): DataFrame with 'is_vegetarian' column

    Returns:
        pd.DataFrame: DataFrame containing only vegetarian recipes
    """
    if "is_vegetarian" not in df.columns:
        raise ValueError("DataFrame must contain 'is_vegetarian' column. Run prepare_vegetarian_classification first.")

    vegetarian_df = df[df["is_vegetarian"]].copy()
    logging.info(f"Filtered to {len(vegetarian_df)} vegetarian recipes")

    return vegetarian_df
