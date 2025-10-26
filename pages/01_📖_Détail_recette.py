"""
Page de détail d'une recette - Navigation via query params.

Cette page affiche les informations complètes d'une recette sélectionnée
depuis la page de recherche principale. L'ID de la recette est transmis
via st.query_params.
"""

import ast
import logging

import pandas as pd
import streamlit as st

from services.data_loader import load_recipes
from services.recommender import get_recommender

logger = logging.getLogger(__name__)

# Configuration de la page
st.set_page_config(page_title="Détail Recette - Mangetamain", page_icon="📖", layout="wide")


def render_recipe_card_mini(recipe: pd.Series) -> None:
    """Affiche une mini-carte de recette pour les recommandations."""
    recipe_name = recipe.get("name", f"Recette #{int(recipe.get('id', 0))}")
    display_name = recipe_name if len(recipe_name) <= 50 else recipe_name[:47] + "..."

    nutri_grade = recipe.get("nutrition_grade", "C")
    nutri_colors = {"A": "#238B45", "B": "#85BB2F", "C": "#FECC00", "D": "#FF9500", "E": "#E63946"}
    nutri_color = nutri_colors.get(nutri_grade, "#7f8c8d")

    is_veg = recipe.get("isVegetarian", False) or recipe.get("is_vegetarian", False)
    prep_time = int(recipe.get("totalTime", recipe.get("minutes", 30)))

    tags = []
    if is_veg:
        tags.append(("🌱 Végé", "#28a745"))
    if prep_time <= 30:
        tags.append(("⚡ Rapide", "#007bff"))

    tags_html = " ".join(
        [
            f'<span style="background-color: {color}; color: white; padding: 3px 8px; '
            f'border-radius: 10px; font-size: 0.7rem; margin-right: 4px;">{tag}</span>'
            for tag, color in tags
        ]
    )

    rating = float(recipe.get("average_rating", 4.0))
    full_stars = int(rating)
    half_star = 1 if (rating - full_stars) >= 0.5 else 0
    empty_stars = 5 - full_stars - half_star

    stars_html = "⭐" * full_stars
    if half_star:
        stars_html += "✨"
    stars_html += "☆" * empty_stars

    card_html = f"""
    <div style="
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        background: white;
        height: 280px;
        display: flex;
        flex-direction: column;
        transition: transform 0.2s ease;
    ">
        <div style="
            width: 100%;
            height: 120px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
        ">
            <div style="
                position: absolute;
                top: 8px;
                right: 8px;
                background-color: {nutri_color};
                color: white;
                font-weight: bold;
                font-size: 12px;
                padding: 3px 8px;
                border-radius: 4px;
            ">{nutri_grade}</div>
            <div style="color: rgba(255,255,255,0.4); font-size: 2rem;">🍽️</div>
        </div>
        <div style="background: #2c2c2c; padding: 0.75rem; color: white; 
                    height: 160px; display: flex; flex-direction: column;">
            <div style="margin-bottom: 0.5rem;">{tags_html}</div>
            <h4 style="margin: 0 0 0.5rem 0; font-size: 1rem; color: white; 
                       font-weight: 600; line-height: 1.2; height: 2.5rem;
                       overflow: hidden;">{display_name}</h4>
            <div style="margin-top: auto; font-size: 0.8rem; color: #ffc107;">
                {stars_html} <span style="color: #e0e0e0;">{rating:.1f}/5</span>
            </div>
        </div>
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)


def main():
    """Affiche le détail d'une recette basé sur session_state ou query params."""

    # Récupérer l'ID de la recette depuis session_state (priorité) ou query params
    recipe_id = st.session_state.get("recipe_id_to_view") or st.query_params.get("id")

    if not recipe_id:
        st.error("❌ Aucune recette spécifiée")
        if st.button("← Retour à la recherche"):
            st.switch_page("app.py")
        return

    try:
        recipe_id = int(recipe_id)
        # Stocker dans session_state pour persistance
        st.session_state.current_recipe_id = recipe_id
    except ValueError:
        st.error("❌ ID de recette invalide")
        if st.button("← Retour à la recherche"):
            st.switch_page("app.py")
        return

    # Charger les données
    recipes_df = load_recipes()
    recommender = get_recommender(recipes_df)

    # Trouver la recette
    target_recipe = recipes_df[recipes_df["id"] == recipe_id]
    if target_recipe.empty:
        st.error(f"❌ Recette #{recipe_id} introuvable")
        if st.button("← Retour à la recherche"):
            st.switch_page("app.py")
        return

    target_recipe = target_recipe.iloc[0]
    recipe_name = target_recipe.get("name", f"Recette #{target_recipe['id']}")

    # Bouton retour en haut
    if st.button("← Retour à la recherche", key="back_top"):
        # Nettoyer les IDs stockés
        if "recipe_id_to_view" in st.session_state:
            del st.session_state.recipe_id_to_view
        if "current_recipe_id" in st.session_state:
            del st.session_state.current_recipe_id
        st.switch_page("app.py")

    # En-tête avec titre
    recipe_name_clean = str(recipe_name).replace("'", "&#39;").replace('"', "&quot;")
    title_html = (
        f"<div style='margin-bottom: 1.5rem;'>"
        f"<h1 style='font-size: 2.5rem; color: #ffffff; margin-bottom: 1rem; font-weight: 700;'>"
        f"{recipe_name_clean}"
        f"</h1>"
        f"</div>"
    )
    st.markdown(title_html, unsafe_allow_html=True)

    # Badges avec informations clés
    prep_time = int(target_recipe["totalTime"])
    calories = int(target_recipe["calories"])
    is_veg = target_recipe.get("isVegetarian", False)
    nutri_grade = target_recipe.get("nutrition_grade", "C")

    nutri_colors = {"A": "#28a745", "B": "#5cb85c", "C": "#ffc107", "D": "#fd7e14", "E": "#dc3545"}
    nutri_color = nutri_colors.get(nutri_grade, "#6c757d")

    if prep_time <= 30:
        time_tag = "⚡ Rapide"
        time_color = "#007bff"
    elif prep_time <= 60:
        time_tag = "⏱️ Moyen"
        time_color = "#ffc107"
    else:
        time_tag = "🍲 Longue"
        time_color = "#dc3545"

    veg_badge = ""
    if is_veg:
        veg_badge = "<span style='background: #28a745; color: white; padding: 0.4rem 1rem; border-radius: 20px; font-size: 0.9rem; font-weight: 600;'>🌱 Végétarien</span>"

    badges_html = (
        f"<div style='display: flex; gap: 0.75rem; margin-bottom: 1.5rem; flex-wrap: wrap;'>"
        f"<span style='background: {time_color}; color: white; padding: 0.4rem 1rem; border-radius: 20px; font-size: 0.9rem; font-weight: 600;'>{time_tag} ({prep_time} min)</span>"
        f"<span style='background: #ff6b6b; color: white; padding: 0.4rem 1rem; border-radius: 20px; font-size: 0.9rem; font-weight: 600;'>🔥 {calories} kcal</span>"
        f"{veg_badge}"
        f"<span style='background: {nutri_color}; color: white; padding: 0.4rem 1rem; border-radius: 20px; font-size: 0.9rem; font-weight: 600;'>Nutri-Score: {nutri_grade}</span>"
        f"</div>"
    )
    st.markdown(badges_html, unsafe_allow_html=True)

    # Grande image de la recette (placeholder)
    image_html = (
        "<div style='width: 100%; height: 400px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); "
        "border-radius: 15px; display: flex; align-items: center; justify-content: center; margin-bottom: 2rem; "
        "box-shadow: 0 4px 12px rgba(0,0,0,0.1);'>"
        "<div style='color: rgba(255,255,255,0.4); font-size: 5rem;'>🍽️</div>"
        "</div>"
    )
    st.markdown(image_html, unsafe_allow_html=True)

    # Description
    description = target_recipe.get("description", "")
    if description and pd.notna(description):
        description_clean = str(description).replace("'", "&#39;").replace('"', "&quot;")
        description_html = (
            f"<div style='background: #2d2d2d; padding: 1.5rem; border-radius: 10px; margin-bottom: 2rem; "
            f"font-size: 1.05rem; line-height: 1.8; color: #e0e0e0; font-style: italic;'>"
            f"{description_clean}"
            f"</div>"
        )
        st.markdown(description_html, unsafe_allow_html=True)

    # Section Ingrédients
    st.markdown("### Ingredients:")
    st.markdown("---")

    ingredients_text = target_recipe.get("ingredients", "")
    if isinstance(ingredients_text, str) and ingredients_text:
        try:
            ingredients_list = (
                ast.literal_eval(ingredients_text) if ingredients_text.startswith("[") else [ingredients_text]
            )
            for ingredient in ingredients_list[:20]:
                st.markdown(f"• {ingredient}")
        except (ValueError, SyntaxError):
            st.write("Informations d'ingrédients non disponibles")
    else:
        st.write("Informations d'ingrédients non disponibles")

    st.markdown("<br>", unsafe_allow_html=True)

    # Section Instructions
    st.markdown("### Instructions:")
    st.markdown("---")

    steps_text = target_recipe.get("steps", "")
    if isinstance(steps_text, str) and steps_text:
        try:
            steps_list = ast.literal_eval(steps_text) if steps_text.startswith("[") else [steps_text]
            for i, step in enumerate(steps_list[:20], 1):
                step_clean = str(step).replace("'", "&#39;").replace('"', "&quot;")
                step_title = step_clean.split(":")[0] if ":" in step_clean else f"Step {i}"
                step_content = step_clean.split(":", 1)[1].strip() if ":" in step_clean else step_clean

                step_html = (
                    f"<div style='margin-bottom: 1.5rem;'>"
                    f"<strong style='color: #667eea; font-size: 1.1rem;'>{i}. {step_title}:</strong>"
                    f"<div style='margin-top: 0.5rem; color: #e0e0e0; line-height: 1.6;'>{step_content}</div>"
                    f"</div>"
                )
                st.markdown(step_html, unsafe_allow_html=True)
        except (ValueError, SyntaxError):
            st.write("Instructions non disponibles")
    else:
        st.write("Instructions non disponibles")

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")

    # Recommandations
    recommendations_header = (
        "<h2 style='text-align: center; color: #667eea; font-size: 2rem; margin: 2rem 0;'>🌟 Recettes similaires</h2>"
    )
    st.markdown(recommendations_header, unsafe_allow_html=True)

    with st.spinner("Calcul des recommandations..."):
        recommendations = recommender.get_similar_recipes(recipe_id, k=8)

    if recommendations:
        for i in range(0, len(recommendations), 4):
            cols = st.columns(4)
            for j, col in enumerate(cols):
                idx = i + j
                if idx < len(recommendations):
                    recipe, score = recommendations[idx]
                    with col:
                        render_recipe_card_mini(recipe)

                        # Bouton pour voir cette recette - utilise session_state
                        if st.button(
                            "📖 Voir", key=f"view_rec_{recipe['id']}", use_container_width=True, type="primary"
                        ):
                            st.session_state.recipe_id_to_view = recipe["id"]
                            st.rerun()

    # Bouton retour en bas
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("← Retour à la recherche", key="back_bottom", use_container_width=False):
        # Nettoyer les IDs stockés
        if "recipe_id_to_view" in st.session_state:
            del st.session_state.recipe_id_to_view
        if "current_recipe_id" in st.session_state:
            del st.session_state.current_recipe_id
        st.switch_page("app.py")


if __name__ == "__main__":
    main()
