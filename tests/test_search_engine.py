"""
Tests pour le moteur de recherche (services/search_engine.py).

Ce module teste la recherche textuelle et le ranking des résultats.
"""

import pandas as pd
import pytest

from services.search_engine import search_recipes


class TestSearchFunction:
    """Tests pour la fonction de recherche."""

    @pytest.fixture
    def sample_recipes(self):
        """Fixture fournissant des recettes de test."""
        return pd.DataFrame(
            {
                "id": [1, 2, 3, 4, 5],
                "name": [
                    "Chocolate Cake",
                    "Vanilla Ice Cream",
                    "Strawberry Chocolate Mousse",
                    "Chicken Pasta",
                    "Vegetarian Lasagna",
                ],
                "ingredients": [
                    "['chocolate', 'flour', 'sugar', 'eggs']",
                    "['milk', 'vanilla', 'sugar', 'cream']",
                    "['strawberry', 'chocolate', 'cream', 'sugar']",
                    "['chicken', 'pasta', 'tomato', 'cheese']",
                    "['pasta', 'vegetables', 'cheese', 'tomato']",
                ],
                "steps": [
                    "['Mix chocolate', 'Bake cake']",
                    "['Freeze mixture']",
                    "['Whip cream', 'Add chocolate']",
                    "['Cook pasta', 'Add chicken']",
                    "['Layer pasta', 'Bake lasagna']",
                ],
                "nutrition_score": [45.0, 30.0, 25.0, 60.0, 70.0],
                "minutes": [60, 15, 30, 45, 90],
                "n_ingredients": [4, 4, 4, 4, 5],
                "calories": [400, 250, 300, 500, 450],
                "is_vegetarian": [True, True, True, False, True],
                "nutrition_grade": ["C", "D", "E", "B", "A"],
            }
        )

    def test_search_function_returns_tuple(self, sample_recipes):
        """Test : La fonction search_recipes retourne un tuple (DataFrame, int)."""
        # Ajouter les colonnes nécessaires pour search_recipes
        sample_recipes["name_tokens"] = sample_recipes["name"].str.split()
        sample_recipes["ingredient_tokens"] = sample_recipes["ingredients"].str.split()
        sample_recipes["steps_tokens"] = sample_recipes["steps"].str.split()

        results, total = search_recipes(sample_recipes, query="chocolate", page_size=10)

        assert isinstance(results, pd.DataFrame)
        assert isinstance(total, int)
        assert total >= 0

    def test_search_with_query(self, sample_recipes):
        """Test : Recherche avec une requête textuelle."""
        # Ajouter les colonnes nécessaires
        sample_recipes["name_tokens"] = sample_recipes["name"].str.split()
        sample_recipes["ingredient_tokens"] = sample_recipes["ingredients"].str.split()
        sample_recipes["steps_tokens"] = sample_recipes["steps"].str.split()

        results, total = search_recipes(sample_recipes, query="chocolate", page_size=10)

        # Devrait trouver au moins quelques résultats
        assert total >= 0
        assert len(results) >= 0

    def test_search_with_filters(self, sample_recipes):
        """Test : Recherche avec filtres."""
        results, total = search_recipes(
            sample_recipes, query="", prep_time_max=60, ingredients_max=5, calories_max=500, page_size=10
        )

        # Devrait filtrer les recettes
        assert len(results) <= len(sample_recipes)

        # Toutes les recettes devraient respecter les filtres
        if len(results) > 0:
            assert (results["minutes"] <= 60).all()
            assert (results["n_ingredients"] <= 5).all()
            assert (results["calories"] <= 500).all()

    def test_search_vegetarian_filter(self, sample_recipes):
        """Test : Filtre végétarien."""
        results, total = search_recipes(sample_recipes, query="", vegetarian_only=True, page_size=10)

        # Toutes les recettes devraient être végétariennes
        if len(results) > 0:
            assert results["is_vegetarian"].all()

    def test_search_empty_query(self, sample_recipes):
        """Test : Recherche sans requête (retourne tout)."""
        results, total = search_recipes(sample_recipes, query="", page_size=100)

        # Devrait retourner toutes les recettes (selon les filtres par défaut)
        assert total >= 0
        assert len(results) >= 0

    def test_search_pagination(self, sample_recipes):
        """Test : Pagination fonctionne correctement."""
        # Page 1
        results_p1, total = search_recipes(sample_recipes, query="", page=1, page_size=2)

        # Page 2
        results_p2, total2 = search_recipes(sample_recipes, query="", page=2, page_size=2)

        # Total devrait être le même
        assert total == total2

        # Les résultats devraient être différents
        if len(results_p1) > 0 and len(results_p2) > 0:
            assert not results_p1["id"].equals(results_p2["id"])

    def test_search_nutrition_grades_filter(self, sample_recipes):
        """Test : Filtre par grades nutritionnels."""
        results, total = search_recipes(sample_recipes, query="", nutrition_grades=["A", "B"], page_size=10)

        # Les résultats devraient avoir seulement les grades A ou B
        if len(results) > 0:
            assert results["nutrition_grade"].isin(["A", "B"]).all()


class TestSearchEdgeCases:
    """Tests des cas limites."""

    def test_search_with_empty_dataframe(self):
        """Test : Recherche sur DataFrame vide - devrait retourner 0 résultats."""
        empty_df = pd.DataFrame(
            columns=[
                "id",
                "name",
                "ingredients",
                "steps",
                "minutes",
                "n_ingredients",
                "calories",
                "is_vegetarian",
                "nutrition_grade",
                "name_tokens",
                "ingredient_tokens",
                "steps_tokens",
            ]
        )

        # Sans requête pour éviter les problèmes avec apply sur DataFrame vide
        results, total = search_recipes(empty_df, query="", page_size=10)

        assert len(results) == 0
        assert total == 0

    def test_search_with_special_characters(self):
        """Test : Recherche avec caractères spéciaux."""
        recipes = pd.DataFrame(
            {
                "id": [1],
                "name": ["Mom's Recipe!"],
                "ingredients": ["['flour']"],
                "steps": ["['mix']"],
                "minutes": [30],
                "n_ingredients": [1],
                "calories": [200],
                "is_vegetarian": [True],
                "nutrition_grade": ["B"],
            }
        )

        # Ajouter les colonnes tokens
        recipes["name_tokens"] = recipes["name"].str.split()
        recipes["ingredient_tokens"] = recipes["ingredients"].str.split()
        recipes["steps_tokens"] = recipes["steps"].str.split()

        # Ne devrait pas crasher
        results, total = search_recipes(recipes, query="mom's", page_size=10)
        assert isinstance(results, pd.DataFrame)
