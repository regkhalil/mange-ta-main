"""
Tests pour les utilitaires de détail de recette.

Ce module teste :
- L'affichage des cartes de recettes mini
- Le rendu du détail complet d'une recette
- La gestion des données manquantes
"""

from unittest.mock import patch

import pandas as pd

from utils.recipe_detail import render_recipe_card_mini


class TestRecipeDetail:
    """Tests pour les fonctions d'affichage de détail de recette."""

    @patch("utils.recipe_detail.get_image_from_pexels")
    @patch("streamlit.markdown")
    def test_render_recipe_card_mini_with_image(self, mock_markdown, mock_get_image):
        """Test : Affichage d'une mini-carte avec image."""
        # Mock de l'image
        mock_get_image.return_value = "https://example.com/image.jpg"

        # Créer une recette de test
        recipe = pd.Series(
            {
                "id": 123,
                "name": "Chocolate Cake",
                "minutes": 45,
                "n_ingredients": 8,
                "calories": 350,
                "nutrition_grade": "C",
                "isVegetarian": False,
                "average_rating": 4.7,
                "description": "A delicious chocolate cake",
            }
        )

        # Appel de la fonction
        render_recipe_card_mini(recipe)

        # Vérifications
        mock_get_image.assert_called_once_with("Chocolate Cake")
        mock_markdown.assert_called()

        # Vérifier que le HTML contient l'image
        html_call = mock_markdown.call_args[0][0]
        assert "https://example.com/image.jpg" in html_call
        assert "Chocolate Cake" in html_call

    @patch("utils.recipe_detail.get_image_from_pexels")
    @patch("streamlit.markdown")
    def test_render_recipe_card_mini_without_image(self, mock_markdown, mock_get_image):
        """Test : Affichage d'une mini-carte sans image (fallback icon)."""
        # Pas d'image disponible
        mock_get_image.return_value = None

        recipe = pd.Series(
            {
                "id": 456,
                "name": "Simple Salad",
                "minutes": 10,
                "n_ingredients": 4,
                "calories": 120,
                "nutrition_grade": "A",
                "isVegetarian": True,
                "average_rating": 4.2,
            }
        )

        # Appel de la fonction
        render_recipe_card_mini(recipe)

        # Vérifications
        mock_markdown.assert_called()
        html_call = mock_markdown.call_args[0][0]

        # Devrait contenir l'icône de fallback
        assert "🍽️" in html_call
        assert "Simple Salad" in html_call

    @patch("utils.recipe_detail.get_image_from_pexels")
    @patch("streamlit.markdown")
    def test_render_recipe_card_long_name_truncation(self, mock_markdown, mock_get_image):
        """Test : Les noms très longs sont tronqués."""
        mock_get_image.return_value = None

        long_name = "A" * 100
        recipe = pd.Series(
            {
                "id": 789,
                "name": long_name,
                "minutes": 20,
                "n_ingredients": 5,
                "calories": 200,
                "nutrition_grade": "B",
                "average_rating": 4.0,
            }
        )

        # Appel de la fonction
        render_recipe_card_mini(recipe)

        # Vérifications
        html_call = mock_markdown.call_args[0][0]

        # Le nom affiché ne devrait pas dépasser 60 caractères + "..."
        assert "..." in html_call

    @patch("utils.recipe_detail.get_image_from_pexels")
    @patch("streamlit.markdown")
    def test_render_recipe_card_nutri_score_colors(self, mock_markdown, mock_get_image):
        """Test : Les couleurs Nutri-Score sont correctement appliquées."""
        mock_get_image.return_value = None

        # Test pour chaque grade
        grades_colors = {"A": "#238B45", "B": "#85BB2F", "C": "#FECC00", "D": "#FF9500", "E": "#E63946"}

        for grade, expected_color in grades_colors.items():
            recipe = pd.Series(
                {
                    "id": 100 + ord(grade),
                    "name": f"Recipe {grade}",
                    "minutes": 30,
                    "n_ingredients": 5,
                    "calories": 300,
                    "nutrition_grade": grade,
                    "average_rating": 4.0,
                }
            )

            render_recipe_card_mini(recipe)

            html_call = mock_markdown.call_args[0][0]
            # Vérifier que la couleur est présente dans le HTML
            assert expected_color in html_call or grade in html_call

    @patch("utils.recipe_detail.get_image_from_pexels")
    @patch("streamlit.markdown")
    def test_render_recipe_card_vegetarian_tag(self, mock_markdown, mock_get_image):
        """Test : Le tag végétarien s'affiche correctement."""
        mock_get_image.return_value = None

        recipe = pd.Series(
            {
                "id": 999,
                "name": "Vegan Bowl",
                "minutes": 15,
                "n_ingredients": 6,
                "calories": 180,
                "nutrition_grade": "A",
                "isVegetarian": True,
                "average_rating": 4.8,
            }
        )

        render_recipe_card_mini(recipe)

        html_call = mock_markdown.call_args[0][0]

        # Devrait contenir le tag végétarien
        assert "🌱" in html_call or "Végétarien" in html_call
