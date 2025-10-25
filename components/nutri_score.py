"""
Composant pour afficher le Nutri-Score des recettes.
"""

import pandas as pd


def get_nutri_grade(nutrition_score: float) -> str:
    """
    Convertit un score nutritionnel en grade (A, B, C, D, E).

    Le Nutri-Score utilise une échelle de 0-100 où:
    - A (vert): 0-40
    - B (vert clair): 41-55
    - C (jaune): 56-70
    - D (orange): 71-80
    - E (rouge): 81-100

    Args:
        nutrition_score: Score nutritionnel (0-100)

    Returns:
        str: Grade (A, B, C, D, E)
    """
    if pd.isna(nutrition_score):
        return "C"  # Grade par défaut

    score = float(nutrition_score)

    if score <= 40:
        return "A"
    elif score <= 55:
        return "B"
    elif score <= 70:
        return "C"
    elif score <= 80:
        return "D"
    else:
        return "E"


def get_nutri_color(grade: str) -> str:
    """
    Retourne la couleur associée à un grade Nutri-Score.

    Args:
        grade: Grade (A, B, C, D, E)

    Returns:
        str: Couleur hexadécimale
    """
    colors = {
        "A": "#238B45",  # Vert foncé
        "B": "#85BB2F",  # Vert clair
        "C": "#FECC00",  # Jaune
        "D": "#FF9500",  # Orange
        "E": "#E63946",  # Rouge
    }
    return colors.get(grade, "#7f8c8d")


def display_nutri_score_badge(grade: str, size: str = "large") -> str:
    """
    Affiche le badge Nutri-Score en HTML/CSS.

    Args:
        grade: Grade (A, B, C, D, E)
        size: Taille ('small', 'medium', 'large')

    Returns:
        str: HTML du badge
    """
    color = get_nutri_color(grade)

    if size == "small":
        font_size = "16px"
        padding = "4px 12px"
    elif size == "medium":
        font_size = "20px"
        padding = "8px 16px"
    else:  # large
        font_size = "24px"
        padding = "12px 20px"

    html = f"""
    <div style="
        display: inline-block;
        background-color: {color};
        color: white;
        font-weight: bold;
        font-size: {font_size};
        padding: {padding};
        border-radius: 8px;
        text-align: center;
        min-width: 50px;
    ">
        {grade}
    </div>
    """
    return html


def display_nutri_score_scale() -> str:
    """
    Affiche l'échelle Nutri-Score complète.

    Returns:
        str: HTML de l'échelle
    """
    html = """
    <div style="
        display: flex;
        gap: 2px;
        margin: 10px 0;
        align-items: center;
    ">
        <div style="color: #888; font-size: 12px; margin-right: 10px;">Nutri-Score:</div>
    """

    grades = ["A", "B", "C", "D", "E"]
    for grade in grades:
        color = get_nutri_color(grade)
        html += f"""
        <div style="
            background-color: {color};
            color: white;
            font-weight: bold;
            font-size: 14px;
            padding: 6px 10px;
            border-radius: 4px;
            text-align: center;
            min-width: 40px;
        ">
            {grade}
        </div>
        """

    html += "</div>"
    return html


def render_nutri_score_in_card(grade: str, score: float = None) -> str:
    """
    Crée le HTML pour afficher le Nutri-Score dans une carte de recette.

    Args:
        grade: Grade (A, B, C, D, E)
        score: Score nutritionnel optionnel (pour affichage)

    Returns:
        str: HTML formaté
    """
    color = get_nutri_color(grade)

    html = f"""
    <div style="
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 8px;
        padding: 8px;
        background-color: #f5f5f5;
        border-radius: 6px;
    ">
        <span style="font-size: 12px; color: #666;">Nutri-Score:</span>
        <div style="
            background-color: {color};
            color: white;
            font-weight: bold;
            font-size: 16px;
            padding: 4px 12px;
            border-radius: 6px;
            min-width: 40px;
            text-align: center;
        ">
            {grade}
        </div>
    """

    if score is not None and not pd.isna(score):
        html += f'<span style="font-size: 11px; color: #999;">({score:.0f}/100)</span>'

    html += "</div>"
    return html
