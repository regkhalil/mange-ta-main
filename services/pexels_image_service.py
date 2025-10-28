"""
Service pour récupérer les images de recettes via l'API Pexels.
API Pexels : https://www.pexels.com/api/documentation/

Fonctionnalités :
- Recherche d'images par nom de recette
- Cache des résultats pour éviter les appels répétés
- Gestion des erreurs et fallback
"""

import logging
import os
from typing import Optional

import requests
import streamlit as st

logger = logging.getLogger(__name__)

# Pexels API key (overridable via environment variable or secrets)
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "kf3rfQoEUAGezF8M4T6gJ4gKLiIZw93xd0BqF8NTx2oDExXCgZAco9J6")

# Fallback placeholder image URL when no image found
FALLBACK_IMAGE_URL = "https://via.placeholder.com/400x300/667eea/ffffff?text=No+Image"


@st.cache_data(ttl=3600)  # Cache pendant 1 heure
def get_image_from_pexels(recipe_name: str, per_page: int = 1) -> Optional[str]:
    """
    Récupère l'URL d'une image correspondant au nom de la recette via l'API Pexels.

    Args:
        recipe_name: Nom de la recette à rechercher
        per_page: Nombre de résultats à récupérer (défaut: 1)

    Returns:
        URL de l'image (large) ou None si aucune image n'est trouvée

    Exemple:
        >>> get_image_from_pexels("chocolate cake")
        'https://images.pexels.com/photos/1234/pexels-photo-1234.jpeg'
    """
    try:
        # Clean recipe name for search query
        query = recipe_name.strip()

        if not query:
            logger.warning("Nom de recette vide, impossible de rechercher une image")
            return None

        # Enhance query with culinary keywords to get food images
        # Essayer d'abord avec le nom complet + "food"
        enhanced_query = f"{query} food"

        logger.info(f"Recherche d'image Pexels pour: {enhanced_query}")

        # Build Pexels API request
        url = "https://api.pexels.com/v1/search"
        headers = {"Authorization": PEXELS_API_KEY}
        params = {
            "query": enhanced_query,
            "per_page": 3,  # Fetch 3 results for better selection
            "page": 1,
        }

        # Execute request with reduced timeout
        response = requests.get(url, headers=headers, params=params, timeout=5)
        response.raise_for_status()

        # Process response
        data = response.json()

        if data.get("photos") and len(data["photos"]) > 0:
            # Fetch first image (large format)
            image_url = data["photos"][0]["src"]["large"]
            logger.info(f"Image Pexels trouvée pour '{recipe_name}': {image_url}")
            return image_url
        else:
            # If no results with full name, try generic "food" query
            logger.info(f"Aucune image trouvée pour '{query} food', essai avec 'food dish'")
            params["query"] = "food dish"
            response = requests.get(url, headers=headers, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            if data.get("photos") and len(data["photos"]) > 0:
                image_url = data["photos"][0]["src"]["large"]
                logger.info(f"Image générique trouvée pour '{recipe_name}'")
                return image_url
            else:
                logger.info(f"Aucune image Pexels trouvée pour '{recipe_name}'")
                return None

    except requests.exceptions.Timeout:
        logger.warning(f"Timeout lors de la recherche d'image Pexels pour '{recipe_name}'")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"Erreur HTTP lors de la recherche d'image Pexels: {e}")
        return None
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la recherche d'image Pexels pour '{recipe_name}': {str(e)}")
        return None


def get_image_with_fallback(recipe_name: str) -> str:
    """
    Récupère une image pour la recette avec fallback automatique.

    Args:
        recipe_name: Nom de la recette

    Returns:
        URL de l'image (Pexels ou fallback)
    """
    image_url = get_image_from_pexels(recipe_name)

    if image_url:
        return image_url
    else:
        logger.info(f"Utilisation de l'image fallback pour '{recipe_name}'")
        return FALLBACK_IMAGE_URL


# Interface de test Streamlit
def main():
    """
    Interface Streamlit de test pour le service d'images Pexels.
    """
    st.set_page_config(page_title="Test API Pexels", page_icon="🖼️", layout="centered")

    st.title("🖼️ Test API Pexels - Recherche d'Images")
    st.markdown("---")

    # Display API key (masked)
    api_key_display = PEXELS_API_KEY[:10] + "..." + PEXELS_API_KEY[-5:]
    st.info(f"🔑 Clé API Pexels : `{api_key_display}`")

    # Champ de recherche
    recipe_name = st.text_input(
        "🍽️ Nom du plat",
        placeholder="Ex: chocolate cake, spaghetti, pizza...",
        help="Entrez le nom d'un plat pour rechercher une image",
    )

    # Bouton de recherche
    if st.button("🔍 Rechercher", type="primary", use_container_width=True):
        if recipe_name:
            with st.spinner(f"Recherche d'une image pour '{recipe_name}'..."):
                image_url = get_image_from_pexels(recipe_name)

                if image_url:
                    st.success(f"✅ Image trouvée pour '{recipe_name}'")
                    st.image(image_url, caption=recipe_name, use_container_width=True)
                    st.code(image_url, language=None)
                else:
                    st.warning(f"⚠️ Aucune image trouvée pour '{recipe_name}'.")
                    st.info("💡 Essayez avec un nom de plat plus simple ou en anglais")

                    # Afficher l'image de fallback
                    st.markdown("**Image de fallback :**")
                    fallback = get_image_with_fallback(recipe_name)
                    st.image(fallback, caption="Image par défaut", use_container_width=True)
        else:
            st.error("❌ Veuillez entrer le nom d'un plat")

    # Instructions
    st.markdown("---")
    st.markdown("""
    ### 📚 Utilisation dans votre code
    
    ```python
    from services.pexels_image_service import get_image_from_pexels, get_image_with_fallback
    
    # Fetch image (may return None)
    image_url = get_image_from_pexels("chocolate cake")
    
    # Fetch image with automatic fallback
    image_url = get_image_with_fallback("chocolate cake")
    
    # Afficher l'image dans Streamlit
    if image_url:
        st.image(image_url)
    ```
    """)


if __name__ == "__main__":
    main()
