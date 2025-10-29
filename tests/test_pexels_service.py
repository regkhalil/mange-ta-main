"""
Tests pour le service Pexels Image Service.

Ce module teste :
- La récupération d'images depuis l'API Pexels
- Le cache des images
- La gestion des erreurs et timeouts
- Les fallbacks en cas d'échec
"""

from unittest.mock import Mock, patch

from services.pexels_image_service import get_image_from_pexels


class TestPexelsImageService:
    """Tests pour le service de récupération d'images Pexels."""

    @patch("services.pexels_image_service.requests.get")
    def test_get_image_success(self, mock_get):
        """Test : Récupération réussie d'une image depuis Pexels."""
        # Mock de la réponse API
        mock_response = Mock()
        mock_response.json.return_value = {
            "photos": [{"src": {"large": "https://images.pexels.com/photos/123/test.jpg"}}]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Appel de la fonction
        result = get_image_from_pexels("chocolate cake")

        # Vérifications
        assert result == "https://images.pexels.com/photos/123/test.jpg"
        mock_get.assert_called()

    @patch("services.pexels_image_service.requests.get")
    def test_get_image_no_results(self, mock_get):
        """Test : Aucune image trouvée, utilise le fallback générique."""
        # Premier appel : aucun résultat
        mock_response_1 = Mock()
        mock_response_1.json.return_value = {"photos": []}
        mock_response_1.raise_for_status = Mock()

        # Deuxième appel : résultat générique
        mock_response_2 = Mock()
        mock_response_2.json.return_value = {
            "photos": [{"src": {"large": "https://images.pexels.com/photos/456/food.jpg"}}]
        }
        mock_response_2.raise_for_status = Mock()

        mock_get.side_effect = [mock_response_1, mock_response_2]

        # Appel de la fonction
        result = get_image_from_pexels("unknown recipe xyz")

        # Vérifications
        assert result == "https://images.pexels.com/photos/456/food.jpg"
        assert mock_get.call_count == 2

    @patch("services.pexels_image_service.requests.get")
    def test_get_image_timeout(self, mock_get):
        """Test : Timeout lors de l'appel API."""
        import requests

        mock_get.side_effect = requests.exceptions.Timeout()

        # Appel de la fonction
        result = get_image_from_pexels("test recipe")

        # Vérifications : devrait retourner None en cas de timeout
        assert result is None

    @patch("services.pexels_image_service.requests.get")
    def test_get_image_http_error(self, mock_get):
        """Test : Erreur HTTP (403, 500, etc.)."""
        import requests

        mock_get.side_effect = requests.exceptions.HTTPError("403 Forbidden")

        # Appel de la fonction
        result = get_image_from_pexels("test recipe")

        # Vérifications
        assert result is None

    def test_get_image_empty_name(self):
        """Test : Nom de recette vide."""
        # Appel avec nom vide
        result = get_image_from_pexels("")

        # Vérifications : devrait retourner None
        assert result is None

    @patch("services.pexels_image_service.requests.get")
    def test_get_image_caching(self, mock_get):
        """Test : Vérification que le cache Streamlit fonctionne."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "photos": [{"src": {"large": "https://images.pexels.com/photos/789/cached.jpg"}}]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Clear cache avant le test
        get_image_from_pexels.clear()

        # Premier appel
        result1 = get_image_from_pexels("pasta carbonara")

        # Deuxième appel (devrait utiliser le cache)
        result2 = get_image_from_pexels("pasta carbonara")

        # Vérifications
        assert result1 == result2
        # L'API ne devrait être appelée qu'une seule fois grâce au cache
        assert mock_get.call_count == 1
