"""
Moteur de recherche optimisé pour les recettes.
Utilise la recherche textuelle et le ranking par pertinence.
"""

from typing import List, Optional, Tuple

import pandas as pd
import streamlit as st


@st.cache_data(ttl=3600)
def search_recipes(
    recipes_df: pd.DataFrame,
    query: str = "",
    prep_time_max: int = 180,
    ingredients_max: int = 30,
    calories_max: int = 1000,
    vegetarian_only: bool = False,
    nutrition_grades: List[str] = None,
    sort_by: str = "relevance",
    page: int = 1,
    page_size: int = 20,
) -> Tuple[pd.DataFrame, int]:
    """
    Recherche et filtre les recettes avec pagination.

    Args:
        recipes_df: DataFrame complet des recettes
        query: Texte de recherche
        prep_time_max: Temps de préparation maximum
        ingredients_max: Nombre d'ingrédients maximum
        calories_max: Calories maximum
        vegetarian_only: Filtrer les recettes végétariennes uniquement
        nutrition_grades: Liste des grades nutritionnels acceptés
        sort_by: Tri (relevance, health_score, prep_time)
        page: Numéro de page
        page_size: Nombre de résultats par page

    Returns:
        Tuple (DataFrame paginé, nombre total de résultats)
    """
    # Créer le masque de filtrage
    mask = (
        (recipes_df["totalTime"] <= prep_time_max)
        & (recipes_df["n_ingredients"] <= ingredients_max)
        & (recipes_df["calories"] <= calories_max)
    )

    # Filtre végétarien
    if vegetarian_only and "is_vegetarian" in recipes_df.columns:
        mask = mask & recipes_df["is_vegetarian"]

    # Filtre grades nutritionnels
    if nutrition_grades and len(nutrition_grades) > 0 and "nutrition_grade" in recipes_df.columns:
        mask = mask & recipes_df["nutrition_grade"].isin(nutrition_grades)

    # Appliquer les filtres de base
    filtered_df = recipes_df[mask].copy()

    # Recherche textuelle si une requête est fournie
    if query and query.strip():
        query_lower = query.lower().strip()

        # Recherche dans les tokens de nom et d'ingrédients
        def match_query(row):
            # Recherche dans le nom
            name_tokens_str = " ".join([str(t).lower() for t in row["name_tokens"]])
            if query_lower in name_tokens_str:
                return 3  # Score élevé pour correspondance dans le titre

            # Recherche dans les ingrédients
            ingredient_tokens_str = " ".join([str(t).lower() for t in row["ingredient_tokens"]])
            if query_lower in ingredient_tokens_str:
                return 2  # Score moyen pour correspondance dans les ingrédients

            # Recherche dans les étapes
            steps_tokens_str = " ".join([str(t).lower() for t in row["steps_tokens"]])
            if query_lower in steps_tokens_str:
                return 1  # Score faible pour correspondance dans les étapes

            return 0  # Pas de correspondance

        # Calculer les scores de pertinence
        filtered_df["relevance_score"] = filtered_df.apply(match_query, axis=1)

        # Garder uniquement les recettes avec correspondance
        filtered_df = filtered_df[filtered_df["relevance_score"] > 0]
    else:
        # Pas de recherche : attribuer un score uniforme
        filtered_df["relevance_score"] = 1

    # Tri
    if sort_by == "relevance" and query:
        filtered_df = filtered_df.sort_values("relevance_score", ascending=False)
    elif sort_by == "health_score" and "nutrition_score" in filtered_df.columns:
        filtered_df = filtered_df.sort_values("nutrition_score", ascending=False, na_position="last")
    elif sort_by == "prep_time":
        filtered_df = filtered_df.sort_values("totalTime", ascending=True)
    else:
        # Tri par défaut : ID ou tendance
        pass

    # Nombre total de résultats
    total_results = len(filtered_df)

    # Pagination
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size

    paginated_df = filtered_df.iloc[start_idx:end_idx]

    return paginated_df, total_results


@st.cache_data
def get_recipe_by_id(recipes_df: pd.DataFrame, recipe_id: int) -> Optional[pd.Series]:
    """
    Récupère une recette par son ID.

    Args:
        recipes_df: DataFrame des recettes
        recipe_id: ID de la recette

    Returns:
        Série pandas de la recette ou None
    """
    result = recipes_df[recipes_df["id"] == recipe_id]
    if len(result) > 0:
        return result.iloc[0]
    return None


def format_recipe_title(recipe: pd.Series) -> str:
    """
    Génère un titre lisible pour une recette.

    Args:
        recipe: Série pandas de la recette

    Returns:
        Titre formaté
    """
    # Utiliser les tokens de nom pour créer un titre
    if "name_tokens" in recipe and len(recipe["name_tokens"]) > 0:
        # Joindre les premiers tokens
        title_tokens = recipe["name_tokens"][:5]  # Limiter à 5 tokens
        title = " ".join([str(t).capitalize() for t in title_tokens])
        return title
    return f"Recette #{int(recipe['id'])}"


def format_description(recipe: pd.Series, max_length: int = 180) -> str:
    """
    Génère une description courte pour une recette.

    Args:
        recipe: Série pandas de la recette
        max_length: Longueur maximale de la description

    Returns:
        Description formatée
    """
    # Utiliser les premiers steps comme description
    if "steps_tokens" in recipe and len(recipe["steps_tokens"]) > 0:
        # Joindre les premiers tokens
        desc_tokens = recipe["steps_tokens"][:20]  # Limiter à 20 tokens
        description = " ".join([str(t) for t in desc_tokens])

        # Couper proprement si trop long
        if len(description) > max_length:
            description = description[:max_length].rsplit(" ", 1)[0] + "..."

        return description

    return "Délicieuse recette à découvrir !"


def get_trending_recipes(recipes_df: pd.DataFrame, limit: int = 20) -> pd.DataFrame:
    """
    Récupère les recettes "tendances" (fallback quand pas de recherche).
    Tri par health score ou random.

    Args:
        recipes_df: DataFrame des recettes
        limit: Nombre de recettes à retourner

    Returns:
        DataFrame des recettes tendances
    """
    # Tri par nutrition_score si disponible, sinon par ID
    if "nutrition_score" in recipes_df.columns:
        trending = recipes_df.sort_values("nutrition_score", ascending=False, na_position="last")
    else:
        trending = recipes_df.copy()

    return trending.head(limit)
