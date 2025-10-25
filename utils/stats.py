"""
Fonctions utilitaires pour les calculs statistiques.
"""

from typing import List, Tuple

import numpy as np
import pandas as pd
import streamlit as st


@st.cache_data
def compute_quantile_bins(data: List[float], n_quantiles: int = 5) -> Tuple[List[str], List[int]]:
    """
    Calcule les bins basés sur les quantiles pour un histogramme.

    Args:
        data: Liste de valeurs numériques
        n_quantiles: Nombre de quantiles (par défaut 5 pour quintiles)

    Returns:
        Tuple (labels, counts) où labels sont les intervalles et counts le nombre d'éléments
    """
    if len(data) == 0:
        return [], []

    data_array = np.array(data)

    # Calculer les quantiles
    quantiles = np.linspace(0, 100, n_quantiles + 1)
    bins = np.percentile(data_array, quantiles)

    # Compter les éléments dans chaque bin
    counts, _ = np.histogram(data_array, bins=bins)

    # Créer les labels
    labels = []
    for i in range(len(bins) - 1):
        label = f"{bins[i]:.0f}-{bins[i + 1]:.0f}"
        labels.append(label)

    return labels, counts.tolist()


@st.cache_data
def compute_correlation_matrix(_df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """
    Calcule la matrice de corrélation de Pearson pour les colonnes spécifiées.

    Args:
        _df: DataFrame contenant les données
        columns: Liste des noms de colonnes à inclure

    Returns:
        DataFrame contenant la matrice de corrélation
    """
    return _df[columns].corr(method="pearson")


def format_number(value: float, precision: int = 0) -> str:
    """
    Formate un nombre pour l'affichage.

    Args:
        value: Valeur numérique
        precision: Nombre de décimales

    Returns:
        Chaîne formatée
    """
    if precision == 0:
        return f"{value:.0f}"
    return f"{value:.{precision}f}"


def format_time(minutes: float) -> str:
    """
    Formate une durée en minutes en format lisible.

    Args:
        minutes: Durée en minutes

    Returns:
        Chaîne formatée (ex: "1h 30min")
    """
    if minutes < 60:
        return f"{minutes:.0f} min"

    hours = int(minutes // 60)
    mins = int(minutes % 60)

    if mins == 0:
        return f"{hours}h"
    return f"{hours}h {mins:02d}min"


def get_descriptive_stats(data: pd.Series) -> dict:
    """
    Calcule les statistiques descriptives pour une série de données.

    Args:
        data: Série pandas

    Returns:
        Dictionnaire avec les statistiques
    """
    return {
        "count": len(data),
        "mean": data.mean(),
        "median": data.median(),
        "std": data.std(),
        "min": data.min(),
        "max": data.max(),
        "q25": data.quantile(0.25),
        "q75": data.quantile(0.75),
    }
