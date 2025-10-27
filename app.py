"""Application Streamlit de recherche et analyse de recettes."""

import ast
import logging
import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from components.filters_panel import render_filters_panel
from services.data_loader import filter_recipes, load_recipes
from services.recommender import get_recommender
from utils.navigation import navigate_to_recipe

# Configuration
# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Create log filename with timestamp for this session
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"logs/app_{timestamp}.log"

# Configure logging with both file and console handlers
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(),  # Log to console
    ],
)
logger = logging.getLogger(__name__)

logger.info(f"Application started. Logging to {log_filename}")
logger.info(f"Environment: {os.getenv('STREAMLIT_ENV', 'dev')}")

# Constantes
ITEMS_PER_PAGE = 12
NUTRISCORE_COLORS = {
    "A": "#238B45",
    "B": "#85BB2F",
    "C": "#FECC00",
    "D": "#FF9500",
    "E": "#E63946",
}
VEGAN_KEYWORDS = {
    "vegan",
    "vegetarian",
    "veggie",
    "plant-based",
    "plant based",
    "végétarien",
    "végétalien",
    "végan",
    "sans viande",
    "meatless",
}
MEAT_KEYWORDS = {
    "beef",
    "boeuf",
    "pork",
    "porc",
    "chicken",
    "poulet",
    "turkey",
    "dinde",
    "lamb",
    "agneau",
    "veal",
    "veau",
    "duck",
    "canard",
    "fish",
    "poisson",
    "salmon",
    "saumon",
    "tuna",
    "thon",
    "shrimp",
    "crevette",
    "meat",
    "viande",
    "bacon",
    "ham",
    "jambon",
    "sausage",
    "saucisse",
    "steak",
    "ground beef",
    "meatball",
    "boulette",
    "liver",
    "foie",
    "ribs",
    "côtes",
    "chorizo",
    "seafood",
    "fruits de mer",
}

st.set_page_config(
    page_title="Mangetamain - Recettes & Analyses",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Masquer sidebar
st.markdown(
    """<style>
    [data-testid="stSidebar"], [data-testid="stSidebarCollapseButton"] {
        display: none !important;
    }
    </style>""",
    unsafe_allow_html=True,
)


def inject_global_styles() -> None:
    """Injecte les styles CSS globaux."""
    st.markdown(
        """<style>
    /* Boutons principaux */
    div[data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(90deg, #ff4b5c 0%, #ff6b7a 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.5rem !important;
        font-size: 0.95rem !important;
        transition: all 0.3s ease !important;
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(255, 75, 92, 0.4) !important;
    }
    /* Cartes de recettes */
    .recipe-card {
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .recipe-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.2) !important;
    }
    </style>""",
        unsafe_allow_html=True,
    )


def render_simple_pagination(total_results: int, per_page: int, current_page: int) -> int:
    """Affiche pagination simple et élégante."""
    st.markdown(
        """
    <style>
    /* Conteneur de pagination centré */
    .stButton > button {
        background-color: transparent !important;
        border: none !important;
        color: #333 !important;
        font-size: 1rem !important;
        padding: 0.5rem 0.75rem !important;
        margin: 0 0.25rem !important;
        border-radius: 4px !important;
        transition: all 0.2s ease !important;
        min-width: 40px !important;
        height: 40px !important;
    }

    /* Effet survol sur les numéros de page */
    .stButton > button:hover:not(:disabled) {
        background-color: rgba(255, 75, 75, 0.1) !important;
        text-decoration: underline !important;
        transform: translateY(-1px) !important;
    }

    /* Page active (disabled = current) */
    .stButton > button:disabled {
        background-color: transparent !important;
        color: #ff4b4b !important;
        font-weight: 700 !important;
        text-decoration: none !important;
        cursor: default !important;
    }

    /* Bouton "Suivant" spécial (type primary) */
    .stButton > button[kind="primary"] {
        background-color: #ff4b4b !important;
        color: white !important;
        border-radius: 50px !important;
        padding: 0.5rem 1.25rem !important;
        font-weight: 600 !important;
        min-width: auto !important;
    }

    .stButton > button[kind="primary"]:hover:not(:disabled) {
        background-color: #ff3333 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(255, 75, 75, 0.3) !important;
        text-decoration: none !important;
    }

    .stButton > button[kind="primary"]:disabled {
        background-color: #ccc !important;
        color: #666 !important;
        cursor: not-allowed !important;
        transform: none !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    if total_results < 0 or per_page <= 0 or current_page < 1:
        raise ValueError("Paramètres invalides")

    total_pages = max(1, (total_results - 1) // per_page + 1)
    current_page = max(1, min(current_page, total_pages))

    page_numbers = []

    if total_pages <= 10:
        page_numbers = list(range(1, total_pages + 1))
    else:
        page_numbers.append(1)
        window_start = max(2, current_page - 2)
        window_end = min(total_pages - 1, current_page + 2)

        if window_start > 2:
            page_numbers.append("...")

        for i in range(window_start, window_end + 1):
            if i not in page_numbers:
                page_numbers.append(i)

        if window_end < total_pages - 1:
            page_numbers.append("...")

        if total_pages not in page_numbers:
            page_numbers.append(total_pages)

    num_buttons = len(page_numbers) + 1
    cols = st.columns([0.3] + [0.7] * num_buttons + [0.3])
    selected_page = current_page

    for idx, page_item in enumerate(page_numbers):
        with cols[idx + 1]:
            if page_item == "...":
                st.markdown(
                    "<p style='text-align: center; color: #999; margin: 0.5rem 0;'>…</p>",
                    unsafe_allow_html=True,
                )
            else:
                page_num = int(page_item)
                is_current = page_num == current_page

                if st.button(
                    str(page_num),
                    key=f"pg_{page_num}",
                    disabled=is_current,
                    help=f"Aller à la page {page_num}",
                ):
                    selected_page = page_num

    with cols[len(page_numbers) + 1]:
        suivant_disabled = current_page >= total_pages
        if st.button(
            "▶ Suivant",
            key="pg_next",
            disabled=suivant_disabled,
            type="primary",
            help="Page suivante",
        ):
            selected_page = current_page + 1

    return selected_page


def render_recipe_card(recipe: pd.Series, recipe_id: int) -> None:
    """Génère et affiche une carte de recette stylisée."""
    try:
        recipe_name = recipe.get("name", f"Recette #{int(recipe.get('id', 0))}")
        display_name = recipe_name if len(recipe_name) <= 60 else recipe_name[:57] + "..."

        nutri_grade = recipe.get("nutrition_grade", "C")
        nutri_score = float(recipe.get("nutrition_score", 50))
        nutri_color = NUTRISCORE_COLORS.get(nutri_grade, "#7f8c8d")

        is_veg = recipe.get("is_vegetarian", False)
        prep_time = int(recipe.get("minutes", 30))
        n_ingredients = int(recipe.get("n_ingredients", 0))

        tags = []

        # Tag temps de préparation
        if prep_time >= 120:
            tags.append((f"🍲 Longue ({prep_time} min)", "#d9534f"))
        elif prep_time <= 30:
            tags.append((f"⚡ Rapide ({prep_time} min)", "#007bff"))
        elif prep_time <= 60:
            tags.append((f"⏱️ Moyen ({prep_time} min)", "#ffc107"))

        # Tag nombre d'ingrédients
        if n_ingredients > 0:
            if n_ingredients <= 5:
                tags.append((f"🥗 Simple ({n_ingredients} ingr.)", "#17a2b8"))
            elif n_ingredients <= 10:
                tags.append((f"🥘 Modéré ({n_ingredients} ingr.)", "#6c757d"))
            else:
                tags.append((f"👨‍🍳 Élaboré ({n_ingredients} ingr.)", "#6f42c1"))

        # Tag végétarien
        if is_veg:
            tags.append(("🌱 Végétarien", "#28a745"))

        tags_html = " ".join(
            [
                f'<span style="background-color: {color}; color: white; padding: 4px 10px; '
                f"border-radius: 12px; font-size: 0.75rem; margin-right: 5px; display: inline-block; "
                f'vertical-align: middle; white-space: nowrap;">{tag}</span>'
                for tag, color in tags
            ]
        )

        # Description
        description = "Découvrez cette délicieuse recette..."
        if "description" in recipe and pd.notna(recipe["description"]):
            desc_text = str(recipe["description"]).strip()
            description = desc_text[:80] + ("..." if len(desc_text) > 80 else "")
        elif "steps" in recipe and recipe["steps"]:
            try:
                steps_text = recipe["steps"]
                if isinstance(steps_text, str) and steps_text.startswith("["):
                    steps_list = ast.literal_eval(steps_text)
                    if steps_list:
                        first_step = str(steps_list[0])[:80]
                        description = first_step + ("..." if len(first_step) == 80 else "")
            except (ValueError, SyntaxError) as e:
                logger.warning(f"Error parsing steps for recipe {recipe_id}: {e}")

        # Rating avec nombre d'avis
        rating = float(recipe.get("average_rating", 4.0))
        review_count = int(recipe.get("review_count", 0))
        full_stars = int(rating)
        half_star = (rating - full_stars) >= 0.5
        empty_stars = 5 - full_stars - int(half_star)

        stars_html = "⭐" * full_stars + ("✨" if half_star else "") + "☆" * empty_stars
        
        # Affichage avec nombre d'avis si disponible
        if review_count > 0:
            rating_display = (  # noqa: E501
                f'<div style="margin-top: 0.5rem; font-size: 0.9rem; color: #ffc107;">'
                f'{stars_html} <span style="color: #e0e0e0;">{rating:.1f}/5 ({review_count} avis)</span></div>'
            )
        else:
            rating_display = (  # noqa: E501
                f'<div style="margin-top: 0.5rem; font-size: 0.9rem; color: #ffc107;">'
                f'{stars_html} <span style="color: #e0e0e0;">{rating:.1f}/5</span></div>'
            )

        # Carte HTML
        card_html = f"""
        <div class="recipe-card" style="
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            margin-bottom: 1.5rem;
            background: white;
            height: 420px;
            display: flex;
            flex-direction: column;
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
            ">
                <div title="Score: {nutri_score:.2f}" style="
                    position: absolute;
                    top: 12px;
                    right: 12px;
                    background-color: {nutri_color};
                    color: #1a1a1a;
                    font-weight: bold;
                    font-size: 16px;
                    padding: 3px 10px;
                    border-radius: 4px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                ">{nutri_grade}</div>
                <div style="color: rgba(255,255,255,0.5); font-size: 3rem;"
                     title="Image à venir" aria-label="Placeholder">🍽️</div>
            </div>
            <div style="background: #2c2c2c; padding: 1rem; color: white;
                        height: 220px; flex-shrink: 0; display: flex; flex-direction: column;">
                <div style="margin-bottom: 0.7rem; min-height: 28px;">{tags_html}</div>
                <h3 style="margin: 0 0 0.5rem 0; font-size: 1.25rem; color: white;
                           font-weight: 700; line-height: 1.3; flex-shrink: 0;">{display_name}</h3>
                <p style="margin: 0; font-size: 0.85rem; color: #b0b0b0;
                          line-height: 1.4; overflow: hidden;">{description}</p>
                {rating_display}
            </div>
        </div>
        """

        st.markdown(card_html, unsafe_allow_html=True)

    except Exception as e:
        logger.error(f"Error rendering recipe card for recipe {recipe_id}: {e}")
        st.error(f"Unable to display recipe #{recipe_id}")


def page_recherche(recipes_df: pd.DataFrame, recommender) -> None:
    """Page de recherche avec filtres et pagination."""
    header_html = (
        "<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); "
        "padding: 3rem 2rem; border-radius: 15px; margin-bottom: 2rem; text-align: center; "
        "color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>"
        "<h1 style='font-size: 2.5rem; margin-bottom: 0.5rem; font-weight: 700;'>"
        "🍽️ Des recettes et des actus culinaires"
        "</h1>"
        "<p style='font-size: 1.2rem; margin: 0; opacity: 0.95;'>"
        "Plus de 90 000 recettes faciles et rapides pour vous inspirer en cuisine."
        "</p>"
        "</div>"
    )
    st.markdown(header_html, unsafe_allow_html=True)

    # Barre de recherche par mots-clés
    st.markdown("### 🔍 Recherche par mots-clés")
    col_search, col_button = st.columns([4, 1])
    with col_search:
        search_query = st.text_input(
            "Rechercher une recette",
            placeholder="Ex: chicken pasta, chocolate cake, vegan salad... (en anglais)",
            help="Recherchez par mots-clés dans le nom, les ingrédients et les étapes des recettes",
            key="search_input",
        )
    with col_button:
        if st.button("🔍 Rechercher", type="primary"):
            st.session_state.current_page = 1  # Reset pagination

    # Bouton Filtres avancés
    if "show_filters" not in st.session_state:
        st.session_state.show_filters = False

    if st.button(
        "🎯 Filtres avancés" if not st.session_state.show_filters else "✖️ Masquer les filtres",
        use_container_width=False,
    ):
        st.session_state.show_filters = not st.session_state.show_filters

    # Afficher les filtres si le bouton est activé
    if st.session_state.show_filters:
        filters = render_filters_panel(in_sidebar=False)
    else:
        # Filtres par défaut quand fermés
        filters = {
            "prep": [0, 300],
            "ingredients": [1, 45],
            "calories": [0, 2000],
            "vegetarian_only": False,
            "nutrition_grades": [],
        }

    # Réinitialiser la pagination si les filtres changent
    if "last_filters" not in st.session_state:
        st.session_state.last_filters = filters
    elif st.session_state.last_filters != filters:
        st.session_state.current_page = 1
        st.session_state.last_filters = filters

    # Appliquer les filtres
    filtered_recipes = filter_recipes(
        recipes_df,
        prep_range=tuple(filters["prep"]),
        ingredients_range=tuple(filters["ingredients"]),
        calories_range=tuple(filters["calories"]),
        vegetarian_only=filters["vegetarian_only"],
        nutrition_grades=filters.get("nutrition_grades", []),
    )

    # Filtrer par recherche textuelle si une requête existe
    if search_query and search_query.strip():
        filtered_recipes = _apply_keyword_search(filtered_recipes, search_query)
    else:
        # Trier par popularité par défaut en utilisant le score combiné
        if "popularity_score" in filtered_recipes.columns:
            # Tri principal par popularity_score, puis par average_rating en cas d'égalité
            filtered_recipes = filtered_recipes.sort_values(
                ["popularity_score", "average_rating"], 
                ascending=[False, False], 
                na_position="last"
            )
        elif "average_rating" in filtered_recipes.columns:
            # Fallback vers average_rating seul si popularity_score n'existe pas
            filtered_recipes = filtered_recipes.sort_values("average_rating", ascending=False, na_position="last")

    # Afficher le nombre de résultats
    total_results = len(filtered_recipes)
    st.markdown(
        f"<p style='font-size: 0.9rem; color: #b0b0b0;'>📚 {total_results} recette(s) trouvée(s)</p>",
        unsafe_allow_html=True,
    )

    if total_results > 0:
        _display_recipes_grid(filtered_recipes, total_results)
    else:
        st.info("😕 Aucune recette ne correspond à vos critères. Ajustez les filtres dans la sidebar.")


def _apply_keyword_search(df: pd.DataFrame, search_query: str) -> pd.DataFrame:
    """Recherche par mots-clés avec scoring et détection auto végé/viande."""
    query_lower = search_query.lower().strip()
    query_words = query_lower.split()

    contains_vegan = any(kw in query_lower for kw in VEGAN_KEYWORDS)
    contains_meat = any(kw in query_lower or any(kw in w for w in query_words) for kw in MEAT_KEYWORDS)

    veg_col = "is_vegetarian"

    if contains_vegan and veg_col in df.columns:
        df = df[df[veg_col].fillna(False)]
    elif contains_meat and veg_col in df.columns:
        df = df[~df[veg_col].fillna(False)]

    def score_recipe(row: pd.Series) -> int:
        score = 0
        name, ingredients, steps = (
            str(row.get("name", "")).lower(),
            str(row.get("ingredients", "")).lower(),
            str(row.get("steps", "")).lower(),
        )
        for word in query_words:
            score += 3 * (word in name) + 2 * (word in ingredients) + (word in steps)
        return score

    df["relevance_score"] = df.apply(score_recipe, axis=1)
    df = df[df["relevance_score"] > 0].sort_values("relevance_score", ascending=False)

    if df.empty:
        st.warning(f"Aucun résultat pour '{search_query}'. Essayez d'autres mots-clés.")

    return df


def _display_recipes_grid(filtered_recipes: pd.DataFrame, total_results: int) -> None:
    """Affiche grille de recettes avec pagination."""
    if "current_page" not in st.session_state:
        st.session_state.current_page = 1

    start_idx = (st.session_state.current_page - 1) * ITEMS_PER_PAGE
    end_idx = min(start_idx + ITEMS_PER_PAGE, total_results)

    display_recipes = filtered_recipes.iloc[start_idx:end_idx]

    n_cols = 2
    for i in range(0, len(display_recipes), n_cols):
        cols = st.columns(n_cols)
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(display_recipes):
                recipe = display_recipes.iloc[idx]
                recipe_id = int(recipe["id"])
                with col:
                    render_recipe_card(recipe, recipe_id)

                    if st.button(
                        "📖 Voir la recette",
                        key=f"view_{recipe_id}",
                        use_container_width=True,
                        type="primary",
                    ):
                        navigate_to_recipe(recipe_id)

    st.markdown("---")
    new_page = render_simple_pagination(total_results, ITEMS_PER_PAGE, st.session_state.current_page)
    if new_page != st.session_state.current_page:
        st.session_state.current_page = new_page
        st.rerun()


def page_analyse(recipes_df: pd.DataFrame) -> None:
    """Page d'analyse statistique des recettes."""
    st.title("📊 Analyse des données")
    st.markdown("**Analyse statistique des recettes**")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("🍽️ Recettes totales", f"{len(recipes_df):,}")

    with col2:
        if "minutes" in recipes_df.columns:
            median_time = recipes_df["minutes"].median()
            st.metric("⏱️ Temps médian", f"{median_time:.0f} min")

    with col3:
        if "n_ingredients" in recipes_df.columns:
            avg_ingredients = recipes_df["n_ingredients"].mean()
            st.metric("🥕 Ingrédients moy.", f"{avg_ingredients:.1f}")

    with col4:
        if "calories" in recipes_df.columns:
            avg_calories = recipes_df["calories"].mean()
            st.metric("🔥 Calories moy.", f"{avg_calories:.0f}")

    st.markdown("---")

    _render_distributions(recipes_df)
    st.markdown("---")
    _render_scatter_plot(recipes_df)
    st.markdown("---")
    _render_stats_table(recipes_df)

    st.markdown("---")
    st.caption("💡 Données du dataset Food.com")


def _render_distributions(recipes_df: pd.DataFrame) -> None:
    """Affiche histogrammes de distribution."""
    st.subheader("📊 Distributions")

    viz_col1, viz_col2 = st.columns(2)

    with viz_col1:
        if "minutes" in recipes_df.columns:
            fig = px.histogram(
                recipes_df[recipes_df["minutes"] <= 180],
                x="minutes",
                nbins=30,
                title="Distribution du temps de préparation",
                labels={"minutes": "Temps (min)", "count": "Nombre de recettes"},
                color_discrete_sequence=["#667eea"],
            )
            fig.update_layout(template="plotly_dark", showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)

    with viz_col2:
        if "n_ingredients" in recipes_df.columns:
            fig = px.histogram(
                recipes_df,
                x="n_ingredients",
                nbins=25,
                title="Distribution du nombre d'ingrédients",
                labels={"n_ingredients": "Nombre d'ingrédients", "count": "Nombre de recettes"},
                color_discrete_sequence=["#764ba2"],
            )
            fig.update_layout(template="plotly_dark", showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)


def _render_scatter_plot(recipes_df: pd.DataFrame) -> None:
    """Affiche scatter plot de relations."""
    st.subheader("🔍 Analyses de relations")

    if all(col in recipes_df.columns for col in ["minutes", "n_ingredients", "calories"]):
        sample_df = recipes_df.sample(n=min(2000, len(recipes_df)), random_state=42)
        sample_df = sample_df[(sample_df["minutes"] <= 300) & (sample_df["calories"] <= 2000)]

        fig = px.scatter(
            sample_df,
            x="minutes",
            y="calories",
            color="n_ingredients",
            title="Relation entre Temps, Calories et Nombre d'ingrédients",
            labels={
                "minutes": "Temps de préparation (min)",
                "calories": "Calories",
                "n_ingredients": "Nb d'ingrédients",
            },
            opacity=0.6,
            color_continuous_scale="Viridis",
        )
        fig.update_layout(template="plotly_dark", height=500)
        st.plotly_chart(fig, use_container_width=True)


def _render_stats_table(recipes_df: pd.DataFrame) -> None:
    """Affiche statistiques descriptives."""
    st.subheader("📋 Statistiques détaillées")

    numeric_cols = []
    col_mapping = {
        "minutes": "Temps (min)",
        "n_ingredients": "Ingrédients",
        "n_steps": "Étapes",
        "calories": "Calories",
        "protein": "Protéines",
        "total_fat": "Lipides",
        "sugar": "Sucre",
        "sodium": "Sodium",
    }

    for col in col_mapping.keys():
        if col in recipes_df.columns:
            numeric_cols.append(col)

    if numeric_cols:
        stats_df = recipes_df[numeric_cols].describe().T
        stats_df.index = [col_mapping.get(idx, idx) for idx in stats_df.index]

        st.dataframe(
            stats_df.style.format("{:.2f}").background_gradient(cmap="Blues"),
            use_container_width=True,
        )


@st.cache_resource
def initialize_app() -> tuple[pd.DataFrame, object]:
    """Load data and initialize recommender."""
    logger.info("Initialization - Loading data")
    recipes_df = load_recipes()
    logger.info(f"Recipes loaded: {len(recipes_df)}")

    recommender = get_recommender(recipes_df)
    logger.info("Recommendation system initialized")

    return recipes_df, recommender


def main():
    # Entry point
    inject_global_styles()
    recipes_df, recommender = initialize_app()

    tab1, tab2 = st.tabs(["🔍 Recherche", "📊 Analyse"])

    with tab1:
        page_recherche(recipes_df, recommender)

    with tab2:
        page_analyse(recipes_df)


if __name__ == "__main__":
    main()
