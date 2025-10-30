"""
Tests pour les composants UI du package components.
"""

import unittest
from unittest.mock import Mock, patch

import pandas as pd

# Import des fonctions à tester
from components.filters_panel import render_filters_panel
from components.metrics_header import render_metrics_header
from components.nutri_score import (
    display_nutri_score_badge,
    display_nutri_score_scale,
    get_nutri_color,
    get_nutri_grade,
    render_nutri_score_in_card,
)


class TestFiltersPanel(unittest.TestCase):
    """Tests pour le composant filters_panel"""

    @patch("components.filters_panel.st")
    def test_render_filters_panel_sidebar(self, mock_st):
        """Test du rendu des filtres en sidebar"""
        # Mock session state avec dictionnaire normal
        session_state_mock = {}
        mock_st.session_state = session_state_mock

        # Mock widgets pour sidebar
        mock_st.sidebar.slider.side_effect = [
            (10, 30),  # prep_range
            (3, 8),  # ing_range
            (200, 600),  # cal_range
        ]
        mock_st.sidebar.multiselect.return_value = ["A", "B"]
        mock_st.sidebar.checkbox.return_value = True

        result = render_filters_panel(in_sidebar=True)

        # Vérifier la structure du résultat
        self.assertIsInstance(result, dict)
        self.assertIn("prep", result)
        self.assertIn("ingredients", result)
        self.assertIn("calories", result)
        self.assertIn("vegetarian_only", result)
        self.assertIn("nutrition_grades", result)

        # Vérifier les valeurs
        self.assertEqual(result["prep"], [10, 30])
        self.assertEqual(result["ingredients"], [3, 8])
        self.assertEqual(result["calories"], [200, 600])
        self.assertTrue(result["vegetarian_only"])
        self.assertEqual(result["nutrition_grades"], ["A", "B"])

        # Vérifier que filter_key_suffix a été initialisé
        self.assertIn("filter_key_suffix", session_state_mock)
        self.assertEqual(session_state_mock["filter_key_suffix"], 0)


class TestMetricsHeader(unittest.TestCase):
    """Tests pour le composant metrics_header"""

    @patch("components.metrics_header.st")
    def test_render_metrics_header_complete_stats(self, mock_st):
        """Test du rendu des métriques avec stats complètes"""
        # Mock columns
        col1_mock = Mock()
        col2_mock = Mock()
        col3_mock = Mock()
        col4_mock = Mock()
        mock_st.columns.return_value = (col1_mock, col2_mock, col3_mock, col4_mock)

        stats = {"total_recipes": 1000, "median_prep_time": 25.5, "avg_calories": 450.2, "vegetarian_percentage": 35.7}

        render_metrics_header(stats)

        # Vérifier la création des colonnes
        mock_st.columns.assert_called_once_with(4)

        # Vérifier les appels metric
        col1_mock.metric.assert_called_once_with(label="📚 Recettes totales", value="1,000")
        col2_mock.metric.assert_called_once_with(label="⏱️ Temps médian", value="26 min")
        col3_mock.metric.assert_called_once_with(label="🔥 Calories moyennes", value="450 kcal")
        col4_mock.metric.assert_called_once_with(label="🌱 Végétarien", value="35.7%")


class TestNutriScore(unittest.TestCase):
    """Tests pour le composant nutri_score"""

    def test_get_nutri_grade_a(self):
        """Test grade A (85-98)"""
        self.assertEqual(get_nutri_grade(95.0), "A")
        self.assertEqual(get_nutri_grade(85.0), "A")
        self.assertEqual(get_nutri_grade(98.0), "A")

    def test_get_nutri_grade_b(self):
        """Test grade B (70-84)"""
        self.assertEqual(get_nutri_grade(75.0), "B")
        self.assertEqual(get_nutri_grade(70.0), "B")
        self.assertEqual(get_nutri_grade(84.9), "B")

    def test_get_nutri_grade_c(self):
        """Test grade C (55-69)"""
        self.assertEqual(get_nutri_grade(60.0), "C")
        self.assertEqual(get_nutri_grade(55.0), "C")
        self.assertEqual(get_nutri_grade(69.9), "C")

    def test_get_nutri_grade_d(self):
        """Test grade D (40-54)"""
        self.assertEqual(get_nutri_grade(45.0), "D")
        self.assertEqual(get_nutri_grade(40.0), "D")
        self.assertEqual(get_nutri_grade(54.9), "D")

    def test_get_nutri_grade_e(self):
        """Test grade E (0-39)"""
        self.assertEqual(get_nutri_grade(30.0), "E")
        self.assertEqual(get_nutri_grade(10.0), "E")
        self.assertEqual(get_nutri_grade(39.9), "E")

    def test_get_nutri_grade_nan(self):
        """Test avec valeur NaN"""
        self.assertEqual(get_nutri_grade(float("nan")), "C")
        self.assertEqual(get_nutri_grade(pd.NA), "C")

    def test_get_nutri_grade_none(self):
        """Test avec valeur None"""
        self.assertEqual(get_nutri_grade(None), "C")

    def test_get_nutri_color_all_grades(self):
        """Test des couleurs pour tous les grades"""
        self.assertEqual(get_nutri_color("A"), "#238B45")
        self.assertEqual(get_nutri_color("B"), "#85BB2F")
        self.assertEqual(get_nutri_color("C"), "#FECC00")
        self.assertEqual(get_nutri_color("D"), "#FF9500")
        self.assertEqual(get_nutri_color("E"), "#E63946")

    def test_get_nutri_color_invalid_grade(self):
        """Test avec grade invalide"""
        self.assertEqual(get_nutri_color("X"), "#7f8c8d")
        self.assertEqual(get_nutri_color(""), "#7f8c8d")
        self.assertEqual(get_nutri_color(None), "#7f8c8d")

    def test_display_nutri_score_badge(self):
        """Test de l'affichage du badge"""
        badge_html = display_nutri_score_badge("A")
        self.assertIsInstance(badge_html, str)
        self.assertIn("A", badge_html)
        self.assertIn("#238B45", badge_html)

    def test_display_nutri_score_scale(self):
        """Test de l'affichage de l'échelle"""
        scale_html = display_nutri_score_scale()
        self.assertIsInstance(scale_html, str)

        # Vérifier que toutes les couleurs sont présentes
        colors = ["#238B45", "#85BB2F", "#FECC00", "#FF9500", "#E63946"]
        for color in colors:
            self.assertIn(color, scale_html)

    def test_render_nutri_score_in_card(self):
        """Test du rendu dans une carte"""
        # Test avec score
        card_with_score = render_nutri_score_in_card("A", 88.5)
        self.assertIn("A", card_with_score)
        self.assertIn("#238B45", card_with_score)
        self.assertIn("88", card_with_score)  # Score arrondi

        # Test sans score
        card_without_score = render_nutri_score_in_card("B")
        self.assertIn("B", card_without_score)
        self.assertIn("#85BB2F", card_without_score)

    def test_nutri_score_integration(self):
        """Test d'intégration entre les fonctions Nutri-Score"""
        # Test du workflow complet avec scores réels
        nutrition_scores = [95.0, 75.0, 60.0, 45.0, 25.0, float("nan")]

        grades = [get_nutri_grade(score) for score in nutrition_scores]
        expected_grades = ["A", "B", "C", "D", "E", "C"]

        self.assertEqual(grades, expected_grades)

        # Tester les couleurs correspondantes
        colors = [get_nutri_color(grade) for grade in grades]
        self.assertEqual(len(colors), len(grades))
        self.assertIn("#238B45", colors)  # A
        self.assertIn("#85BB2F", colors)  # B


if __name__ == "__main__":
    unittest.main()
