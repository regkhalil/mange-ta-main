"""
Tests unitaires pour les composants UI Streamlit.

Ce module teste tous les composants UI :
- filters_panel.py - Panneau de filtres
- metrics_header.py - En-tête de métriques
- nutri_score.py - Nutri-Score
- recipe_card.py - Cartes de recettes
- ui_enhanced.py - UI améliorée
"""

import unittest
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pandas as pd
import pytest

from components.filters_panel import render_filters_panel
from components.metrics_header import render_metrics_header
from components.nutri_score import (
    display_nutri_score_badge,
    display_nutri_score_scale,
    get_nutri_color,
    get_nutri_grade,
    render_nutri_score_in_card,
)


class TestFiltersPanel:
    """Tests pour le panneau de filtres."""

    @patch("components.filters_panel.st")
    def test_render_filters_panel_sidebar(self, mock_st):
        """Test du rendu des filtres en sidebar"""
        # Mock session state avec session_state normal
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

        # Vérifier que st.sidebar a été utilisé
        mock_st.sidebar.header.assert_called_once_with("Filtres")
        self.assertEqual(mock_st.sidebar.slider.call_count, 3)
        mock_st.sidebar.multiselect.assert_called_once()
        mock_st.sidebar.checkbox.assert_called_once()

        # Vérifier que filter_key_suffix a été initialisé
        self.assertIn("filter_key_suffix", session_state_mock)
        self.assertEqual(session_state_mock["filter_key_suffix"], 0)

    @patch("components.filters_panel.st")
    def test_render_filters_panel_main_page(self, mock_st):
        """Test du rendu des filtres dans la page principale"""
        # Mock session state avec session_state normal
        session_state_mock = {}
        mock_st.session_state = session_state_mock

        # Mock columns pour layout
        col1_mock = Mock()
        col2_mock = Mock()
        mock_st.columns.return_value = (col1_mock, col2_mock)

        # Mock widgets pour page principale
        col1_mock.slider.side_effect = [(10, 30), (3, 8)]  # prep et ingredients
        col2_mock.slider.return_value = (200, 600)  # calories
        col2_mock.multiselect.return_value = ["C", "D"]
        col2_mock.checkbox.return_value = False

        result = render_filters_panel(in_sidebar=False)

        # Vérifier la structure du résultat
        self.assertIsInstance(result, dict)
        self.assertEqual(result["prep"], [10, 30])
        self.assertEqual(result["ingredients"], [3, 8])
        self.assertEqual(result["calories"], [200, 600])
        self.assertFalse(result["vegetarian_only"])
        self.assertEqual(result["nutrition_grades"], ["C", "D"])

        # Vérifier que les colonnes ont été créées
        mock_st.columns.assert_called_once_with(2)

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

        # Vérifier que le CSS est ajouté
        mock_st.markdown.assert_called()

    @patch("components.metrics_header.st")
    def test_render_metrics_header_missing_stats(self, mock_st):
        """Test du rendu avec des statistiques manquantes."""
        # Données de test avec valeurs manquantes
        stats = {
            "total_recipes": 1500,
            # median_prep_time manquant
            "avg_calories": 350.5,
            # vegetarian_percentage manquant
        }

        # Mock des widgets Streamlit
        mock_st.columns = MagicMock(return_value=[MagicMock(), MagicMock(), MagicMock(), MagicMock()])
        mock_st.markdown = MagicMock()

        # Mock pour les colonnes
        mock_cols = [MagicMock() for _ in range(4)]
        for col in mock_cols:
            col.metric = MagicMock()
        mock_st.columns.return_value = mock_cols

        # Exécuter la fonction - ne doit pas lever d'erreur
        render_metrics_header(stats)

        # Vérifier que les valeurs par défaut (0) sont utilisées
        for col in mock_cols:
            col.metric.assert_called_once()

    @patch("components.metrics_header.st")
    def test_render_metrics_header_empty_stats(self, mock_st):
        """Test du rendu avec un dictionnaire vide."""
        stats = {}

        # Mock des widgets Streamlit
        mock_st.columns = MagicMock(return_value=[MagicMock(), MagicMock(), MagicMock(), MagicMock()])
        mock_st.markdown = MagicMock()

        # Mock pour les colonnes
        mock_cols = [MagicMock() for _ in range(4)]
        for col in mock_cols:
            col.metric = MagicMock()
        mock_st.columns.return_value = mock_cols

        # Exécuter la fonction
        render_metrics_header(stats)

        # Vérifier que les valeurs par défaut sont utilisées
        for col in mock_cols:
            col.metric.assert_called_once()


class TestNutriScore(unittest.TestCase):
    """Tests pour le système Nutri-Score."""

    def test_get_nutri_grade_a(self):
        """Test du grade A (excellente nutrition)."""
        assert get_nutri_grade(95.0) == "A"
        assert get_nutri_grade(85.0) == "A"  # Limite inférieure

    def test_get_nutri_grade_b(self):
        """Test du grade B (bonne nutrition)."""
        assert get_nutri_grade(84.9) == "B"
        assert get_nutri_grade(75.0) == "B"
        assert get_nutri_grade(70.0) == "B"  # Limite inférieure

    def test_get_nutri_grade_c(self):
        """Test du grade C (acceptable)."""
        assert get_nutri_grade(69.9) == "C"
        assert get_nutri_grade(60.0) == "C"
        assert get_nutri_grade(55.0) == "C"  # Limite inférieure

    def test_get_nutri_grade_d(self):
        """Test du grade D (pauvre)."""
        assert get_nutri_grade(54.9) == "D"
        assert get_nutri_grade(45.0) == "D"
        assert get_nutri_grade(40.0) == "D"  # Limite inférieure

    def test_get_nutri_grade_e(self):
        """Test du grade E (très pauvre)."""
        assert get_nutri_grade(39.9) == "E"
        assert get_nutri_grade(25.0) == "E"
        assert get_nutri_grade(10.0) == "E"

    def test_get_nutri_grade_nan(self):
        """Test avec valeur NaN."""
        assert get_nutri_grade(float("nan")) == "C"
        assert get_nutri_grade(pd.NA) == "C"

    def test_get_nutri_grade_none(self):
        """Test avec valeur None."""
        # pd.isna(None) retourne True
        assert get_nutri_grade(None) == "C"

    def test_get_nutri_grade_edge_cases(self):
        """Test des cas limites."""
        assert get_nutri_grade(0.0) == "E"
        assert get_nutri_grade(100.0) == "A"
        assert get_nutri_grade(-5.0) == "E"
        assert get_nutri_grade(105.0) == "A"

    def test_get_nutri_color_all_grades(self):
        """Test des couleurs pour tous les grades."""
        assert get_nutri_color("A") == "#238B45"  # Vert foncé
        assert get_nutri_color("B") == "#85BB2F"  # Vert clair
        assert get_nutri_color("C") == "#FECC00"  # Jaune
        assert get_nutri_color("D") == "#FF9500"  # Orange
        assert get_nutri_color("E") == "#E63946"  # Rouge

    def test_get_nutri_color_invalid_grade(self):
        """Test avec grade invalide."""
        assert get_nutri_color("X") == "#7f8c8d"  # Gris par défaut (valeur réelle)
        assert get_nutri_color("") == "#7f8c8d"
        assert get_nutri_color(None) == "#7f8c8d"

    def test_get_nutri_color_lowercase(self):
        """Test avec grades en minuscules."""
        assert get_nutri_color("a") == "#7f8c8d"  # Doit être sensible à la casse
        assert get_nutri_color("b") == "#7f8c8d"

    def test_display_nutri_score_badge(self):
        """Test du badge Nutri-Score."""
        # Test avec différentes tailles
        badge_large = display_nutri_score_badge("A", "large")
        badge_medium = display_nutri_score_badge("B", "medium")
        badge_small = display_nutri_score_badge("C", "small")

        # Vérifier que le HTML contient les bonnes informations
        assert "A" in badge_large
        assert "#238B45" in badge_large  # Couleur du grade A
        assert "24px" in badge_large  # Taille large

        assert "B" in badge_medium
        assert "#85BB2F" in badge_medium  # Couleur du grade B
        assert "20px" in badge_medium  # Taille medium

        assert "C" in badge_small
        assert "#FECC00" in badge_small  # Couleur du grade C
        assert "16px" in badge_small  # Taille small

    def test_display_nutri_score_badge_all_grades(self):
        """Test du badge pour tous les grades."""
        grades = ["A", "B", "C", "D", "E"]
        colors = ["#238B45", "#85BB2F", "#FECC00", "#FF9500", "#E63946"]

        for grade, expected_color in zip(grades, colors):
            badge = display_nutri_score_badge(grade)
            assert grade in badge
            assert expected_color in badge

    def test_display_nutri_score_scale(self):
        """Test de l'échelle complète Nutri-Score."""
        scale_html = display_nutri_score_scale()

        # Vérifier que tous les grades sont présents
        for grade in ["A", "B", "C", "D", "E"]:
            assert grade in scale_html

        # Vérifier que les couleurs sont présentes
        colors = ["#238B45", "#85BB2F", "#FECC00", "#FF9500", "#E63946"]
        for color in colors:
            assert color in scale_html

    def test_render_nutri_score_in_card(self):
        """Test du rendu dans une carte."""
        # Test avec score
        card_with_score = render_nutri_score_in_card("A", 88.5)
        assert "A" in card_with_score
        assert "#238B45" in card_with_score
        assert "88" in card_with_score  # Score arrondi

        # Test sans score
        card_without_score = render_nutri_score_in_card("B")
        assert "B" in card_without_score
        assert "#85BB2F" in card_without_score

        # Test avec score NaN
        card_nan_score = render_nutri_score_in_card("C", float("nan"))
        assert "C" in card_nan_score
        assert "#FECC00" in card_nan_score

    def test_nutri_score_integration(self):
        """Test d'intégration entre les fonctions Nutri-Score."""
        # Test du workflow complet
        nutrition_scores = [95.0, 75.0, 60.0, 45.0, 25.0, float("nan")]

        grades = [get_nutri_grade(score) for score in nutrition_scores]
        expected_grades = ["A", "B", "C", "D", "E", "C"]

        assert grades == expected_grades

        # Test des couleurs correspondantes
        colors = [get_nutri_color(grade) for grade in grades]
        expected_colors = ["#238B45", "#85BB2F", "#FECC00", "#FF9500", "#E63946", "#FECC00"]

        assert colors == expected_colors

    def test_nutri_score_with_real_data(self):
        """Test avec des données réalistes."""
        # Simuler des scores de nutrition réels
        df = pd.DataFrame({"nutrition_score": [88.5, 72.3, 65.1, 48.7, 31.2, None, 95.0, 15.5]})

        # Calculer les grades
        df["nutrition_grade"] = df["nutrition_score"].apply(get_nutri_grade)

        # Vérifier la distribution
        grade_counts = df["nutrition_grade"].value_counts()

        # Doit avoir tous les grades représentés dans cet échantillon
        assert "A" in grade_counts.index
        assert "B" in grade_counts.index
        assert "C" in grade_counts.index
        assert "D" in grade_counts.index
        assert "E" in grade_counts.index

    def test_nutri_score_statistical_properties(self):
        """Test des propriétés statistiques du calcul de grade."""
        # Générer une série de scores
        np.random.seed(42)
        scores = np.random.normal(60, 20, 1000)  # Moyenne 60, écart-type 20
        scores = np.clip(scores, 0, 100)  # Limiter entre 0 et 100

        # Calculer les grades
        grades = [get_nutri_grade(score) for score in scores]

        # Compter les occurrences
        grade_counts = {grade: grades.count(grade) for grade in ["A", "B", "C", "D", "E"]}

        # Vérifier la distribution (approximative)
        total = len(grades)
        for grade, count in grade_counts.items():
            percentage = count / total
            assert 0.05 < percentage < 0.50  # Entre 5% et 50% pour chaque grade


class TestComponentsEdgeCases:
    """Tests pour les cas limites des composants."""

    @patch("components.filters_panel.st")
    def test_filters_panel_session_state_handling(self, mock_st):
        """Test de la gestion du session_state."""
        # Test sans filter_key_suffix
        mock_st.session_state = {}
        mock_st.sidebar.header = MagicMock()
        mock_st.sidebar.subheader = MagicMock()
        mock_st.sidebar.slider = MagicMock(return_value=(0, 300))
        mock_st.sidebar.selectbox = MagicMock(return_value="Toutes")
        mock_st.sidebar.multiselect = MagicMock(return_value=[])
        mock_st.sidebar.checkbox = MagicMock(return_value=False)
        mock_st.sidebar.caption = MagicMock()

        render_filters_panel(in_sidebar=True)

        # Vérifier que filter_key_suffix a été initialisé
        assert "filter_key_suffix" in mock_st.session_state

    def test_nutri_score_type_conversion(self):
        """Test de la conversion de types pour Nutri-Score."""
        # Test avec différents types
        assert get_nutri_grade("85.5") == "A"  # String
        assert get_nutri_grade(85) == "A"  # Integer
        assert get_nutri_grade(85.0) == "A"  # Float

        # Test avec valeurs extrêmes
        assert get_nutri_grade(float("inf")) == "A"
        assert get_nutri_grade(float("-inf")) == "E"


if __name__ == "__main__":
    pytest.main([__file__])
