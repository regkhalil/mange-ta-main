# Analytics Module - Nutrition Profiling

## Overview
Comprehensive statistical analysis system for healthy recipe profiling with 5 modular sections.

## Structure
```
components/analytics/
├── __init__.py                    # Package init
├── nutrition_profiling.py         # Section 1: Grade distribution & correlations
├── time_analysis.py               # Section 2: Time vs health
├── ingredient_health.py           # Section 3: Ingredient health index
├── complexity_analysis.py         # Section 4: Complexity vs healthiness
└── global_overview.py             # Section 5: Multi-dimensional insights

pages/
└── 03_📊_Profil_Nutrition.py     # Main page with 5 tabs
```

## Features by Section

### Section 1: Profil Nutritionnel
- Grade distribution histogram (with vegetarian filter)
- Spearman correlation matrix between nutrients
- Mean nutrient %DV per grade
- Box plots of nutrient distributions by grade

### Section 2: Temps vs Santé
- Scatter plot: time vs score with trendline & correlation
- Bar chart: average score per time category
- Stacked bar: grade distribution per time category

### Section 3: Ingrédients
- Scatter: ingredient frequency vs avg score
- Tables: Top 20 healthiest/unhealthiest ingredients
- **Sugar vs Salt comparison**:
  - Scatter: sugar vs sodium colored by score
  - Box plots: score distribution for high/low sugar and sodium
  - Bar chart: average scores comparison

### Section 4: Complexité
- Complexity index: weighted combination of steps (40%) + ingredients (40%) + time (20%)
- Scatter: complexity vs score
- Bar chart: score by complexity category (Simple/Moyen/Complexe)
- Bar chart: individual factor correlations
- Heatmap: score by steps × ingredients

### Section 5: Vue Globale
- **KPI Dashboard**: Total recipes, avg score, % Grade A, % healthy (A+B), % vegetarian
- Feature importance chart: which factors most correlate with score
- Radar chart: healthy (A/B) vs unhealthy (D/E) nutrient profiles
- Sankey diagram: time category → grade flow
- 3D scatter: time × complexity × score

## Performance
- **Data loading**: Cached (loads once per session)
- **Ingredient parsing**: ~2-3 seconds first time (cached after)
- **All other visualizations**: < 1 second each
- **Total page load**: ~3-5 seconds

## Modularity
Each section is independent:
- Delete `time_analysis.py` → Remove time analysis tab
- Delete `ingredient_health.py` → Remove ingredient analysis tab
- Comment out tab in main page → Hide section

## Dependencies
- `scipy`: Statistical tests (already in scikit-learn)
- `pandas`, `plotly`, `streamlit`, `numpy`: Already installed
- **No heavy dependencies like statsmodels**

## Usage
```bash
make start  # Run Streamlit app
# Navigate to "📊 Profil Nutrition" page
```

## Key Insights Provided
1. **Nutrition patterns**: Which nutrients correlate with high scores?
2. **Time factor**: Do quick recipes score better?
3. **Ingredient analysis**: Which ingredients make recipes healthy/unhealthy?
4. **Sugar vs Salt**: Which has more negative impact?
5. **Complexity**: Are simpler recipes healthier?
6. **Multi-dimensional**: How do all factors interact?

## Vegetarian Analysis
Toggle in Section 1 applies to:
- Grade distribution histogram
- Nutrient box plots

Shows if vegetarian recipes have different nutrition profiles.
