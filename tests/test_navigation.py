"""
Tests pour le module de navigation entre les pages.

Ce module teste :
- La navigation vers les pages de détail
- L'alternance entre detail_a et detail_b
- La gestion de l'état de session
"""

from unittest.mock import patch

import streamlit as st

from utils.navigation import navigate_to_recipe


class TestNavigation:
    """Tests pour les fonctions de navigation."""

    @patch("streamlit.switch_page")
    def test_navigate_to_recipe_alternates_pages(self, mock_switch_page):
        """Test : Navigation alterne entre detail_a et detail_b."""
        # Setup : page actuelle = "a"
        st.session_state.current_detail_page = "a"

        # Appel de la fonction
        navigate_to_recipe(12345)

        # Vérifications
        assert st.session_state.recipe_id_to_view == 12345
        assert st.session_state.current_detail_page == "b"
        assert st.session_state.from_navigation is True
        mock_switch_page.assert_called_once_with("pages/recipe_detail_b.py")

    @patch("streamlit.switch_page")
    def test_navigate_to_recipe_from_b_to_a(self, mock_switch_page):
        """Test : Navigation de detail_b vers detail_a."""
        # Setup : page actuelle = "b"
        st.session_state.current_detail_page = "b"

        # Appel de la fonction
        navigate_to_recipe(67890)

        # Vérifications
        assert st.session_state.recipe_id_to_view == 67890
        assert st.session_state.current_detail_page == "a"
        assert st.session_state.from_navigation is True
        mock_switch_page.assert_called_once_with("pages/recipe_detail_a.py")

    @patch("streamlit.switch_page")
    def test_navigate_to_recipe_first_time(self, mock_switch_page):
        """Test : Première navigation (pas de page actuelle définie)."""
        # Setup : aucune page définie
        if "current_detail_page" in st.session_state:
            del st.session_state.current_detail_page

        # Appel de la fonction
        navigate_to_recipe(11111)

        # Vérifications : devrait utiliser "b" par défaut (inverse de "a")
        assert st.session_state.recipe_id_to_view == 11111
        assert st.session_state.current_detail_page == "b"
        mock_switch_page.assert_called_once_with("pages/recipe_detail_b.py")

    @patch("streamlit.switch_page")
    def test_navigate_sets_navigation_flag(self, mock_switch_page):
        """Test : Le flag from_navigation est correctement défini."""
        # Appel de la fonction
        navigate_to_recipe(99999)

        # Vérifications
        assert "from_navigation" in st.session_state
        assert st.session_state.from_navigation is True

    def test_navigate_stores_recipe_id(self):
        """Test : L'ID de la recette est stocké dans session_state."""
        with patch("streamlit.switch_page"):
            navigate_to_recipe(55555)

        # Vérifications
        assert "recipe_id_to_view" in st.session_state
        assert st.session_state.recipe_id_to_view == 55555
