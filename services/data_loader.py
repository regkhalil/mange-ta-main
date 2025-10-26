"""
Service de chargement et prétraitement des données pour l'application Mangetamain.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st


@st.cache_data(show_spinner=False)  # Désactiver le spinner par défaut, on gère manuellement
def load_recipes(data_dir: str = None) -> pd.DataFrame:
    """
    Charge et prétraite les données de recettes depuis PP_recipes.csv et RAW_recipes.csv.
    Merge les deux pour avoir les features ET les textes recherchables.

    Returns:
        DataFrame avec les colonnes prétraitées pour l'application
    """
    if data_dir is None:
        # Chemin relatif depuis le dossier de l'application
        data_dir = Path.cwd() / "data"

    # Vérifier si le fichier preprocessed existe
    preprocessed_path = Path(data_dir) / "preprocessed_recipes.csv"

    if preprocessed_path.exists():
        # Charger les données prétraitées enrichies (optimisé avec dtypes)
        df = pd.read_csv(
            preprocessed_path,
            low_memory=False,
            dtype={
                "id": "int64",
                "minutes": "float32",
                "n_steps": "float32",
                "n_ingredients": "float32",
            },
        )

        # Merger avec RAW_recipes pour récupérer la description (fallback si pas dans preprocessed)
        try:
            if 'description' not in df.columns:
                raw_recipes_path = Path(data_dir) / "RAW_recipes.csv"
                if raw_recipes_path.exists():
                    raw_df = pd.read_csv(raw_recipes_path, usecols=["id", "description"])
                    df = df.merge(raw_df, on="id", how="left")
        except Exception as e:
            print(f"Impossible de charger les descriptions: {e}")

        # Créer des colonnes dérivées pour l'UI (si elles n'existent pas)
        if "ingredientCount" not in df.columns and "n_ingredients" in df.columns:
            df["ingredientCount"] = df["n_ingredients"]

        if "stepsCount" not in df.columns and "n_steps" in df.columns:
            df["stepsCount"] = df["n_steps"]

        if "totalTime" not in df.columns and "minutes" in df.columns:
            df["totalTime"] = df["minutes"].clip(5, 300)  # Limiter entre 5 et 300 minutes

        # Estimer les calories à partir du nombre d'étapes
        if "calories" not in df.columns:
            if "n_steps" in df.columns:
                df["calories"] = (df["n_steps"] * 10 + 100).clip(50, 800)
            else:
                df["calories"] = 300  # Valeur par défaut

        # Créer alias pour compatibilité
        if "isVegetarian" not in df.columns:
            if "is_vegetarian" in df.columns:
                df["isVegetarian"] = df["is_vegetarian"]
            else:
                df["isVegetarian"] = False

        # Créer le Nutri-Score grade si nutrition_score existe
        if "nutrition_grade" not in df.columns and "nutrition_score" in df.columns:
            # Convertir le score en grade (A-E)
            def score_to_grade(score):
                if pd.isna(score):
                    return "C"  # Défaut
                score = float(score)
                if score <= 40:
                    return "A"
                elif score <= 55:
                    return "B"
                elif score <= 70:
                    return "C"
                elif score <= 80:
                    return "D"
                else:
                    return "E"

            df["nutrition_grade"] = df["nutrition_score"].apply(score_to_grade)
        elif "nutrition_grade" not in df.columns:
            df["nutrition_grade"] = "C"  # Grade par défaut

        # Ajouter le rating moyen des recettes à partir des interactions (OPTIMISÉ)
        if "average_rating" not in df.columns:
            try:
                # Charger les interactions pour calculer le rating moyen
                interactions_path = Path(data_dir) / "RAW_interactions.csv"
                if interactions_path.exists():
                    # Lire seulement les colonnes nécessaires avec échantillonnage
                    interactions = pd.read_csv(
                        interactions_path,
                        usecols=["recipe_id", "rating"],
                        dtype={"recipe_id": "int64", "rating": "float32"},
                    )
                    # Calculer la moyenne par recette
                    avg_ratings = interactions.groupby("recipe_id", as_index=False)["rating"].mean()
                    avg_ratings.columns = ["id", "average_rating"]
                    # Merger avec les recettes
                    df = df.merge(avg_ratings, on="id", how="left")
                    # Remplir les valeurs manquantes avec 4.0
                    df["average_rating"] = df["average_rating"].fillna(4.0)
                else:
                    df["average_rating"] = 4.0
            except Exception as e:
                print(f"Erreur lors du chargement des ratings: {e}")
                df["average_rating"] = 4.0

    else:
        # Fallback: charger depuis PP_recipes et RAW_recipes
        recipes_path = Path(data_dir) / "PP_recipes.csv"
        raw_recipes_path = Path(data_dir) / "RAW_recipes.csv"

        df = pd.read_csv(recipes_path, nrows=10000)
        raw_df = pd.read_csv(raw_recipes_path)
        raw_df = raw_df[["id", "name", "ingredients", "steps"]]
        df = df.merge(raw_df, on="id", how="left")

        df["name_tokens"] = df["name_tokens"].apply(eval)
        df["ingredient_tokens"] = df["ingredient_tokens"].apply(eval)
        df["steps_tokens"] = df["steps_tokens"].apply(eval)
        df["techniques"] = df["techniques"].apply(eval)
        df["ingredient_ids"] = df["ingredient_ids"].apply(eval)

        df["ingredientCount"] = df["ingredient_tokens"].apply(len)
        df["stepsCount"] = df["steps_tokens"].apply(len)

        calorie_mapping = {0: 200, 1: 400, 2: 600, 3: 800}
        df["calories"] = df["calorie_level"].map(calorie_mapping)
        df["totalTime"] = df["stepsCount"] * 5 + df["techniques"].apply(lambda x: sum(x)) * 2
        df["totalTime"] = df["totalTime"].clip(5, 180)

        if "nutrition_score" not in df.columns:
            df["nutrition_score"] = np.nan
        if "nutrition_grade" not in df.columns:
            df["nutrition_grade"] = None
        if "is_vegetarian" not in df.columns:
            df["is_vegetarian"] = df["ingredient_ids"].apply(lambda ids: all(id not in [389, 7655] for id in ids))

        df["isVegetarian"] = df.get("is_vegetarian", False)

    return df


@st.cache_data
def load_users(data_dir: str = None) -> pd.DataFrame:
    """
    Charge les données utilisateurs depuis PP_users.csv.

    Returns:
        DataFrame avec les profils utilisateurs
    """
    if data_dir is None:
        data_dir = Path.cwd() / "data"

    users_path = Path(data_dir) / "PP_users.csv"
    df = pd.read_csv(users_path)

    # Convertir les colonnes de listes
    df["techniques"] = df["techniques"].apply(eval)
    df["items"] = df["items"].apply(eval)
    df["ratings"] = df["ratings"].apply(eval)

    return df


@st.cache_data
def load_interactions(data_dir: str = None, split: str = "train") -> pd.DataFrame:
    """
    Charge les interactions utilisateur-recette.

    Args:
        data_dir: Répertoire contenant les données
        split: 'train', 'validation' ou 'test'

    Returns:
        DataFrame des interactions
    """
    if data_dir is None:
        data_dir = Path.cwd() / "data"

    interactions_path = Path(data_dir) / f"interactions_{split}.csv"
    df = pd.read_csv(interactions_path)
    return df


def get_recipe_name(recipe_id: int, recipes_df: pd.DataFrame) -> str:
    """
    Récupère le nom lisible d'une recette à partir de ses tokens.

    Args:
        recipe_id: ID de la recette
        recipes_df: DataFrame des recettes

    Returns:
        Nom de la recette (approximatif basé sur les tokens)
    """
    recipe = recipes_df[recipes_df["id"] == recipe_id]
    if recipe.empty:
        return f"Recette #{recipe_id}"

    # Simplifier pour l'affichage
    return f"Recette #{recipe_id}"


def get_recipe_details(recipe_id: int, recipes_df: pd.DataFrame) -> dict:
    """
    Récupère tous les détails d'une recette.

    Args:
        recipe_id: ID de la recette
        recipes_df: DataFrame des recettes

    Returns:
        Dictionnaire avec les détails de la recette
    """
    recipe = recipes_df[recipes_df["id"] == recipe_id].iloc[0]

    return {
        "id": recipe["id"],
        "name": get_recipe_name(recipe_id, recipes_df),
        "ingredients": len(recipe["ingredient_tokens"]),
        "steps": len(recipe["steps_tokens"]),
        "calories": recipe["calories"],
        "totalTime": recipe["totalTime"],
        "isVegetarian": recipe["isVegetarian"],
        "techniques": recipe["techniques"],
        "calorie_level": recipe["calorie_level"],
    }


def filter_recipes(
    recipes_df: pd.DataFrame,
    prep_range: tuple = (0, 180),
    ingredients_range: tuple = (1, 30),
    calories_range: tuple = (0, 1000),
    vegetarian_only: bool = False,
    nutrition_grades: list = None,
) -> pd.DataFrame:
    """
    Filtre les recettes selon les critères spécifiés.

    Args:
        recipes_df: DataFrame des recettes
        prep_range: Tuple (min, max) pour le temps de préparation
        ingredients_range: Tuple (min, max) pour le nombre d'ingrédients
        calories_range: Tuple (min, max) pour les calories
        vegetarian_only: Filtrer uniquement les recettes végétariennes
        nutrition_grades: Liste des grades nutritionnels acceptés (A, B, C, D, E)

    Returns:
        DataFrame filtré
    """
    result = recipes_df.copy()

    # Déterminer les colonnes de temps (essayer totalTime d'abord, puis minutes)
    time_col = "totalTime" if "totalTime" in recipes_df.columns else "minutes"

    # Déterminer les colonnes d'ingrédients
    ing_col = "ingredientCount" if "ingredientCount" in recipes_df.columns else "n_ingredients"

    # Déterminer les colonnes de calories
    cal_col = "calories" if "calories" in recipes_df.columns else None

    # Filtrer par temps de préparation
    if time_col in result.columns:
        result = result[(result[time_col] >= prep_range[0]) & (result[time_col] <= prep_range[1])]

    # Filtrer par nombre d'ingrédients
    if ing_col in result.columns:
        result = result[(result[ing_col] >= ingredients_range[0]) & (result[ing_col] <= ingredients_range[1])]

    # Filtrer par calories (si la colonne existe)
    if cal_col and cal_col in result.columns:
        result = result[(result[cal_col] >= calories_range[0]) & (result[cal_col] <= calories_range[1])]

    # Filtre végétarien
    if vegetarian_only:
        if "isVegetarian" in result.columns:
            result = result[result["isVegetarian"]]
        elif "is_vegetarian" in result.columns:
            result = result[result["is_vegetarian"]]

    # Filtre grades nutritionnels
    if nutrition_grades and len(nutrition_grades) > 0 and "nutrition_grade" in result.columns:
        result = result[result["nutrition_grade"].isin(nutrition_grades)]

    return result


def get_recipe_stats(recipes_df: pd.DataFrame) -> dict:
    """
    Calcule les statistiques globales sur les recettes.

    Args:
        recipes_df: DataFrame des recettes

    Returns:
        Dictionnaire avec les statistiques
    """
    return {
        "total_recipes": len(recipes_df),
        "avg_prep_time": recipes_df["totalTime"].mean(),
        "median_prep_time": recipes_df["totalTime"].median(),
        "avg_ingredients": recipes_df["ingredientCount"].mean(),
        "avg_calories": recipes_df["calories"].mean(),
        "vegetarian_count": recipes_df["isVegetarian"].sum(),
        "vegetarian_percentage": (recipes_df["isVegetarian"].sum() / len(recipes_df)) * 100,
    }
