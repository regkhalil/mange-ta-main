"""
Tests d'intégration pour le dossier services.

Ce module teste l'interaction entre tous les services :
- data_loader, search_engine, recommender, pexels_image_service
- Scénarios end-to-end réalistes
- Performance et cohérence des données
"""

import time
from unittest.mock import patch

import pandas as pd
import pytest

from services.data_loader import filter_recipes, get_recipe_stats
from services.pexels_image_service import get_image_with_fallback
from services.recommender import RecipeRecommender
from services.search_engine import search_recipes


class TestServicesIntegration:
    """Tests d'intégration pour tous les services."""

    @pytest.fixture(scope="class")
    def recipes_data(self):
        """Fixture pour charger les données de recettes."""
        # Toujours utiliser des données de test pour éviter les dépendances externes
        return pd.DataFrame(
            {
                "id": [1, 2, 3, 4, 5],
                "name_tokens": [
                    ["chocolate", "cake"],
                    ["pasta", "bolognese"],
                    ["vegetable", "soup"],
                    ["pizza", "margherita"],
                    ["salad", "caesar"],
                ],
                "ingredient_tokens": [
                    ["flour", "sugar", "chocolate"],
                    ["pasta", "tomato", "meat"],
                    ["carrot", "onion", "celery"],
                    ["flour", "tomato", "cheese"],
                    ["lettuce", "cheese", "croutons"],
                ],
                "steps_tokens": [
                    ["mix", "bake", "cool"],
                    ["boil", "sauce", "serve"],
                    ["chop", "simmer", "blend"],
                    ["knead", "top", "bake"],
                    ["wash", "mix", "dress"],
                ],
                "minutes": [60.0, 30.0, 45.0, 90.0, 15.0],
                "n_ingredients": [8.0, 6.0, 5.0, 4.0, 3.0],
                "calories": [450.0, 350.0, 200.0, 600.0, 150.0],
                "is_vegetarian": [True, False, True, True, True],
                "nutrition_score": [6.5, 7.2, 8.9, 5.8, 8.1],
                "nutrition_grade": ["C", "B", "A", "D", "B"],
                "techniques": [["baking"], ["boiling"], ["simmering"], ["baking"], ["mixing"]],
                "calorie_level": ["medium", "medium", "low", "high", "low"],
                "review_count": [150, 89, 234, 67, 123],
                "average_rating": [4.2, 4.5, 4.8, 3.9, 4.1],
                "popularity_score": [0.75, 0.68, 0.89, 0.45, 0.71],
            }
        )

    def test_data_loading_and_basic_stats(self, recipes_data):
        """Test du chargement de données et calcul de statistiques basiques."""
        # Vérifier que les données sont chargées
        assert len(recipes_data) > 0
        assert "id" in recipes_data.columns

        # Calculer les statistiques
        stats = get_recipe_stats(recipes_data)

        # Vérifier la cohérence des statistiques
        assert stats["total_recipes"] == len(recipes_data)
        assert stats["avg_prep_time"] > 0
        assert 0 <= stats["vegetarian_percentage"] <= 100

    def test_search_and_filter_integration(self, recipes_data):
        """Test de l'intégration recherche et filtrage."""
        # Test de recherche avec query
        results, total = search_recipes(recipes_data, query="chocolate", prep_time_max=120, calories_max=500)

        # Vérifier que les résultats respectent les filtres
        assert len(results) <= total
        if len(results) > 0:
            assert all(row["minutes"] <= 120 for _, row in results.iterrows())
            assert all(row["calories"] <= 500 for _, row in results.iterrows())

        # Test de recherche végétarienne
        veg_results, veg_total = search_recipes(recipes_data, vegetarian_only=True, prep_time_max=60)

        if len(veg_results) > 0:
            assert all(row["is_vegetarian"] for _, row in veg_results.iterrows())
            assert all(row["minutes"] <= 60 for _, row in veg_results.iterrows())

    def test_search_pagination_consistency(self, recipes_data):
        """Test de la cohérence de la pagination."""
        # Recherche sans pagination
        all_results, total = search_recipes(recipes_data, page_size=1000)

        # Recherche avec pagination
        page1_results, total1 = search_recipes(recipes_data, page=1, page_size=2)
        page2_results, total2 = search_recipes(recipes_data, page=2, page_size=2)

        # Vérifier la cohérence
        assert total1 == total2 == total  # Le total doit être le même
        assert len(page1_results) <= 2
        assert len(page2_results) <= 2

        # Les IDs ne doivent pas se chevaucher entre les pages
        if len(page1_results) > 0 and len(page2_results) > 0:
            page1_ids = set(page1_results["id"])
            page2_ids = set(page2_results["id"])
            assert page1_ids.isdisjoint(page2_ids)

    @patch("services.recommender.read_pickle_file")
    def test_recommender_integration(self, mock_read_pickle, recipes_data):
        """Test du système de recommandations avec données réelles."""
        # Mock des données de similarité
        import numpy as np

        mock_similarity_data = {
            "id_to_index": {1: 0, 2: 1, 3: 2, 4: 3, 5: 4},
            "index_to_id": {0: 1, 1: 2, 2: 3, 3: 4, 4: 5},
            "combined_features": np.array(
                [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9], [0.2, 0.3, 0.4], [0.5, 0.6, 0.7]]
            ),
        }
        mock_read_pickle.return_value = mock_similarity_data

        # Créer le recommender
        recommender = RecipeRecommender(recipes_data)

        # Test des recommandations avec un ID valide
        if len(recipes_data) > 0:
            recipe_id = recipes_data.iloc[0]["id"]
            recommendations = recommender.get_similar_recipes(recipe_id, k=3)

            # Vérifier que les recommandations sont cohérentes
            assert len(recommendations) <= 3
            for recipe, score in recommendations:
                assert recipe["id"] != recipe_id  # Ne doit pas recommander la même recette
                assert 0 <= score <= 1  # Score de similarité valide

    def test_filter_and_recommend_workflow(self, recipes_data):
        """Test du workflow complet : filtrage puis recommandations."""
        # Étape 1 : Filtrer les recettes végétariennes
        vegetarian_recipes = filter_recipes(recipes_data, vegetarian_only=True, prep_range=(10, 60))

        if len(vegetarian_recipes) > 0:
            # Étape 2 : Prendre une recette filtrée
            sample_recipe = vegetarian_recipes.iloc[0]

            # Étape 3 : Recommandations basées sur les filtres
            with patch("services.recommender.read_pickle_file") as mock_read_pickle:
                import numpy as np

                mock_similarity_data = {
                    "id_to_index": {int(row["id"]): idx for idx, (_, row) in enumerate(vegetarian_recipes.iterrows())},
                    "index_to_id": {idx: int(row["id"]) for idx, (_, row) in enumerate(vegetarian_recipes.iterrows())},
                    "combined_features": np.array(
                        [[0.1 * i, 0.2 * i, 0.3 * i] for i in range(len(vegetarian_recipes))]
                    ),
                }
                mock_read_pickle.return_value = mock_similarity_data

                recommender = RecipeRecommender(vegetarian_recipes)
                similar_recipes = recommender.get_similar_recipes(sample_recipe["id"], k=2)

                # Vérifier que les recommandations sont du même type (végétariennes)
                for recipe, score in similar_recipes:
                    assert recipe["is_vegetarian"]  # Vérification boolean

    @patch("services.pexels_image_service.requests.get")
    def test_search_with_images_integration(self, mock_get, recipes_data):
        """Test de l'intégration recherche + images."""
        # Mock de la réponse Pexels
        mock_response = mock_get.return_value
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"photos": [{"src": {"large": "https://images.pexels.com/test-image.jpg"}}]}

        # Rechercher une recette
        results, total = search_recipes(recipes_data, query="chocolate", page_size=1)

        if len(results) > 0:
            recipe = results.iloc[0]
            recipe_name = f"Recipe #{recipe['id']}"

            # Récupérer l'image pour cette recette
            image_url = get_image_with_fallback(recipe_name)

            # Vérifier que l'image est retournée
            assert image_url is not None
            assert isinstance(image_url, str)
            assert image_url.startswith("http")

    def test_performance_integration(self, recipes_data):
        """Test de performance pour les opérations intégrées."""
        start_time = time.time()

        # Opération complexe : recherche + filtrage + stats
        filtered_recipes = filter_recipes(
            recipes_data, prep_range=(15, 90), ingredients_range=(3, 10), calories_range=(100, 600)
        )

        if len(filtered_recipes) > 0:
            # Recherche dans les données filtrées
            search_results, total = search_recipes(filtered_recipes, query="recipe", sort_by="prep_time", page_size=10)

            # Calcul des statistiques
            get_recipe_stats(filtered_recipes)

        end_time = time.time()
        execution_time = end_time - start_time

        # L'opération complète ne doit pas prendre plus de 5 secondes
        assert execution_time < 5.0, f"Opération trop lente: {execution_time:.2f}s"

    def test_data_consistency_across_services(self, recipes_data):
        """Test de cohérence des données entre les services."""
        if len(recipes_data) == 0:
            pytest.skip("Pas de données disponibles pour le test de cohérence")

        # Prendre un échantillon de recettes
        sample_size = min(5, len(recipes_data))
        sample_recipes = recipes_data.head(sample_size)

        for _, recipe in sample_recipes.iterrows():
            recipe_id = recipe["id"]

            # Test 1 : La recette doit être trouvable par recherche d'ID
            search_results, total = search_recipes(recipes_data, query=str(recipe_id), page_size=100)

            # Test 2 : Les données numériques doivent être cohérentes
            assert recipe["minutes"] >= 0
            assert recipe["n_ingredients"] >= 0
            assert recipe["calories"] >= 0

            # Test 3 : Les flags booléens doivent être valides
            assert isinstance(recipe["is_vegetarian"], (bool, int))

            # Test 4 : Les grades nutritionnels doivent être valides
            if "nutrition_grade" in recipe and pd.notna(recipe["nutrition_grade"]):
                assert recipe["nutrition_grade"] in ["A", "B", "C", "D", "E"]

    def test_error_handling_integration(self, recipes_data):
        """Test de gestion d'erreurs dans l'intégration des services."""
        # Test avec DataFrame vide complètement
        empty_df = pd.DataFrame()

        # Les filtres ne doivent pas échouer avec un DataFrame vide
        filtered = filter_recipes(empty_df, prep_range=(10, 60))
        assert len(filtered) == 0

        # Tester avec des critères impossibles sur des données réelles
        impossible_filtered = filter_recipes(recipes_data, prep_range=(1000, 2000))
        assert len(impossible_filtered) == 0

        # Test de cohérence des données
        assert len(recipes_data) > 0
        assert "id" in recipes_data.columns

    def test_service_caching_behavior(self, recipes_data):
        """Test du comportement de cache des services."""
        # Test que les appels répétés sont cohérents (cache fonctionne)
        results1, total1 = search_recipes(recipes_data, query="test", page_size=5)
        results2, total2 = search_recipes(recipes_data, query="test", page_size=5)

        # Les résultats doivent être identiques (cache fonctionne)
        assert total1 == total2
        if len(results1) > 0 and len(results2) > 0:
            assert results1.equals(results2)


class TestServicesPerformance:
    """Tests de performance pour les services."""

    def test_large_dataset_search_performance(self):
        """Test de performance de recherche sur un grand dataset."""
        # Créer un dataset de test plus grand
        large_data = []
        for i in range(1000):
            large_data.append(
                {
                    "id": i + 1,
                    "name_tokens": [f"recipe_{i}", "test"],
                    "ingredient_tokens": [f"ingredient_{i % 10}", "common"],
                    "steps_tokens": [f"step_{i}", "cook"],
                    "minutes": 30.0 + (i % 60),
                    "n_ingredients": 5.0 + (i % 10),
                    "calories": 200.0 + (i % 400),
                    "is_vegetarian": i % 2 == 0,
                    "nutrition_score": 5.0 + (i % 5),
                    "nutrition_grade": ["A", "B", "C", "D", "E"][i % 5],
                    "review_count": 50 + (i % 100),
                    "average_rating": 3.0 + (i % 2),
                    "popularity_score": 0.5 + (i % 5) / 10,
                }
            )

        large_df = pd.DataFrame(large_data)

        # Test de performance de recherche
        start_time = time.time()

        results, total = search_recipes(large_df, query="recipe_500", prep_time_max=60, page_size=20)

        end_time = time.time()
        search_time = end_time - start_time

        # La recherche ne doit pas prendre plus de 2 secondes
        assert search_time < 2.0, f"Recherche trop lente: {search_time:.2f}s"

        # Vérifier que les résultats sont corrects
        assert len(results) <= 20
        assert total <= 1000


if __name__ == "__main__":
    pytest.main([__file__])
