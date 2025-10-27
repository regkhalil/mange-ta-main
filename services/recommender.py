"""
Système de recommandations basé sur TF-IDF et similarité cosinus.
"""

from typing import List, Tuple

import pandas as pd
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class RecipeRecommender:
    """Système de recommandations de recettes utilisant TF-IDF."""

    def __init__(self, recipes_df: pd.DataFrame):
        """
        Initialise le système de recommandations.

        Args:
            recipes_df: DataFrame contenant les recettes
        """
        self.recipes_df = recipes_df
        self.vectorizer = None
        self.tfidf_matrix = None
        self._build_index()

    def _build_index(self):
        """Construit l'index TF-IDF à partir des recettes (OPTIMISÉ)."""
        # Créer un document texte pour chaque recette
        # Utilise les colonnes disponibles selon le format des données

        # Optimisation: Vectoriser l'opération au lieu de boucler
        if "ingredient_tokens" in self.recipes_df.columns:
            # Anciennes données avec tokens
            self.recipes_df["_combined_text"] = (
                self.recipes_df["ingredient_tokens"].astype(str)
                + " "
                + self.recipes_df["steps_tokens"].astype(str)
                + " "
                + self.recipes_df["techniques"].astype(str)
            )
            documents = self.recipes_df["_combined_text"].tolist()
        else:
            # Nouvelles données avec textes
            self.recipes_df["_combined_text"] = (
                self.recipes_df.get("ingredients", "").astype(str) + " " + self.recipes_df.get("steps", "").astype(str)
            )
            documents = self.recipes_df["_combined_text"].tolist()

        # Créer la matrice TF-IDF (limiter max_features pour performance)
        self.vectorizer = TfidfVectorizer(max_features=500, min_df=2, max_df=0.8)
        self.tfidf_matrix = self.vectorizer.fit_transform(documents)

    def get_similar_recipes(self, recipe_id: int, k: int = 10) -> List[Tuple[pd.Series, float]]:
        """
        Trouve les k recettes les plus similaires à une recette donnée.

        Args:
            recipe_id: ID de la recette de référence
            k: Nombre de recommandations à retourner

        Returns:
            Liste de tuples (recette, score de similarité)
        """
        # Trouver l'index de la recette
        idx = self.recipes_df[self.recipes_df["id"] == recipe_id].index
        if len(idx) == 0:
            return []

        idx = idx[0]

        # Calculer la similarité cosinus
        cosine_sim = cosine_similarity(self.tfidf_matrix[idx : idx + 1], self.tfidf_matrix).flatten()

        # Obtenir les indices des k+1 recettes les plus similaires (excluant la recette elle-même)
        similar_indices = cosine_sim.argsort()[::-1][1 : k + 1]

        # Retourner les recettes et leurs scores
        results = []
        for sim_idx in similar_indices:
            recipe = self.recipes_df.iloc[sim_idx]
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
            (filtered["totalTime"] >= prep_range[0])
            & (filtered["totalTime"] <= prep_range[1])
            & (filtered["ingredientCount"] >= ingredients_range[0])
            & (filtered["ingredientCount"] <= ingredients_range[1])
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
                "ingredients": recipe["ingredientCount"],
                "time": recipe["totalTime"],
                "calories": recipe["calories"],
                "vegetarian": recipe["is_vegetarian"],
                "similarity": f"{score:.2%}",
                "score": score,
            }
        )
    return formatted
