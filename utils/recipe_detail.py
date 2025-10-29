"""Logique réutilisable pour afficher les détails d'une recette."""

import ast

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from services.data_loader import load_recipes
from services.pexels_image_service import get_image_from_pexels


def render_recipe_card_mini(recipe: pd.Series) -> None:
    """Affiche une mini-carte de recette pour les recommandations (identique à la page d'accueil)."""
    recipe_name = recipe.get("name", f"Recette #{int(recipe.get('id', 0))}")
    display_name = recipe_name if len(recipe_name) <= 60 else recipe_name[:57] + "..."

    # Fetch image via Pexels
    image_url = get_image_from_pexels(recipe_name)

    nutri_grade = recipe.get("nutrition_grade", "C")
    nutri_colors = {"A": "#238B45", "B": "#85BB2F", "C": "#FECC00", "D": "#FF9500", "E": "#E63946"}
    nutri_color = nutri_colors.get(nutri_grade, "#7f8c8d")

    is_veg = recipe.get("isVegetarian", False) or recipe.get("is_vegetarian", False)
    prep_time = int(recipe.get("totalTime", recipe.get("minutes", 30)))
    n_ingredients = int(recipe.get("n_ingredients", 0))

    # Create badges/tags (always display essential tags)
    tags = []

    # Preparation time tag - emoji seulement
    if prep_time >= 120:
        tags.append(("🍲", "#d9534f"))
    elif prep_time <= 30:
        tags.append(("⚡", "#007bff"))
    elif prep_time <= 60:
        tags.append(("⏱️", "#ffc107"))
    else:
        tags.append(("⏱️", "#ff6347"))

    # Ingredients count tag - emoji + nombre
    if n_ingredients > 0:
        if n_ingredients <= 5:
            tags.append((f"🥗 {n_ingredients}", "#17a2b8"))
        elif n_ingredients <= 10:
            tags.append((f"🥘 {n_ingredients}", "#6c757d"))
        else:
            tags.append((f"👨‍🍳 {n_ingredients}", "#6f42c1"))

    # Calories tag - nombre seulement
    calories = int(recipe.get("calories", 0))
    tags.append((str(calories) + " kcal", "#E74C3C"))

    # Vegetarian tag - emoji seulement
    if is_veg:
        tags.append(("🌱", "#2ECC71"))

    # Nutri-Score tag - lettre seulement
    tags.append((nutri_grade, nutri_color))

    tags_html = " ".join(
        [
            f'<span style="background-color: {color}; color: white; padding: 4px 10px; '
            f"border-radius: 12px; font-size: 0.75rem; margin-right: 5px; display: inline-block; "
            f'vertical-align: middle; white-space: nowrap;">{tag}</span>'
            for tag, color in tags
        ]
    )

    # Description - utiliser la vraie description de la recette si disponible
    description = "Découvrez cette délicieuse recette..."
    if "description" in recipe and pd.notna(recipe["description"]):
        desc_text = str(recipe["description"]).strip()
        if desc_text:
            description = desc_text[:80] + "..." if len(desc_text) > 80 else desc_text
    elif "steps" in recipe and recipe["steps"]:
        try:
            steps_text = recipe["steps"]
            if isinstance(steps_text, str) and steps_text.startswith("["):
                steps_list = ast.literal_eval(steps_text)
                if steps_list and len(steps_list) > 0:
                    first_step = str(steps_list[0])[:80]
                    description = first_step + "..." if len(first_step) == 80 else first_step
        except (ValueError, SyntaxError):
            pass

    rating = float(recipe.get("average_rating", 4.0))
    review_count = int(recipe.get("review_count", 0))
    full_stars = int(rating)
    half_star = 1 if (rating - full_stars) >= 0.5 else 0
    empty_stars = 5 - full_stars - half_star

    stars_html = "⭐" * full_stars
    if half_star:
        stars_html += "✨"
    stars_html += "☆" * empty_stars

    rating_display = f'<div class="recipe-rating-stars" style="margin-top: 0.5rem; font-size: 0.9rem; color: #ffc107 !important;">{stars_html} <span class="recipe-rating-text" style="color: #ffffff !important;">{rating:.1f}/5 ({review_count})</span></div>'

    card_html = f"""
    <div style="
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        background: white;
        height: 420px;
        display: flex;
        flex-direction: column;
        transition: transform 0.2s ease;
    ">
        <div style="
            width: 100%;
            height: 200px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
            overflow: hidden;
        ">
            <div style="
                position: absolute;
                top: 12px;
                right: 12px;
                background-color: {nutri_color};
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 4px 12px;
                border-radius: 6px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                z-index: 10;
            ">{nutri_grade}</div>
            {f'<img src="{image_url}" style="width: 100%; height: 100%; object-fit: cover;" alt="{recipe_name}" />' if image_url else '<div style="color: rgba(255,255,255,0.5); font-size: 3rem;">🍽️</div>'}
        </div>
        <div class="recipe-similar-card-dark" style="background: #2c2c2c; padding: 1rem; color: white; 
                    height: 220px; flex-shrink: 0; display: flex; flex-direction: column;">
            <div style="margin-bottom: 0.7rem; min-height: 28px;">{tags_html}</div>
            <h3 style="margin: 0 0 0.5rem 0; font-size: 1.25rem; color: white !important; 
                       font-weight: 700; line-height: 1.3; height: 3.5rem;
                       overflow: hidden; text-overflow: ellipsis; display: -webkit-box;
                       -webkit-line-clamp: 2; -webkit-box-orient: vertical;">{display_name}</h3>
            <p style="margin: 0; font-size: 0.85rem; color: #b0b0b0 !important;
                      line-height: 1.4; flex-grow: 1; overflow: hidden;">{description}</p>
            {rating_display}
        </div>
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)


def render_recipe_detail(recipes_df: pd.DataFrame, recommender, recipe_id: int, on_view_similar=None):
    """
    Affiche le détail complet d'une recette avec recommandations.

    Args:
        recipes_df: DataFrame des recettes
        recommender: Instance du recommender
        recipe_id: ID de la recette à afficher
        on_view_similar: Callback(recipe_id) appelé quand on clique sur une recette similaire
    """
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
        if "recipe_id_to_view" in st.session_state:
            del st.session_state.recipe_id_to_view
        if "current_recipe_id" in st.session_state:
            del st.session_state.current_recipe_id
        st.switch_page("app.py")

    # Header with title
    recipe_name_clean = str(recipe_name).replace("'", "&#39;").replace('"', "&quot;")
    title_html = (
        f"<div style='margin-bottom: 1.5rem;'>"
        f"<h1 style='font-size: 2.5rem; color: #ffffff; margin-bottom: 1rem; font-weight: 700;'>"
        f"{recipe_name_clean}"
        f"</h1>"
        f"</div>"
    )
    st.markdown(title_html, unsafe_allow_html=True)

    # Badges with key information
    prep_time = int(target_recipe.get("totalTime", target_recipe.get("minutes", 30)))

    # Extract calories from nutrition array (or use direct column if available)
    calories = int(target_recipe.get("calories", 0))
    if calories == 0:
        # Fallback: extract from nutrition array
        nutrition_data = target_recipe.get("nutrition")
        if nutrition_data:
            try:
                if isinstance(nutrition_data, str):
                    nutrition_array = ast.literal_eval(nutrition_data)
                else:
                    nutrition_array = nutrition_data
                calories = int(nutrition_array[0]) if nutrition_array else 0
            except (ValueError, IndexError, SyntaxError):
                calories = 0

    is_veg = target_recipe.get("isVegetarian", target_recipe.get("is_vegetarian", False))
    nutri_grade = target_recipe.get("nutrition_grade", "C")
    nutri_score = float(target_recipe.get("nutrition_score", 50))
    n_ingredients = int(target_recipe.get("n_ingredients", 0))

    nutri_colors = {"A": "#28a745", "B": "#82c91e", "C": "#ffc107", "D": "#fd7e14", "E": "#dc3545"}
    nutri_color = nutri_colors.get(nutri_grade, "#6c757d")

    # Create comprehensive tags list
    tags = []

    # Preparation time tag
    if prep_time >= 120:
        tags.append((f"🍲 Longue ({prep_time} min)", "#d9534f"))
    elif prep_time <= 30:
        tags.append((f"⚡ Rapide ({prep_time} min)", "#007bff"))
    elif prep_time <= 60:
        tags.append((f"⏱️ Moyen ({prep_time} min)", "#ffc107"))
    else:
        tags.append((f"⏱️ {prep_time} min", "#ff6347"))

    # Ingredients count tag
    if n_ingredients > 0:
        if n_ingredients <= 5:
            tags.append((f"🥗 Simple ({n_ingredients} ingr.)", "#17a2b8"))
        elif n_ingredients <= 10:
            tags.append((f"🥘 Modéré ({n_ingredients} ingr.)", "#6c757d"))
        else:
            tags.append((f"👨‍🍳 Élaboré ({n_ingredients} ingr.)", "#6f42c1"))

    # Calories tag
    tags.append((f"🔥 {calories} kcal", "#ff6b6b"))

    # Vegetarian tag
    if is_veg:
        tags.append(("🌱 Végétarien", "#28a745"))

    # Nutri-Score tag (with link to analysis)
    nutri_tag_html = f"<a href='#nutrition-analysis' style='text-decoration: none;'><span title='Score: {nutri_score:.2f} - Cliquez pour voir l&#39;analyse détaillée' style='background: {nutri_color}; color: white; padding: 0.4rem 1rem; border-radius: 20px; font-size: 0.9rem; font-weight: 700; cursor: pointer;'>Nutri-Score {nutri_grade}</span></a>"

    # Build badges HTML
    badges_list = " ".join(
        [
            f"<span style='background: {color}; color: white; padding: 0.4rem 1rem; border-radius: 20px; font-size: 0.9rem; font-weight: 600;'>{tag}</span>"
            for tag, color in tags
        ]
    )

    badges_html = (
        f"<div style='display: flex; gap: 0.75rem; margin-bottom: 1.5rem; flex-wrap: wrap; align-items: center;'>"
        f"{badges_list}"
        f"{nutri_tag_html}"
        f"</div>"
    )
    st.markdown(badges_html, unsafe_allow_html=True)

    # Large recipe image from Pexels - centered with reduced width
    image_url = get_image_from_pexels(recipe_name)
    if image_url:
        image_html = (
            f"<div style='display: flex; justify-content: center; margin-bottom: 2rem;'>"
            f"<div style='width: 40%; height: 350px; border-radius: 15px; overflow: hidden; "
            f"box-shadow: 0 4px 12px rgba(0,0,0,0.1);'>"
            f"<img src='{image_url}' style='width: 100%; height: 100%; object-fit: cover;' alt='{recipe_name}' />"
            f"</div></div>"
        )
    else:
        image_html = (
            "<div style='display: flex; justify-content: center; margin-bottom: 2rem;'>"
            "<div style='width: 40%; height: 350px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); "
            "border-radius: 15px; display: flex; align-items: center; justify-content: center; "
            "box-shadow: 0 4px 12px rgba(0,0,0,0.1);'>"
            "<div style='color: rgba(255,255,255,0.4); font-size: 5rem;'>🍽️</div>"
            "</div></div>"
        )
    st.markdown(image_html, unsafe_allow_html=True)

    # Description - Subtle styling to keep focus on the title
    description = target_recipe.get("description", "")
    if description and pd.notna(description):
        description_clean = str(description).replace("'", "&#39;").replace('"', "&quot;")
        description_html = (
            f"<div style='border-left: 4px solid #667eea; padding: 1.5rem 1.5rem 1.5rem 2rem; "
            f"margin-bottom: 2rem; background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);'>"
            f"<p style='font-size: 1rem; line-height: 1.7; color: #1a1a1a; margin: 0; "
            f'font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;\'>{description_clean}</p>'
            f"</div>"
        )
        st.markdown(description_html, unsafe_allow_html=True)

    # Ingredients section - compact inline display
    st.markdown("### Ingrédients")

    ingredients_text = target_recipe.get("ingredients", "")
    if isinstance(ingredients_text, str) and ingredients_text:
        try:
            ingredients_list = (
                ast.literal_eval(ingredients_text) if ingredients_text.startswith("[") else [ingredients_text]
            )
            # Display ingredients as inline chips - fond clair
            ingredients_html = "<div style='margin-bottom: 1.5rem;'>"
            for ingredient in ingredients_list[:20]:
                ing_clean = str(ingredient).replace("'", "&#39;").replace('"', "&quot;")
                ingredients_html += f"<span style='background: #e8e8e8; color: #2c3e50; padding: 0.3rem 0.7rem; border-radius: 15px; font-size: 0.85rem; margin: 0.2rem; display: inline-block; border: 1px solid #d0d0d0;'>{ing_clean}</span>"
            ingredients_html += "</div>"
            st.markdown(ingredients_html, unsafe_allow_html=True)
        except (ValueError, SyntaxError):
            st.write("Informations d'ingrédients non disponibles")
    else:
        st.write("Informations d'ingrédients non disponibles")

    # Section Instructions - Style élégant comme la description
    st.markdown("### Instructions")

    steps_text = target_recipe.get("steps", "")
    if isinstance(steps_text, str) and steps_text:
        try:
            steps_list = ast.literal_eval(steps_text) if steps_text.startswith("[") else [steps_text]
            for i, step in enumerate(steps_list[:20], 1):
                step_clean = str(step).replace("'", "&#39;").replace('"', "&quot;")
                step_html = (
                    f"<div style='border-left: 4px solid #667eea; padding: 1rem 1rem 1rem 1.5rem; "
                    f"margin-bottom: 1rem; background: #f8f9fa; border-radius: 8px;'>"
                    f"<span style='color: #667eea; font-size: 1.1rem; font-weight: 700; margin-right: 0.75rem;'>{i}.</span>"
                    f"<span style='color: #2c3e50; line-height: 1.7; font-size: 1rem; "
                    f'font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;\'>{step_clean}</span>'
                    f"</div>"
                )
                st.markdown(step_html, unsafe_allow_html=True)
        except (ValueError, SyntaxError):
            st.write("Instructions non disponibles")
    else:
        st.write("Instructions non disponibles")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    # Nutrition Statistics and Visualizations
    st.markdown("<div id='nutrition-analysis'></div>", unsafe_allow_html=True)
    st.markdown("### 📊 Analyse Nutritionnelle")

    # Load nutrition data from the recipe
    try:
        nutrition_data = target_recipe.get("nutrition")

        if nutrition_data:
            # If it's a string, parse it; if it's already a list, use it directly
            if isinstance(nutrition_data, str):
                nutrition_array = ast.literal_eval(nutrition_data)
            else:
                nutrition_array = nutrition_data

            calories_nutr, total_fat, sugar, sodium, protein, saturated_fat, carbohydrates = nutrition_array

            # Create two columns for gauge and table
            col1, col2 = st.columns([1, 1])

            with col1:
                # Nutri-Score Gauge with median reference and quartile markers
                nutri_colors = {"A": "#28a745", "B": "#82c91e", "C": "#ffc107", "D": "#fd7e14", "E": "#dc3545"}
                gauge_color = nutri_colors.get(nutri_grade, "#6c757d")

                # Add title above the gauge
                st.markdown(
                    f"<h3 style='text-align: center; font-size: 1.5rem; color: #1a1a1a; margin-bottom: -5px; margin-top: 0;'>Nutri-Score: {nutri_grade}</h3>",
                    unsafe_allow_html=True,
                )

                # Calculate dataset statistics for reference
                all_recipes = load_recipes()
                all_scores = all_recipes[["nutrition_score"]].dropna()
                median_score = all_scores["nutrition_score"].median()
                q1_score = all_scores["nutrition_score"].quantile(0.25)
                q3_score = all_scores["nutrition_score"].quantile(0.75)

                fig_gauge = go.Figure(
                    go.Indicator(
                        mode="gauge+number+delta",
                        value=nutri_score,
                        domain={"x": [0, 1], "y": [0, 1]},
                        delta={
                            "reference": median_score,
                            "increasing": {"color": "#28a745"},  # Higher = better (green)
                            "decreasing": {"color": "#dc3545"},  # Lower = worse (red)
                            "suffix": " vs médiane",
                            "position": "bottom",
                            "font": {"size": 14},
                        },
                        number={"suffix": "/100", "font": {"size": 36}, "valueformat": ".1f"},
                        gauge={
                            "axis": {
                                "range": [0, 100],
                                "tickwidth": 2,
                                "tickcolor": "darkgray",
                                "tickmode": "array",
                                "tickvals": [q1_score, median_score, q3_score],
                                "ticktext": [
                                    f"Q1: {q1_score:.0f}",
                                    f"Médiane: {median_score:.0f}",
                                    f"Q3: {q3_score:.0f}",
                                ],
                            },
                            "bar": {"color": gauge_color, "thickness": 0.75},
                            "bgcolor": "white",
                            "borderwidth": 2,
                            "bordercolor": "gray",
                            "steps": [
                                {"range": [0, 20], "color": "rgba(220, 53, 69, 0.3)"},  # E - worst (red)
                                {"range": [20, 40], "color": "rgba(253, 126, 20, 0.3)"},  # D - poor (orange)
                                {"range": [40, 60], "color": "rgba(255, 193, 7, 0.3)"},  # C - average (yellow)
                                {"range": [60, 80], "color": "rgba(130, 201, 30, 0.3)"},  # B - good (lime)
                                {"range": [80, 100], "color": "rgba(40, 167, 69, 0.3)"},  # A - best (green)
                            ],
                            "threshold": {
                                "line": {"color": "black", "width": 4},
                                "thickness": 0.75,
                                "value": nutri_score,
                            },
                        },
                    )
                )

                fig_gauge.update_layout(
                    height=280,
                    margin=dict(l=20, r=20, t=30, b=50),
                    paper_bgcolor="rgba(0,0,0,0)",
                    font={"color": "#1a1a1a", "family": "Arial", "size": 11},
                )

                st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False})

                # Calculate percentile
                percentile = (all_scores["nutrition_score"] < nutri_score).sum() / len(all_scores) * 100
                st.markdown(
                    f"<div style='text-align: center; margin-top: -50px;'>"
                    f"<p style='font-size: 0.85rem; color: #666; margin-bottom: 2px;'>Cette recette est meilleure que <b>{percentile:.1f}%</b> des recettes du dataset</p>"
                    f"<p style='font-size: 0.75rem; color: #999; margin-top: 0;'>Score plus élevé = meilleure qualité nutritionnelle</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            with col2:
                # Nutrition Table with Score
                st.markdown(
                    f"<div style='background: #f8f9fa; padding: 1rem; border-radius: 10px;'>"
                    f"<h4 style='margin-top: 0; color: #1a1a1a;'>Valeurs Nutritionnelles</h4>"
                    f"<table style='width: 100%; border-collapse: collapse;'>"
                    f"<tr style='border-bottom: 2px solid #dee2e6;'><td style='padding: 0.5rem; font-weight: bold;'>Nutri-Score</td><td style='padding: 0.5rem; text-align: right; font-weight: bold; color: {gauge_color};'>{nutri_score:.2f} ({nutri_grade})</td></tr>"
                    f"<tr style='border-bottom: 1px solid #dee2e6;'><td style='padding: 0.5rem;'>Calories</td><td style='padding: 0.5rem; text-align: right;'>{calories_nutr:.0f} kcal</td></tr>"
                    f"<tr style='border-bottom: 1px solid #dee2e6;'><td style='padding: 0.5rem;'>Lipides totaux</td><td style='padding: 0.5rem; text-align: right;'>{total_fat:.1f}% AJR</td></tr>"
                    f"<tr style='border-bottom: 1px solid #dee2e6;'><td style='padding: 0.5rem;'>Lipides saturés</td><td style='padding: 0.5rem; text-align: right;'>{saturated_fat:.1f}% AJR</td></tr>"
                    f"<tr style='border-bottom: 1px solid #dee2e6;'><td style='padding: 0.5rem;'>Glucides</td><td style='padding: 0.5rem; text-align: right;'>{carbohydrates:.1f}% AJR</td></tr>"
                    f"<tr style='border-bottom: 1px solid #dee2e6;'><td style='padding: 0.5rem;'>Sucre</td><td style='padding: 0.5rem; text-align: right;'>{sugar:.1f}% AJR</td></tr>"
                    f"<tr style='border-bottom: 1px solid #dee2e6;'><td style='padding: 0.5rem;'>Protéines</td><td style='padding: 0.5rem; text-align: right;'>{protein:.1f}% AJR</td></tr>"
                    f"<tr><td style='padding: 0.5rem;'>Sodium</td><td style='padding: 0.5rem; text-align: right;'>{sodium:.1f}% AJR</td></tr>"
                    f"</table>"
                    f"<p style='font-size: 0.75rem; color: #666; margin-top: 0.5rem; margin-bottom: 0;'>AJR = Apport Journalier Recommandé</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            # Bar chart comparing with dataset means - Limited to key nutrients
            st.markdown("#### Comparaison avec la Moyenne du Dataset")

            # Limit to key nutrients only
            key_nutrients = {
                "Calories": calories_nutr,
                "Protéines": protein,
                "Lipides": total_fat,
                "Sucre": sugar,
                "Sodium": sodium,
            }

            key_means = {"Calories": 473.94, "Protéines": 34.68, "Lipides": 36.08, "Sucre": 84.30, "Sodium": 30.15}

            nutrients = list(key_nutrients.keys())
            recipe_vals = list(key_nutrients.values())
            dataset_vals = list(key_means.values())

            # Calculate max value for proper scaling
            max_val = max(max(recipe_vals), max(dataset_vals)) * 1.15  # Add 15% padding for text labels

            fig_bar = go.Figure()

            fig_bar.add_trace(
                go.Bar(
                    name="Cette Recette",
                    x=nutrients,
                    y=recipe_vals,
                    marker_color="#667eea",
                    text=[f"{v:.1f}" for v in recipe_vals],
                    textposition="outside",
                    hovertemplate="%{x}: %{y:.1f}<extra></extra>",
                )
            )

            fig_bar.add_trace(
                go.Bar(
                    name="Moyenne Dataset",
                    x=nutrients,
                    y=dataset_vals,
                    marker_color="#dc3545",
                    opacity=0.6,
                    text=[f"{v:.1f}" for v in dataset_vals],
                    textposition="outside",
                    hovertemplate="%{x}: %{y:.1f}<extra></extra>",
                )
            )

            fig_bar.update_layout(
                barmode="group",
                xaxis_title="",
                yaxis_title="Valeur",
                height=400,
                margin=dict(l=40, r=40, t=30, b=60),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font={"color": "#1a1a1a", "family": "Arial", "size": 12},
                xaxis={"tickangle": 0, "tickfont": {"size": 12}},
                yaxis={"range": [0, max_val], "fixedrange": False},
                legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="center", x=0.5, font={"size": 11}),
                showlegend=True,
                autosize=True,
            )

            fig_bar.update_yaxes(
                gridcolor="rgba(200,200,200,0.3)", zeroline=True, zerolinecolor="rgba(200,200,200,0.5)"
            )

            st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

            # Add explanation note
            st.markdown(
                "<p style='font-size: 0.8rem; color: #666; text-align: center; margin-top: -10px;'>"
                "Calories en kcal | Autres nutriments en % de l'Apport Journalier Recommandé"
                "</p>",
                unsafe_allow_html=True,
            )

        else:
            st.info("Données nutritionnelles détaillées non disponibles pour cette recette.")
    except Exception as e:
        st.warning(f"Impossible de charger les données nutritionnelles: {str(e)}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")

    # Recommandations - Better aligned with spacing
    recommendations_header = "<h2 style='text-align: center; color: #667eea; font-size: 2rem; margin: 2rem 0 1.5rem 0;'>🌟 Recettes similaires</h2>"
    st.markdown(recommendations_header, unsafe_allow_html=True)

    with st.spinner("Calcul des recommandations..."):
        recommendations = recommender.get_similar_recipes(
            recipe_id, k=4
        )  # Réduit de 8 à 4 pour meilleures performances

    if recommendations:
        cols = st.columns(4, gap="medium")
        for j, col in enumerate(cols):
            if j < len(recommendations):
                recipe, score = recommendations[j]
                with col:
                    render_recipe_card_mini(recipe)
                    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

                    # Bouton pour voir cette recette
                    if st.button(
                        "📖 Voir la recette",
                        key=f"view_rec_{recipe['id']}",
                        use_container_width=True,
                        type="primary",
                    ):
                        if on_view_similar:
                            on_view_similar(recipe["id"])

    # Bouton retour en bas
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("← Retour à la recherche", key="back_bottom", use_container_width=False):
        if "recipe_id_to_view" in st.session_state:
            del st.session_state.recipe_id_to_view
        if "current_recipe_id" in st.session_state:
            del st.session_state.current_recipe_id
        st.switch_page("app.py")
