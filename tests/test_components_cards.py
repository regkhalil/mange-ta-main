"""
Tests pour les composants recipe_card et ui_enhanced.
"""

import unittest
from unittest.mock import Mock, patch

import pandas as pd


class TestRecipeCard(unittest.TestCase):
    """Tests pour le composant recipe_card"""

    def setUp(self):
        """Configuration des données de test"""
        self.sample_recipe = pd.Series(
            {
                "id": 123,
                "name": "Salade César aux Crevettes",
                "description": "Une délicieuse salade fraîche avec des crevettes",
                "prep_time": 25,
                "cook_time": 10,
                "total_time": 35,
                "calories": 350,
                "ingredients_count": 8,
                "nutrition_grade": "B",
                "nutrition_score": 75.5,
                "vegetarian": False,
                "rating": 4.5,
                "rating_count": 150,
                "image_url": "https://example.com/image.jpg",
            }
        )

    @patch("components.recipe_card.st")
    def test_render_recipe_card_basic(self, mock_st):
        """Test du rendu de base d'une carte de recette"""
        from components.recipe_card import render_recipe_card

        # Mock container et markdown
        mock_container = Mock()
        mock_st.container.return_value.__enter__ = Mock(return_value=mock_container)
        mock_st.container.return_value.__exit__ = Mock(return_value=None)
        mock_st.markdown = Mock()

        # Mock columns (recipe_card utilise 3 colonnes)
        col1, col2, col3 = Mock(), Mock(), Mock()
        mock_st.columns = Mock(return_value=(col1, col2, col3))

        # Mock autres éléments streamlit potentiels
        mock_st.metric = Mock()
        mock_st.write = Mock()

        # Exécuter la fonction
        render_recipe_card(self.sample_recipe)

        # Vérifications
        mock_st.container.assert_called_once()
        mock_st.markdown.assert_called()
        mock_st.columns.assert_called_with(3)

    @patch("components.recipe_card.st")
    def test_render_recipe_card_with_similarity(self, mock_st):
        """Test du rendu avec score de similarité"""
        from components.recipe_card import render_recipe_card

        # Mock container
        mock_st.container.return_value.__enter__ = Mock(return_value=Mock())
        mock_st.container.return_value.__exit__ = Mock(return_value=None)
        mock_st.markdown = Mock()
        mock_st.columns = Mock(return_value=(Mock(), Mock(), Mock()))

        # Exécuter avec similarité
        render_recipe_card(self.sample_recipe, show_similarity=True, similarity_score=0.85)

        # Vérifier l'appel
        mock_st.container.assert_called_once()
        mock_st.markdown.assert_called()
        mock_st.columns.assert_called_with(3)

    @patch("components.recipe_card.st")
    def test_render_recipe_card_long_name(self, mock_st):
        """Test avec nom de recette très long"""
        from components.recipe_card import render_recipe_card

        # Mock setup
        mock_st.container.return_value.__enter__ = Mock(return_value=Mock())
        mock_st.container.return_value.__exit__ = Mock(return_value=None)
        mock_st.markdown = Mock()
        mock_st.columns = Mock(return_value=(Mock(), Mock(), Mock()))

        # Recette avec nom très long
        long_name_recipe = self.sample_recipe.copy()
        long_name_recipe["name"] = "A" * 100  # Nom très long

        # Exécuter
        render_recipe_card(long_name_recipe)

        # Vérifier que ça fonctionne
        mock_st.markdown.assert_called()
        mock_st.columns.assert_called_with(3)

    @patch("components.recipe_card.st")
    def test_render_recipe_card_missing_data(self, mock_st):
        """Test avec données manquantes"""
        from components.recipe_card import render_recipe_card

        # Mock setup
        mock_st.container.return_value.__enter__ = Mock(return_value=Mock())
        mock_st.container.return_value.__exit__ = Mock(return_value=None)
        mock_st.markdown = Mock()
        mock_st.columns = Mock(return_value=(Mock(), Mock(), Mock()))

        # Recette avec données minimales
        minimal_recipe = pd.Series(
            {
                "id": 456,
                # name manquant volontairement
            }
        )

        # Doit fonctionner sans erreur
        render_recipe_card(minimal_recipe)

        # Vérifier l'appel
        mock_st.container.assert_called_once()
        mock_st.markdown.assert_called()
        mock_st.columns.assert_called_with(3)


class TestUIEnhanced(unittest.TestCase):
    """Tests pour le composant ui_enhanced"""

    def setUp(self):
        """Configuration des données de test"""
        self.sample_recipe = pd.Series(
            {
                "id": 789,
                "name": "Tarte aux Pommes Traditionnelle",
                "description": "Une tarte aux pommes faite maison avec de la cannelle",
                "prep_time": 45,
                "cook_time": 60,
                "total_time": 105,
                "calories": 280,
                "ingredients_count": 12,
                "nutrition_grade": "C",
                "nutrition_score": 65.0,
                "vegetarian": True,
                "rating": 4.8,
                "rating_count": 234,
                "image_url": "https://example.com/tarte.jpg",
            }
        )

    @patch("components.ui_enhanced.st")
    @patch("components.ui_enhanced.format_recipe_title")
    @patch("components.ui_enhanced.format_description")
    def test_render_recipe_card_enhanced_basic(self, mock_format_desc, mock_format_title, mock_st):
        """Test du rendu de carte améliorée"""
        from components.ui_enhanced import render_recipe_card_enhanced

        # Mock les fonctions de formatage
        mock_format_title.return_value = "Tarte aux Pommes"
        mock_format_desc.return_value = "Une délicieuse tarte..."

        # Mock container avec context manager
        mock_container = Mock()
        mock_st.container.return_value.__enter__ = Mock(return_value=mock_container)
        mock_st.container.return_value.__exit__ = Mock(return_value=None)

        # Mock colonnes avec context managers - première fois: 2 colonnes, puis 4 colonnes
        class MockColumn:
            def __init__(self):
                self.button = Mock(return_value=False)

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        # Les colonnes avec context managers
        mock_columns_2 = (MockColumn(), MockColumn())
        mock_columns_4 = (MockColumn(), MockColumn(), MockColumn(), MockColumn())

        # Appels successifs de st.columns
        mock_st.columns = Mock(side_effect=[mock_columns_2, mock_columns_4])

        # Exécuter la fonction
        render_recipe_card_enhanced(self.sample_recipe)

        # Vérifications
        mock_st.container.assert_called()
        mock_format_title.assert_called_once_with(self.sample_recipe)
        mock_format_desc.assert_called_once()
        # Vérifier que columns a été appelé 2 fois (une fois avec 2 colonnes, une fois avec 4)
        self.assertEqual(mock_st.columns.call_count, 2)

    @patch("components.ui_enhanced.st")
    @patch("components.ui_enhanced.format_recipe_title")
    @patch("components.ui_enhanced.format_description")
    def test_render_recipe_card_enhanced_without_button(self, mock_format_desc, mock_format_title, mock_st):
        """Test sans bouton similaire"""
        from components.ui_enhanced import render_recipe_card_enhanced

        # Mock les fonctions
        mock_format_title.return_value = "Tarte aux Pommes"
        mock_format_desc.return_value = "Une délicieuse tarte..."

        # Mock container avec context manager
        mock_st.container.return_value.__enter__ = Mock(return_value=Mock())
        mock_st.container.return_value.__exit__ = Mock(return_value=None)

        # Mock colonnes avec context managers
        class MockColumn:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        mock_st.columns = Mock(
            side_effect=[
                (MockColumn(), MockColumn()),  # Première fois: 2 colonnes
                (MockColumn(), MockColumn(), MockColumn(), MockColumn()),  # Deuxième fois: 4 colonnes
            ]
        )

        # Exécuter sans bouton
        render_recipe_card_enhanced(self.sample_recipe, show_similar_button=False)

        # Vérifications de base
        mock_st.container.assert_called()

    @patch("components.ui_enhanced.st")
    @patch("components.ui_enhanced.format_recipe_title")
    @patch("components.ui_enhanced.format_description")
    def test_render_recipe_card_enhanced_grade_colors(self, mock_format_desc, mock_format_title, mock_st):
        """Test des couleurs de grades"""
        from components.ui_enhanced import render_recipe_card_enhanced

        # Mock setup minimal
        mock_format_title.return_value = "Test Recipe"
        mock_format_desc.return_value = "Test description"
        mock_st.container.return_value.__enter__ = Mock(return_value=Mock())
        mock_st.container.return_value.__exit__ = Mock(return_value=None)

        # Mock colonnes avec context managers
        class MockColumn:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

        # Préparer les réponses pour st.columns (2 appels par test * 5 tests = 10 appels)
        column_responses = []
        for _ in range(5):  # 5 grades
            column_responses.append((MockColumn(), MockColumn()))  # Premier appel: 2 colonnes
            column_responses.append((MockColumn(), MockColumn(), MockColumn(), MockColumn()))  # Deuxième: 4 colonnes

        mock_st.columns = Mock(side_effect=column_responses)

        # Tester avec différents grades
        for grade in ["A", "B", "C", "D", "E"]:
            recipe_with_grade = self.sample_recipe.copy()
            recipe_with_grade["nutrition_grade"] = grade

            # Doit fonctionner sans erreur
            render_recipe_card_enhanced(recipe_with_grade)

        # Vérifier que container a été appelé pour chaque grade
        self.assertEqual(mock_st.container.call_count, 5)


if __name__ == "__main__":
    unittest.main()
