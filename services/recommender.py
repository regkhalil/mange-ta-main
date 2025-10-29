"""
Système de recommandations basé sur une matrice de similarité pré-calculée.
"""

from typing import List, Tuple, Optional, Dict, Any

import pandas as pd
import streamlit as st
from sklearn.metrics.pairwise import cosine_similarity

from .data_loader import read_pickle_file


class RecipeRecommender:
    """Système de recommandations de recettes utilisant une matrice de similarité pré-calculée."""

    def __init__(self, recipes_df: pd.DataFrame):
        """
        Initialise le système de recommandations.

        Args:
            recipes_df: DataFrame contenant les recettes
        """
        self.recipes_df = recipes_df
        self.similarity_data = None
        self.id_to_index = None
        self.index_to_id = None
        self.combined_features = None
        self._build_index()

    def _build_index(self):
        """Charge la matrice de similarité pré-calculée."""
        # Load pre-computed similarity matrix (required)
        self.similarity_data = read_pickle_file("similarity_matrix.pkl")
        self.id_to_index = self.similarity_data["id_to_index"]
        self.index_to_id = self.similarity_data["index_to_id"]
        self.combined_features = self.similarity_data["combined_features"]
        print("✅ Loaded pre-computed similarity matrix successfully")

    def get_similar_recipes(self, recipe_id: int, k: int = 10) -> List[Tuple[pd.Series, float]]:
        """
        Trouve les k recettes les plus similaires à une recette donnée.
        Utilise uniquement la matrice de similarité pré-calculée.

        Args:
            recipe_id: ID de la recette de référence
            k: Nombre de recommandations à retourner

        Returns:
            Liste de tuples (recette, score de similarité)
        """
        # Check if recipe_id exists in our mapping
        if recipe_id not in self.id_to_index:
            print(f"⚠️ Recipe ID {recipe_id} not found in similarity matrix")
            return []

        # Get the index for this recipe
        recipe_idx = self.id_to_index[recipe_id]
        
        # Get the feature vector for this recipe
        query_vec = self.combined_features[recipe_idx].reshape(1, -1)
        
        # Compute cosine similarity with all recipes
        cosine_sim = cosine_similarity(query_vec, self.combined_features).flatten()

        # Get the indices of the k+1 most similar recipes (excluding self)
        similar_indices = cosine_sim.argsort()[::-1][1 : k + 1]

        # Convert indices back to recipe IDs and get recipe data
        results = []
        for sim_idx in similar_indices:
            similar_recipe_id = self.index_to_id[sim_idx]
            # Find the recipe in our DataFrame
            recipe_row = self.recipes_df[self.recipes_df["id"] == similar_recipe_id]
            if not recipe_row.empty:
                recipe = recipe_row.iloc[0]
                score = cosine_sim[sim_idx]
                results.append((recipe, score))

        return results

    def recommend_by_filters(
        self,
        prep_range: Tuple[int, int],
        ingredients_range: Tuple[int, int],
        calories_range: Tuple[int, int],
        vegetarian_only: bool = False,
        k: int = 12,
    ) -> List[pd.Series]:
        """
        Recommande des recettes basées sur des filtres.

        Args:
            prep_range: Tuple (min, max) pour le temps de préparation
            ingredients_range: Tuple (min, max) pour le nombre d'ingrédients
            calories_range: Tuple (min, max) pour les calories
            vegetarian_only: Filtrer uniquement les recettes végétariennes
            k: Nombre de recommandations

        Returns:
            Liste de recettes recommandées
        """
        filtered = self.recipes_df.copy()

        # Appliquer les filtres
        filtered = filtered[
            (filtered["minutes"] >= prep_range[0])
            & (filtered["minutes"] <= prep_range[1])
            & (filtered["n_ingredients"] >= ingredients_range[0])
            & (filtered["n_ingredients"] <= ingredients_range[1])
            & (filtered["calories"] >= calories_range[0])
            & (filtered["calories"] <= calories_range[1])
        ]

        if vegetarian_only:
            filtered = filtered[filtered["is_vegetarian"]]

        # Retourner les k premières recettes
        results = []
        for _, recipe in filtered.head(k).iterrows():
            results.append(recipe)

        return results


@st.cache_resource
def get_recommender(recipes_df: pd.DataFrame) -> RecipeRecommender:
    """
    Crée et met en cache le système de recommandations.

    Args:
        recipes_df: DataFrame des recettes

    Returns:
        Instance de RecipeRecommender
    """
    return RecipeRecommender(recipes_df)


def format_recommendations_for_display(recommendations: List[Tuple[pd.Series, float]]) -> List[dict]:
    """
    Formate les recommandations pour l'affichage.

    Args:
        recommendations: Liste de tuples (recette, score)

    Returns:
        Liste de dictionnaires avec les informations formatées
    """
    formatted = []
    for recipe, score in recommendations:
        formatted.append(
            {
                "id": recipe["id"],
                "name": f"Recette #{recipe['id']}",
                "ingredients": int(recipe.get("n_ingredients", 0)),
                "time": recipe["minutes"],
                "calories": recipe["calories"],
                "vegetarian": recipe["is_vegetarian"],
                "similarity": f"{score:.2%}",
                "score": score,
            }
        )
    return formatted
