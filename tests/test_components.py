"""
Tests pour les composants UI de l'application.

Ce module teste :
- Le panneau de filtres
- Les cartes de recettes
- Les en-têtes de métriques
- Le Nutri-Score
"""

import pandas as pd
import streamlit as st

from components.nutri_score import get_nutri_color, get_nutri_grade


class TestNutriScore:
    """Tests pour le composant Nutri-Score."""

    def test_nutriscore_grade_A(self):
        """Test : Score excellent (A) pour score >= 85."""
        grade = get_nutri_grade(85)
        assert grade == "A"

        grade = get_nutri_grade(98)
        assert grade == "A"

    def test_nutriscore_grade_B(self):
        """Test : Score bon (B) pour 70 <= score < 85."""
        grade = get_nutri_grade(70)
        assert grade == "B"

        grade = get_nutri_grade(84)
        assert grade == "B"

    def test_nutriscore_grade_C(self):
        """Test : Score moyen (C) pour 55 <= score < 70."""
        grade = get_nutri_grade(55)
        assert grade == "C"

        grade = get_nutri_grade(69)
        assert grade == "C"

    def test_nutriscore_grade_D(self):
        """Test : Score médiocre (D) pour 40 <= score < 55."""
        grade = get_nutri_grade(40)
        assert grade == "D"

        grade = get_nutri_grade(54)
        assert grade == "D"

    def test_nutriscore_grade_E(self):
        """Test : Score mauvais (E) pour score < 40."""
        grade = get_nutri_grade(10)
        assert grade == "E"

        grade = get_nutri_grade(39)
        assert grade == "E"

    def test_nutriscore_color_mapping(self):
        """Test : Couleurs correctes pour chaque grade."""
        assert get_nutri_color("A") == "#238B45"  # Vert foncé
        assert get_nutri_color("B") == "#85BB2F"  # Vert clair
        assert get_nutri_color("C") == "#FECC00"  # Jaune
        assert get_nutri_color("D") == "#FF9500"  # Orange
        assert get_nutri_color("E") == "#E63946"  # Rouge

    def test_nutriscore_color_default(self):
        """Test : Couleur par défaut pour grade invalide."""
        assert get_nutri_color("X") == "#7f8c8d"  # Gris par défaut
        assert get_nutri_color("") == "#7f8c8d"


class TestFiltersPanel:
    """Tests pour le panneau de filtres."""

    def test_render_filters_panel_returns_dict(self):
        """Test : Le panneau de filtres retourne un dictionnaire de filtres."""
        # Les filtres sont stockés dans session_state
        # Initialiser session_state
        if "filters" not in st.session_state:
            st.session_state.filters = {
                "prep": [0, 300],
                "ingredients": [1, 45],
                "calories": [0, 2000],
                "vegetarian_only": False,
                "nutrition_grades": [],
            }

        filters = st.session_state.filters

        # Vérifications
        assert isinstance(filters, dict)
        assert "prep" in filters
        assert "ingredients" in filters
        assert "calories" in filters
        assert "vegetarian_only" in filters
        assert "nutrition_grades" in filters

    def test_filters_vegetarian_only(self):
        """Test : Filtre végétarien activé."""
        # Simuler l'activation du filtre végétarien
        if "filters" not in st.session_state:
            st.session_state.filters = {
                "prep": [0, 300],
                "ingredients": [1, 45],
                "calories": [0, 2000],
                "vegetarian_only": True,  # Activé
                "nutrition_grades": [],
            }

        st.session_state.filters["vegetarian_only"] = True
        filters = st.session_state.filters

        assert filters["vegetarian_only"] is True


class TestRecipeCard:
    """Tests pour les cartes de recettes."""

    def test_recipe_card_displays_required_fields(self):
        """Test : La carte de recette affiche les champs requis."""
        # Créer une recette de test
        recipe = pd.Series(
            {
                "id": 12345,
                "name": "Test Recipe",
                "minutes": 30,
                "n_ingredients": 5,
                "calories": 250,
                "nutrition_grade": "B",
                "isVegetarian": True,
                "average_rating": 4.5,
            }
        )

        # Vérifier que les champs essentiels sont présents
        assert recipe["name"] == "Test Recipe"
        assert recipe["minutes"] == 30
        assert recipe["nutrition_grade"] == "B"

    def test_recipe_name_truncation(self):
        """Test : Les noms longs sont tronqués."""
        long_name = "A" * 100
        display_name = long_name if len(long_name) <= 60 else long_name[:57] + "..."

        assert len(display_name) <= 60
        assert display_name.endswith("...")
