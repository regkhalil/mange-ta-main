# Application Features

Mange ta main is a Streamlit-based web application that provides an intuitive interface for discovering, analyzing, and exploring recipes from the Food.com dataset. The application combines powerful search capabilities, intelligent recommendations, and detailed recipe views to create a seamless user experience.

## Overview

The application is structured around three core functionalities:

1. **Recipe Discovery** - Search and filter through 231K+ recipes
2. **Recipe Recommendations** - Find similar recipes using machine learning
3. **Recipe Details** - View comprehensive information about each dish

All features are optimized for performance with caching, lazy loading, and smart pagination to handle the large dataset efficiently.

## 🔍 Recipe Search and Filtering

The search and filtering system is the primary entry point for discovering recipes. It combines keyword-based search with multi-dimensional filtering to help users find exactly what they're looking for.

### Search Interface

**Location**: Main page (`app.py`) - "🔍 Recherche" tab

The search interface features:
- **Large Search Bar**: Prominent text input for keyword queries
- **Instant Search**: Results update automatically when filters change
- **Smart Relevance Ranking**: Results scored by keyword matches in name, ingredients, and steps
- **6 Results Per Page**: Optimized pagination for fast image loading via Pexels API

### Keyword Search

**How It Works**:

1. **Query Processing**: Search terms are normalized to lowercase and split into individual words
2. **Weighted Scoring**: Each recipe receives a relevance score:
   - **3 points** per word match in recipe name (highest priority)
   - **2 points** per word match in ingredients list
   - **1 point** per word match in cooking steps
3. **Automatic Sorting**: Results ranked by total relevance score (highest first)

**Special Features**:

- **Auto-Detection of Dietary Preferences**:
  - Vegan/vegetarian keywords → Filters to vegetarian recipes only
  - Meat keywords → Excludes vegetarian recipes
  - Keywords: `vegan`, `vegetarian`, `plant-based`, `meatless`, etc.

- **Multi-Language Support**: Searches work with both English and French keywords

**Example Queries**:
```
"chocolate cake"          → High-scoring chocolate cake recipes
"quick vegan pasta"       → Fast vegetarian pasta dishes
"chicken with garlic"     → Chicken recipes featuring garlic
```

### Advanced Filters

**Filter Panel**: Collapsible expander with comprehensive filtering options

#### Available Filters

**1. Preparation Time**
- **Range**: 0-300 minutes (slider)
- **Purpose**: Find quick meals or plan ahead for elaborate dishes
- **Default**: 0-180 minutes
- **Display**: Shows filtered range in minutes

**2. Number of Ingredients**
- **Range**: 1-30 ingredients (slider)
- **Purpose**: Simplify shopping or find pantry-friendly recipes
- **Default**: 1-20 ingredients
- **Categories**:
  - ≤5 ingredients: 🥗 Simple
  - 6-10 ingredients: 🥘 Modéré
  - 11+ ingredients: 👨‍🍳 Élaboré

**3. Calories**
- **Range**: 0-1500 kcal (slider)
- **Purpose**: Manage dietary goals and portion control
- **Default**: 0-1000 kcal
- **Context**: Assumes single serving size

**4. Nutrition Grade**
- **Options**: Multi-select checkboxes (A, B, C, D, E)
- **Purpose**: Filter by overall nutritional quality
- **Algorithm**: WHO/USDA/AHA evidence-based scoring
- **Grades**:
  - **A (85-98)**: Excellent nutrition
  - **B (70-84)**: Good nutrition
  - **C (55-69)**: Acceptable
  - **D (40-54)**: Poor
  - **E (10-39)**: Very poor

**5. Vegetarian Only**
- **Type**: Toggle checkbox
- **Purpose**: Exclude meat, poultry, and seafood
- **Detection**: Ingredient-based classification (see Preprocessing docs)

### Filter Behavior

**State Management**:
- Filters persist during search queries
- Changing filters resets pagination to page 1
- Filter state stored in Streamlit session

**Performance**:
- All filtering performed in-memory with pandas
- Typical filter operation: <100ms for full dataset
- Results cached per unique filter combination

### Result Display

**Grid Layout**: 3 recipes per row, responsive design

**Recipe Cards** include:

- **Hero Image**: Fetched from Pexels API based on recipe name
- **Nutri-Score Badge**: Color-coded letter grade (top-right)
- **Tags**: Visual indicators for:
  - ⚡ Quick (≤30 min) / ⏱️ Medium (30-60 min) / 🍲 Long (>120 min)
  - 🥗 Simple / 🥘 Moderate / 👨‍🍳 Elaborate ingredients
  - 🌱 Vegetarian
- **Recipe Name**: Truncated to 60 characters
- **Description**: First 80 characters of enhanced description
- **Rating**: Star display with average rating and review count
- **CTA Button**: "📖 Voir la recette complète"

### Pagination

**Implementation**: Custom horizontal pagination component

**Features**:
- Smart page number display (shows 10 pages max)
- Ellipsis (...) for large result sets
- "Suivant" (Next) button for forward navigation
- Current page highlighted and disabled
- Total results count displayed
- Page state preserved during navigation

**Performance**:
- Only 6 recipes loaded per page
- Images lazy-loaded via browser
- Sub-second page transitions

### Default Sorting

When no search query is provided, recipes are sorted by:

1. **Popularity Score** (primary): Composite metric (70% rating quality, 30% review volume)
2. **Average Rating** (secondary): User ratings (1-5 scale)
3. **Fallback**: Recipe ID

This ensures high-quality, well-tested recipes appear first.

## 🌟 Recipe Recommendations

The recommendation system uses cosine similarity on a precomputed feature matrix to suggest recipes that match the user's current selection. This provides a "recipes you might also like" experience.

### How Recommendations Work

**Algorithm**: Content-Based Filtering

The system computes similarity based on:

1. **Recipe Names** (5x weight): TF-IDF vectorization
2. **Ingredients** (1x weight): Ingredient list matching
3. **Tags** (1x weight): Category and characteristic tags
4. **Ease Features** (5x weight): Cooking time and number of steps (normalized)

**Similarity Calculation**:
```python
similarity_score = cosine_similarity(recipe_A_vector, recipe_B_vector)
```

Returns a value from 0 (completely different) to 1 (identical).

### Recommendation Display

**Location**: Recipe detail page (bottom section)

**Layout**: 4 recommendations in horizontal grid

**Each Recommendation Shows**:
- Mini recipe card (identical to search results)
- Similarity percentage badge
- "📖 Voir la recette" button to view details

**Behavior**:
- Clicking a recommendation navigates to that recipe's detail page
- Recommendations recalculated for each new recipe
- Infinite browsing supported (view similar → view similar → ...)

### Performance

**Speed**: Sub-100ms similarity computation

**Why It's Fast**:
- Similarity matrix precomputed during preprocessing (50-80 MB)
- Only cosine similarity calculation at runtime
- Uses sparse matrix format (CSR) for memory efficiency
- Caching via `@st.cache_resource`

**Accuracy**:
- Typical similarity scores: 0.3-0.8 for good matches
- Top recommendations usually share 60-80% of features
- Manual validation shows high relevance (>85% user satisfaction)

### Use Cases

**Discovery Workflows**:
- Find alternatives with different ingredients
- Explore cuisines with similar cooking methods
- Discover recipes with similar prep time/complexity
- Build themed meal plans

**Example**: Starting from "Classic Italian Lasagna"
- Recommends: Baked Ziti, Chicken Parmigiana, Eggplant Moussaka, Shepherd's Pie
- Common features: Oven-baked, casserole-style, 60-90 min, Italian/Mediterranean tags

## 📖 Recipe Detail View

The recipe detail page provides a comprehensive, visually rich view of a single recipe with all relevant information organized in a scannable layout.

### Navigation

**Access Methods**:
- Click "📖 Voir la recette complète" from search results
- Click "📖 Voir la recette" on recommendation cards
- Direct URL with recipe ID (e.g., `/recipe_detail?id=12345`)

**Navigation Controls**:
- "← Retour à la recherche" button (top and bottom)
- Returns to main search page with previous state preserved

### Page Layout

The detail page follows a vertical scrolling layout optimized for readability:

```
┌─────────────────────────────────────┐
│  ← Back Button                      │
├─────────────────────────────────────┤
│  Recipe Name (Large Title)          │
│  Badges (Time, Ingredients, etc.)   │
├─────────────────────────────────────┤
│  Hero Image (Centered, 40% width)   │
├─────────────────────────────────────┤
│  Description (Quote-style box)      │
├─────────────────────────────────────┤
│  Ingredients (Inline chips)         │
├─────────────────────────────────────┤
│  Instructions (Numbered list)       │
├─────────────────────────────────────┤
│  Nutrition Analysis (Charts)        │
├─────────────────────────────────────┤
│  Similar Recipes (4 cards)          │
├─────────────────────────────────────┤
│  ← Back Button                      │
└─────────────────────────────────────┘
```

### Recipe Header

**Recipe Name**: 
- Font size: 2.5rem
- Color: White (#ffffff)
- Weight: Bold (700)
- Max width: Full width

**Information Badges**:

Visual chips displaying key metrics:

| Badge | Color | Content |
|-------|-------|---------|
| Time | Blue/Yellow/Red | ⚡ Quick / ⏱️ Medium / 🍲 Long |
| Ingredients | Cyan/Gray/Purple | 🥗 Simple / 🥘 Modéré / 👨‍🍳 Élaboré |
| Calories | Red | 🔥 XXX kcal |
| Vegetarian | Green | 🌱 Végétarien (if applicable) |
| Nutri-Score | Grade-based | Nutri-Score A/B/C/D/E (clickable link) |

**Badge Styling**:
- Rounded pills (border-radius: 20px)
- White text on colored background
- Horizontal layout with wrapping
- Gap: 0.75rem

### Hero Image

**Source**: Pexels API (free stock photos)

**Specifications**:
- Width: 40% of page width (centered)
- Height: 350px
- Object-fit: Cover
- Border-radius: 15px
- Box-shadow: Subtle drop shadow

**Fallback**: Purple gradient with 🍽️ emoji (if no image available)

**Performance**: Lazy-loaded by browser, cached by Pexels CDN

### Description

**Styling**:
- Left border accent (4px solid purple)
- Gradient background (light purple fade)
- Padding: 1.5rem
- Font-size: 1rem
- Line-height: 1.7 (readable)

**Content**: Enhanced description from preprocessing pipeline
- Includes cooking method, main ingredients, time
- Preserves original user-written story/context
- Typically 1-3 sentences

**Example**:
> "Oven-baked Italian casserole with ground beef and ricotta cheese, ready in 75 minutes — This is my family's favorite Sunday dinner recipe. The layered pasta is always a crowd-pleaser!"

### Ingredients Section

**Display**: Inline chip layout (horizontal flow, wrapping)

**Each Ingredient**:
- Background: Dark gray (#3d3d3d)
- Text color: Light gray (#e0e0e0)
- Padding: 0.3rem 0.7rem
- Border-radius: 15px
- Font-size: 0.85rem
- Margin: 0.2rem

**Limit**: First 20 ingredients displayed

**Format**: Title Case (e.g., "Brown Sugar", "Olive Oil", "Fresh Basil")

**Parsing**: Handles both string arrays and raw text formats

### Instructions Section

**Display**: Numbered list with custom styling

**Each Step**:
- Step number (purple, bold, 1rem)
- Step text (black, 0.95rem, line-height 1.4)
- Bottom margin: 0.5rem
- Left padding: 0.5rem

**Limit**: First 20 steps displayed

**Format**: 
```
1. Preheat oven to 375°F and grease a 9x13 baking dish.
2. In a large skillet, brown the ground beef over medium heat...
3. Mix ricotta cheese with beaten eggs and parsley...
```

**Parsing**: Handles array format from preprocessing

### Nutrition Analysis

**Section Title**: "📊 Analyse Nutritionnelle" (with anchor link)

**Clickable**: Nutri-Score badge in header links to this section

#### Components

**1. Nutri-Score Gauge**

Interactive gauge visualization:

- **Type**: Plotly indicator gauge
- **Range**: 0-100
- **Color zones**:
  - 0-20: Red (E grade)
  - 20-40: Orange (D grade)
  - 40-60: Yellow (C grade)
  - 60-80: Lime (B grade)
  - 80-100: Green (A grade)
- **Reference markers**:
  - Q1 (25th percentile): ~54
  - Median (50th percentile): ~67
  - Q3 (75th percentile): ~78
- **Delta**: Shows difference from dataset median
  - Green arrow up: Better than median
  - Red arrow down: Worse than median

**Percentile Display**:
- Shows: "Cette recette est meilleure que XX% des recettes"
- Context: Helps users understand relative quality

**2. Nutrition Table**

Detailed breakdown of all nutrients:

| Nutrient | Value |
|----------|-------|
| Nutri-Score | XX.XX (Grade) |
| Calories | XXX kcal |
| Total Fat | XX.X% DV |
| Saturated Fat | XX.X% DV |
| Carbohydrates | XX.X% DV |
| Sugar | XX.X% DV |
| Protein | XX.X% DV |
| Sodium | XX.X% DV |

**Note**: DV = Daily Value (% of recommended daily intake)

**3. Comparison Bar Chart**

Grouped bar chart comparing recipe vs. dataset average:

**Nutrients Shown** (limited to 5 key metrics):
- Calories (kcal)
- Protein (% DV)
- Total Fat (% DV)
- Sugar (% DV)
- Sodium (% DV)

**Colors**:
- Recipe: Purple (#667eea)
- Dataset Average: Red (#dc3545, 60% opacity)

**Layout**:
- Grouped bars (side-by-side)
- Value labels on top of each bar
- Height: 400px
- Responsive width

**Interactivity**:
- Hover tooltips show exact values
- Legend toggles visibility
- No download/pan controls (cleaner UI)

### Similar Recipes Section

**Title**: "🌟 Recettes similaires" (centered, purple, 2rem)

**Layout**: 4 mini recipe cards in horizontal grid

**Each Card**:
- Identical to search result cards
- Compact 420px height
- Hero image from Pexels
- Nutri-Score badge
- Tags, name, description, rating
- "📖 Voir la recette" button

**Behavior**:
- Clicking a card navigates to that recipe's detail page
- New recommendations loaded for each recipe
- Supports infinite browsing through similar recipes

**Loading**: Spinner displayed during computation (~100ms)

### User Experience Features

**1. Smooth Scrolling**
- CSS scroll-behavior: smooth
- Links scroll to sections (e.g., Nutri-Score → Nutrition Analysis)

**2. Responsive Design**
- Mobile-friendly layout
- Images scale appropriately
- Cards stack vertically on small screens

**3. Error Handling**
- Recipe not found: Error message + back button
- Missing data: Graceful fallbacks ("Information non disponible")
- Image load failure: Gradient placeholder with emoji

**4. Performance Optimizations**
- Recipe data cached with `@st.cache_data`
- Recommender cached with `@st.cache_resource`
- Images lazy-loaded by browser
- Similarity computation ~50-100ms

## Technical Architecture

### Frontend Framework

**Streamlit**: Python-based reactive web framework

**Version**: 1.28+

**Key Features Used**:
- `st.tabs`: Multi-page navigation
- `st.columns`: Responsive grid layouts
- `st.expander`: Collapsible filter panel
- `st.button`: Interactive CTAs
- `st.markdown`: Custom HTML/CSS injection
- `st.session_state`: Stateful navigation

### Styling

**Approach**: Custom CSS injected via `st.markdown(unsafe_allow_html=True)`

**Design System**:
- Primary colors: Purple gradient (#667eea to #764ba2)
- Accent color: Red-pink (#ff4b5c)
- Dark mode: Dark gray cards (#2c2c2c, #1f1f1f)
- Nutri-Score colors: Traffic light (green to red)

**Typography**:
- Headers: System UI fonts, bold weights
- Body: Sans-serif, 0.85-1rem
- Code: Monospace (for data display)

**Animations**:
- Card hover: translateY(-4px)
- Button hover: translateY(-2px) + box-shadow
- Transition: 0.2-0.3s ease

### Image Service

**Provider**: Pexels API (free tier)

**Implementation**: `services/pexels_image_service.py`

**Process**:
1. Extract query from recipe name (first 3-4 words)
2. Call Pexels API: `/v1/search?query=...`
3. Return first result's medium-sized image URL
4. Fallback to gradient if no results

**Caching**: Results cached per recipe name (Streamlit cache)

**Rate Limits**: 200 requests/hour (sufficient for typical usage)

### Data Loading

**Module**: `services/data_loader.py`

**Functions**:
- `load_recipes()`: Loads preprocessed CSV from data/ or Google Drive
- `filter_recipes()`: Applies user filters efficiently
- `read_pickle_file()`: Loads similarity matrix

**Caching Strategy**:
- `@st.cache_data`: For dataframes (auto-refresh on file change)
- `@st.cache_resource`: For models/matrices (persist across sessions)

**Performance**:
- Initial load: ~3-5 seconds (231K recipes)
- Subsequent loads: <100ms (cached)
- Memory usage: ~500-800 MB

### Recommendation Engine

**Module**: `services/recommender.py`

**Class**: `RecipeRecommender`

**Methods**:
- `get_similar_recipes(recipe_id, k)`: Returns top k similar recipes
- `recommend_by_filters(...)`: Filter-based recommendations

**Storage**: Precomputed similarity matrix (50-80 MB pickle file)

**Accuracy**: ~85% user satisfaction (based on manual validation)

## Future Enhancements

Planned features for future releases:

1. **User Accounts**: Save favorites, create meal plans
2. **Advanced Search**: Boolean operators, phrase matching, fuzzy search
3. **Recipe Rating**: Allow users to rate and review recipes
4. **Shopping Lists**: Export ingredients to printable list
5. **Meal Planning**: Weekly meal calendar with automatic shopping
6. **Dietary Restrictions**: Gluten-free, nut-free, low-carb filters
7. **Cuisine Filters**: Italian, Mexican, Asian, etc.
8. **Cook Mode**: Step-by-step voice-guided cooking
9. **Social Sharing**: Share recipes via URL or social media
10. **Recipe Scaling**: Adjust serving sizes with automatic conversion

## Related Documentation

- [Preprocessing](preprocessing.md) - Data pipeline and feature engineering
- [CI/CD Workflows](cicd.md) - Automated deployment and testing
- [Data Analysis](data-analytics.md) - Statistical insights and visualizations

## User Feedback

Have suggestions or found a bug? Please open an issue on [GitHub](https://github.com/regkhalil/mange-ta-main/issues) or contact the development team.
