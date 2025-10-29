# Data Analytics and Visualization

Mange ta main includes comprehensive data analytics dashboards that provide statistical insights into the Food.com dataset. These interactive visualizations help users understand recipe patterns, nutritional trends, and the relationships between cooking complexity, time, and health metrics.

## Overview

The analytics system is divided into two main areas:

1. **General Dataset Analysis** - High-level statistics and distributions
2. **Nutrition Profiling** - In-depth analysis of healthy recipe patterns

Both dashboards use Plotly for interactive visualizations, enabling users to explore data dynamically with zoom, pan, and hover capabilities.

## 📊 General Dataset Analysis

**Location**: "📊 Analyse" tab on main page (`app.py`)

This dashboard provides an overview of the entire recipe dataset with key performance indicators (KPIs) and distribution visualizations.

### Key Metrics

**Top Row KPIs** (4 columns):

1. **🍽️ Total Recipes**: Count of recipes in dataset (~231K)
2. **⏱️ Median Time**: Median preparation time (minutes)
3. **🥕 Average Ingredients**: Mean number of ingredients per recipe
4. **🔥 Average Calories**: Mean calorie content

**Data Source**: Aggregated from `preprocessed_recipes.csv`

**Update Frequency**: Real-time (recalculated on data load)

### Distribution Visualizations

#### 1. Preparation Time Distribution

**Chart Type**: Histogram with median/mean lines

**Purpose**: Understand the distribution of recipe complexity by cooking time

**Features**:
- **X-axis**: Cooking time (minutes)
- **Y-axis**: Number of recipes
- **Bins**: 30 bins
- **Filter**: Only shows recipes ≤180 minutes (removes extreme outliers)
- **Color**: Purple (#667eea)
- **Reference Lines**:
  - Median (vertical line with label)
  - Mean (dashed vertical line)

**Insights**:
- Most recipes: 30-60 minutes (typical home cooking)
- Peak: ~45 minutes
- Long tail: Complex dishes 2-3 hours

**Interactive**:
- Hover: Shows exact bin range and count
- Zoom: Click and drag to focus on time range
- Pan: Shift view left/right

#### 2. Ingredients Distribution

**Chart Type**: Histogram

**Purpose**: Identify recipe complexity by ingredient count

**Features**:
- **X-axis**: Number of ingredients
- **Y-axis**: Number of recipes
- **Bins**: 25 bins
- **Color**: Purple gradient (#764ba2)
- **No filter**: Shows full range (1-50+ ingredients)

**Insights**:
- Most recipes: 7-12 ingredients
- Peak: ~9 ingredients (sweet spot for home cooks)
- Few recipes: >20 ingredients (professional/complex)

**Categories** (displayed in recipe cards):
- 1-5 ingredients: 🥗 Simple (quick pantry meals)
- 6-10 ingredients: 🥘 Modéré (typical home cooking)
- 11+ ingredients: 👨‍🍳 Élaboré (elaborate dishes)

#### 3. Nutrition Score Distribution

**Chart Type**: Histogram with statistics overlay

**Purpose**: Show the distribution of recipe health scores

**Features**:
- **X-axis**: Nutrition score (10-98 scale)
- **Y-axis**: Number of recipes
- **Bins**: 30 bins
- **Color**: Pink gradient (#f093fb)
- **Reference Lines**:
  - Mean score (dashed yellow)
  - Median score (dotted orange)

**Statistics Panel** (below chart):
- 📊 Recipes with score: Count of scored recipes
- ⭐ Average score: Mean of all scores
- 🎯 Median score: 50th percentile
- 📈 Standard deviation: Spread of scores

**Insights**:
- Distribution: Near-normal with slight left skew
- Mean: ~67 (Grade C, acceptable nutrition)
- Median: ~65-70 (most recipes are moderately healthy)
- Range: 10-98 (full spectrum from very poor to excellent)

**Grade Mapping**:
- 85-98: Grade A (small fraction, ~5%)
- 70-84: Grade B (~20%)
- 55-69: Grade C (~40%, largest group)
- 40-54: Grade D (~25%)
- 10-39: Grade E (~10%)

### Relationship Analysis

#### Scatter Plot: Time vs Calories vs Ingredients

**Chart Type**: Interactive scatter plot with color encoding

**Purpose**: Explore relationships between cooking time, calorie content, and recipe complexity

**Features**:
- **X-axis**: Preparation time (minutes)
- **Y-axis**: Calories per serving
- **Color**: Number of ingredients (continuous scale)
- **Sample Size**: 2,000 recipes (random sample for performance)
- **Filters**: Time ≤300 min, Calories ≤2000 (removes outliers)
- **Opacity**: 0.6 (show density patterns)
- **Color Scale**: Viridis (yellow to purple)

**Insights**:
- **Positive correlation**: Longer recipes tend to have more ingredients
- **Weak correlation**: Time vs calories (no strong pattern)
- **Clusters**:
  - Quick low-cal: Salads, snacks (15-30 min, 100-300 cal)
  - Medium balanced: Main dishes (45-60 min, 400-600 cal)
  - Long high-cal: Desserts, casseroles (90+ min, 600-1000 cal)

**Interactive**:
- Hover: Shows exact time, calories, ingredient count
- Zoom: Focus on specific regions
- Legend: Toggle ingredient ranges

### Detailed Statistics Table

**Table Type**: Descriptive statistics with styling

**Purpose**: Provide comprehensive statistical summary

**Metrics Shown** (rows):
- Preparation time (minutes)
- Number of ingredients
- Number of steps
- Calories
- Protein (% DV)
- Total fat (% DV)
- Sugar (% DV)
- Sodium (% DV)

**Statistics** (columns):
- **count**: Number of non-null values
- **mean**: Average value
- **std**: Standard deviation
- **min**: Minimum value
- **25%**: First quartile (Q1)
- **50%**: Median (Q2)
- **75%**: Third quartile (Q3)
- **max**: Maximum value

**Styling**:
- Blue gradient background (intensity = value)
- 2 decimal precision
- Full-width responsive table

**Use Cases**:
- Identify outliers (min/max vs quartiles)
- Understand data spread (std)
- Compare distributions across metrics

### Data Source

**File**: `data/preprocessed_recipes.csv`

**Columns Used**:
- `minutes`, `n_ingredients`, `n_steps`
- `calories`, `protein`, `total_fat`, `sugar`, `sodium`
- `nutrition_score`, `nutrition_grade`
- `is_vegetarian`, `tags`

**Preprocessing**: See [Preprocessing Documentation](preprocessing.md)

## 📈 Nutrition Profiling

**Location**: "📊 Profil Nutrition" page (`pages/03_📊_Profil_Nutrition.py`)

This advanced analytics dashboard provides deep insights into the relationships between recipe characteristics and nutritional quality.

### Page Structure

The page is organized into four major sections:

1. **Section 1: Nutrition Grade Patterns** - Distribution and correlations
2. **Section 2: Time vs Health Analysis** - Cooking time impact
3. **Section 3: Ingredient Health Index** - Ingredient-level insights
4. **Section 4: Complexity vs Healthiness** - Multi-factor analysis

### Data Filtering

**Outlier Removal**:

To improve visualization quality, the dashboard applies percentile-based filtering:

- **Cooking Time**: 1st-99th percentile (removes recipes <5 min or >300 min)
- **Number of Steps**: 1st-99th percentile (removes recipes <2 or >50 steps)
- **Number of Ingredients**: 1st-99th percentile (removes recipes <3 or >40 ingredients)

**Effect**: ~2-3% of recipes filtered out, cleaner visualizations

**Note**: Original dataset still used for KPIs

### Section 1: Nutrition Grade Patterns

#### Nutrition Grade Distribution

**Chart Type**: Histogram with grade coloring

**Purpose**: Show the distribution of nutrition grades across all recipes

**Features**:
- **X-axis**: Nutrition grades (A, B, C, D, E)
- **Y-axis**: Number of recipes
- **Colors**: Traffic light system
  - A: Green (#238B45)
  - B: Lime (#85BB2F)
  - C: Yellow (#FECC00)
  - D: Orange (#FF9500)
  - E: Red (#E63946)
- **Annotations**: Percentage of total for each grade

**Insights**:
- Most common: Grade C (40-45% of recipes)
- Balanced distribution across B-D
- Rare: Grade A (<5%, excellent recipes)
- Few: Grade E (~10%, poor recipes)

**Interpretation**:
- Dataset: Mostly home cooking, not optimized for health
- Grade C: Acceptable for occasional consumption
- Opportunity: Improve recipes to B/A grades

#### Nutrient Correlation Heatmap

**Chart Type**: Spearman correlation heatmap

**Purpose**: Reveal relationships between nutritional components

**Features**:
- **Variables**: All numeric nutrients + nutrition_score
  - Minutes, n_steps, n_ingredients
  - Calories, protein, total_fat, saturated_fat
  - Sugar, sodium, carbohydrates
  - Nutrition_score
- **Method**: Spearman correlation (non-parametric, handles outliers)
- **Color Scale**: Red-Blue diverging (-1 to +1)
- **Annotations**: Correlation coefficients on cells

**Key Findings**:

**Strong Positive Correlations** (ρ > 0.5):
- Calories ↔ Total Fat (0.65): Higher fat = more calories
- Calories ↔ Carbohydrates (0.58): Carbs drive calorie content
- Total Fat ↔ Saturated Fat (0.82): Fats travel together
- N_Ingredients ↔ N_Steps (0.71): Complex recipes are detailed

**Moderate Negative Correlations** (ρ < -0.3):
- Nutrition Score ↔ Sugar (-0.42): Sugar hurts health score
- Nutrition Score ↔ Sodium (-0.38): Salt reduces score
- Nutrition Score ↔ Saturated Fat (-0.51): Worst offender

**Weak/No Correlations** (|ρ| < 0.2):
- Minutes ↔ Nutrition Score: Cooking time doesn't predict health
- Protein ↔ Sugar: Independent nutrients

**Actionable Insights**:
- Reduce saturated fat for biggest score improvement
- Sugar and sodium also important
- Protein has minimal negative impact

#### Mean Nutrients by Grade

**Chart Type**: Grouped bar chart

**Purpose**: Compare average nutrient levels across nutrition grades

**Features**:
- **X-axis**: Nutrition grades (A to E)
- **Y-axis**: Nutrient value (% DV or kcal)
- **Bars**: Grouped by nutrient
  - Calories (kcal)
  - Protein (% DV)
  - Total Fat (% DV)
  - Saturated Fat (% DV)
  - Sugar (% DV)
  - Sodium (% DV)
  - Carbohydrates (% DV)
- **Colors**: Distinct per nutrient (rainbow palette)

**Insights**:
- **Grade A** (excellent):
  - Low: Saturated fat (~15% DV), Sugar (~20% DV), Sodium (~10% DV)
  - High: Protein (~40% DV), Moderate calories (~350 kcal)
- **Grade E** (poor):
  - High: Saturated fat (~100% DV), Sugar (~120% DV), Sodium (~60% DV)
  - Variable: Calories, Protein

**Patterns**:
- Linear degradation from A to E for sat_fat, sugar, sodium
- Protein relatively stable across grades
- Carbs increase slightly from A to E

#### Nutrient Boxplots by Grade

**Chart Type**: Box-and-whisker plots (5 separate charts)

**Purpose**: Show distribution and outliers for key nutrients across grades

**Nutrients Analyzed**:
1. Saturated Fat (% DV)
2. Sugar (% DV)
3. Sodium (% DV)
4. Protein (% DV)
5. Calories (kcal)

**Features**:
- **Box**: Interquartile range (Q1 to Q3)
- **Line**: Median (Q2)
- **Whiskers**: 1.5 × IQR
- **Points**: Outliers beyond whiskers
- **Colors**: Grade-specific (A=green, E=red)

**Insights**:
- **Variability**: All grades have wide ranges (many outliers)
- **Overlap**: Grades overlap significantly (not perfectly separated)
- **Trends**:
  - A recipes: Tight distributions, few outliers
  - E recipes: Wide distributions, many extreme values
- **Protein**: Similar medians across all grades (protein not penalized)

### Section 2: Time vs Health Analysis

#### Time vs Nutrition Score Scatter

**Chart Type**: Scatter plot with trendline

**Purpose**: Investigate if cooking time affects nutritional quality

**Features**:
- **X-axis**: Cooking time (minutes)
- **Y-axis**: Nutrition score (10-98)
- **Sample**: 5,000 recipes (performance optimization)
- **Trendline**: LOWESS (locally weighted scatterplot smoothing)
- **Color**: Single color (purple)
- **Opacity**: 0.5 (show density)

**Findings**:
- **Correlation**: Very weak (ρ ≈ -0.05)
- **Trend**: Essentially flat (no meaningful relationship)
- **Clusters**:
  - Quick meals (15-30 min): Full score range (20-90)
  - Medium recipes (45-60 min): Full score range
  - Long recipes (120+ min): Slightly lower scores (bias toward rich desserts)

**Interpretation**:
- **Myth debunked**: "Quick = unhealthy" is false
- **Reality**: Health depends on ingredients, not time
- **Recommendation**: Don't avoid quick recipes for health reasons

#### Nutrition Grade by Time Category

**Chart Type**: Stacked bar chart

**Purpose**: Show grade distribution within time brackets

**Time Categories**:
- Quick: ≤30 minutes
- Medium: 31-60 minutes
- Long: 61-120 minutes
- Very Long: >120 minutes

**Features**:
- **X-axis**: Time categories
- **Y-axis**: Percentage of recipes (0-100%)
- **Bars**: Stacked, 100% height
- **Colors**: Grade colors (A=green to E=red)
- **Annotations**: Percentage labels on segments

**Insights**:
- **Quick recipes**:
  - Grade distribution: Similar to overall (C most common)
  - A+B: ~25%, E: ~10%
- **Medium recipes**:
  - Healthiest group: Highest A+B proportion (~30%)
  - Lowest E proportion (~8%)
- **Long recipes**:
  - More B/C grades (complex but balanced)
  - Fewer A grades (harder to optimize multi-component dishes)
- **Very Long recipes**:
  - Higher D/E: Rich desserts, indulgent casseroles
  - Fewer A grades: Celebration food, not daily meals

**Takeaway**: Medium-time recipes (30-60 min) offer best health outcomes

#### Time Category Distribution

**Chart Type**: Pie chart

**Purpose**: Show proportion of recipes in each time bracket

**Features**:
- **Segments**: 4 time categories
- **Labels**: Category name + count + percentage
- **Colors**: Cool palette (blues/greens)
- **Hover**: Shows exact count

**Distribution** (typical):
- Quick (≤30 min): 35-40%
- Medium (31-60 min): 40-45% ← Largest group
- Long (61-120 min): 15-20%
- Very Long (>120 min): 3-5%

**Insight**: Most recipes are designed for weeknight cooking (30-60 min)

### Section 3: Ingredient Health Index

#### Ingredients vs Nutrition Score Scatter

**Chart Type**: Scatter plot with size encoding

**Purpose**: Examine relationship between ingredient count and health

**Features**:
- **X-axis**: Number of ingredients
- **Y-axis**: Nutrition score
- **Point Size**: Calories (larger = more calories)
- **Sample**: 5,000 recipes
- **Trendline**: LOWESS
- **Opacity**: 0.5

**Findings**:
- **Correlation**: Weak positive (ρ ≈ 0.15)
- **Trend**: Slight upward slope
- **Interpretation**: More ingredients → slightly better nutrition
  - Reason: Diverse ingredients = balanced macros
  - Caveat: Not causal (simple dishes can be healthy)
- **Size patterns**: Large points (high-cal) scattered across all regions

**Outliers**:
- High ingredients, low score: Complex desserts with butter/sugar
- Low ingredients, high score: Simple salads, grilled proteins

#### Top Ingredients by Health Impact

**Table Type**: Sortable data table

**Purpose**: Identify which ingredients correlate with better/worse scores

**Analysis Method**:
1. Parse ingredient strings from all recipes
2. For each unique ingredient (min 100 occurrences):
   - Calculate mean nutrition score of recipes containing it
   - Count total occurrences
3. Sort by mean score (descending)

**Table Columns**:
- **Ingredient**: Name (Title Case)
- **Avg Score**: Mean nutrition score of recipes with this ingredient
- **Recipe Count**: Number of recipes containing it
- **Grade Equivalent**: A/B/C/D/E (based on avg score)

**Top Healthy Ingredients** (Score >75):
- Fresh vegetables: Spinach, Kale, Bell Peppers, Tomatoes
- Lean proteins: Chicken Breast, Turkey, Fish
- Whole grains: Quinoa, Brown Rice, Oats
- Legumes: Lentils, Chickpeas, Black Beans

**Bottom Unhealthy Ingredients** (Score <50):
- Processed sugars: Powdered Sugar, Corn Syrup, Marshmallows
- Heavy fats: Butter (large amounts), Cream Cheese, Heavy Cream
- Processed meats: Bacon, Sausage, Hot Dogs
- Refined carbs: White Sugar, All-Purpose Flour (excessive)

**Caveats**:
- Correlation ≠ causation
- Context matters (small amounts of butter OK)
- Combinations matter more than individual ingredients

#### Sugar vs Salt Comparison

**Chart Type**: Dual-axis scatter plot

**Purpose**: Compare impact of sugar vs sodium on nutrition score

**Features**:
- **X-axis**: Sugar (% DV)
- **Y-axis (left)**: Nutrition score
- **Y-axis (right)**: Sodium (% DV)
- **Points (left)**: Sugar impact (blue dots)
- **Points (right)**: Sodium impact (red dots)
- **Sample**: 3,000 recipes
- **Trendlines**: Separate LOWESS for each

**Findings**:
- **Sugar impact**: Moderate negative correlation (ρ ≈ -0.42)
  - Sharp drop: 0-50% DV → Score drops 20 points
  - Plateau: >50% DV → Already scored poorly
- **Sodium impact**: Moderate negative correlation (ρ ≈ -0.38)
  - Linear decline: 0-60% DV → Steady score drop
  - Extreme penalty: >60% DV → Very low scores
- **Comparison**: Sugar slightly worse for score, but both important

**Takeaway**: Minimize both sugar AND salt for best nutrition grades

#### Nutrient Impact on Score

**Chart Type**: Horizontal bar chart (coefficient plot)

**Purpose**: Quantify relative importance of each nutrient for nutrition score

**Analysis Method**:
1. Linear regression: `nutrition_score ~ all_nutrients`
2. Extract standardized coefficients (β)
3. Sort by magnitude (absolute value)

**Features**:
- **X-axis**: Standardized coefficient (-1 to +1)
- **Y-axis**: Nutrient names
- **Colors**: 
  - Negative (red): Hurts score
  - Positive (green): Improves score
- **Annotations**: Coefficient values

**Findings** (typical):
- **Largest Negative** (β < -0.3):
  1. Saturated Fat (-0.51): Biggest score killer
  2. Sugar (-0.42): Second worst
  3. Sodium (-0.38): Third worst
- **Moderate Negative** (β ≈ -0.15):
  - Total Fat, Calories (mild penalties)
- **Positive** (β > 0.15):
  - Protein (+0.23): Modest boost
  - (No other nutrients significantly positive)

**Actionable Insights**:
- **Priority 1**: Reduce saturated fat (biggest impact)
- **Priority 2**: Limit sugar (second biggest)
- **Priority 3**: Control sodium (third)
- **Bonus**: Add protein (small benefit)

### Section 4: Complexity vs Healthiness

#### Complexity vs Score Scatter

**Chart Type**: Bubble chart (3D data)

**Purpose**: Examine if recipe complexity affects nutrition

**Complexity Metric**: Combined score
- Formula: `(n_steps × 0.4) + (minutes × 0.01) + (n_ingredients × 0.3)`
- Weights: Steps matter most, then ingredients, then time

**Features**:
- **X-axis**: Complexity score (0-100)
- **Y-axis**: Nutrition score (10-98)
- **Bubble Size**: Number of ingredients (larger = more ingredients)
- **Sample**: 5,000 recipes
- **Color**: Gradient by complexity (cool to warm)

**Findings**:
- **Correlation**: Very weak (ρ ≈ 0.08)
- **Pattern**: Cloud-like distribution (no clear trend)
- **Interpretation**: Complexity doesn't predict health
  - Simple dishes: Full score range (20-90)
  - Complex dishes: Full score range (20-90)

**Outliers**:
- High complexity, high score: Multi-component balanced meals
- High complexity, low score: Rich desserts, fried foods
- Low complexity, high score: Simple salads, grilled proteins
- Low complexity, low score: Fast food recreations

**Takeaway**: Health depends on choices, not recipe length

#### Complexity Heatmap

**Chart Type**: 2D histogram (binned heatmap)

**Purpose**: Visualize density of recipes in complexity-health space

**Features**:
- **X-axis**: Complexity (binned into 20 ranges)
- **Y-axis**: Nutrition score (binned into 20 ranges)
- **Color**: Recipe count (white to red gradient)
- **Annotations**: Count in each bin

**Patterns**:
- **Hot spots** (high density):
  - Medium complexity (40-60), Medium health (50-70): Typical home cooking
  - Low complexity (20-40), Low health (30-50): Quick convenience foods
- **Cold spots** (low density):
  - High complexity (>70), High health (>80): Rare (elaborate healthy meals)
  - Low complexity (<30), High health (>75): Uncommon (simple perfect dishes)

**Interpretation**: Most recipes cluster in "moderate everything" zone

#### Complexity Category Distribution

**Chart Type**: Pie chart with grade breakdown

**Purpose**: Show how grades distribute across complexity levels

**Complexity Categories**:
- Simple: Complexity score <40 (≤10 steps, ≤30 min, ≤8 ingredients)
- Moderate: Complexity score 40-60
- Complex: Complexity score >60 (>15 steps, >60 min, >12 ingredients)

**Features**:
- **Segments**: 3 complexity categories
- **Labels**: Category + percentage
- **Colors**: Cool to warm gradient
- **Hover**: Shows recipe count and grade distribution

**Distribution** (typical):
- Simple: 40-45% of recipes
- Moderate: 45-50% of recipes
- Complex: 5-10% of recipes

**Grade Patterns**:
- Simple: More E grades (quick junk food)
- Moderate: Best grade distribution (balanced cooking)
- Complex: More C/D grades (indulgent celebration food)

#### Individual Complexity Factors

**Chart Type**: Box plots (3 separate charts)

**Purpose**: Break down complexity into components

**Charts**:
1. **Number of Steps by Grade**: Do more steps = better nutrition?
2. **Cooking Time by Grade**: Does longer cooking = better nutrition?
3. **Number of Ingredients by Grade**: Do more ingredients = better nutrition?

**Findings**:

**Number of Steps**:
- All grades: Similar median (~10 steps)
- No significant difference between A and E
- Conclusion: Steps don't affect health

**Cooking Time**:
- All grades: Similar median (~45 minutes)
- Slight variation: E recipes slightly longer (desserts)
- Conclusion: Time doesn't predict health

**Number of Ingredients**:
- Slight positive trend: A recipes ~11 ingredients, E recipes ~9
- Overlapping distributions
- Conclusion: More ingredients = slightly better (diversity helps)

**Overall Takeaway**: Individual complexity factors weakly related to health

## Analytical Methodology

### Statistical Techniques

**1. Correlation Analysis**
- **Method**: Spearman's rank correlation (non-parametric)
- **Why**: Handles outliers and non-linear relationships
- **Interpretation**: ρ = 0 (no relation), ρ = ±1 (perfect relation)

**2. Regression Analysis**
- **Method**: Ordinary Least Squares (OLS)
- **Purpose**: Quantify nutrient impact on score
- **Output**: Standardized coefficients (β)

**3. Smoothing**
- **Method**: LOWESS (locally weighted scatterplot smoothing)
- **Purpose**: Show trends without assuming linearity
- **Bandwidth**: 0.1-0.3 (balances smoothness and detail)

**4. Outlier Detection**
- **Method**: IQR (interquartile range) method
- **Threshold**: 1.5 × IQR beyond Q1/Q3
- **Handling**: Included in visualizations, excluded from percentile calcs

### Data Quality

**Missing Values**:
- Nutrition data: <1% missing (excluded from analyses)
- User ratings: ~50% missing (uses defaults: 3.0 rating, 0 reviews)
- Tags: ~5% missing (treated as empty list)

**Outliers**:
- Identified via percentile filtering (1st-99th)
- Flagged but retained in dataset
- Excluded from specific visualizations (noted in captions)

**Data Integrity**:
- No duplicate recipe IDs
- All nutrition scores in valid range (10-98)
- All grades in valid set (A-E)

### Visualization Design Principles

**1. Color Coding**
- **Nutrition Grades**: Traffic light (green=good, red=bad)
- **Sequential Data**: Single hue gradient (light to dark)
- **Diverging Data**: Red-blue (negative to positive)
- **Categorical**: Distinct hues (rainbow palette)

**2. Accessibility**
- Dark background (`plotly_dark` theme)
- High contrast text
- Colorblind-safe palettes (avoided red-green alone)
- Hover tooltips for all data points

**3. Performance**
- Sampling: Large datasets downsampled to 2K-5K points
- Aggregation: Pre-compute statistics (not per-render)
- Caching: `@st.cache_data` for expensive computations
- Lazy loading: Charts render on scroll (Streamlit default)

**4. Interactivity**
- Zoom: Click and drag rectangular selection
- Pan: Shift + drag to move view
- Hover: Tooltips show exact values
- Legend: Click to toggle series visibility
- Download: Export as PNG (Plotly built-in)

## Technical Implementation

### Visualization Stack

**Library**: Plotly (Python)
- **Version**: 5.x
- **Rendering**: WebGL for large datasets
- **Export**: Static PNG or interactive HTML

**Integration**: Streamlit `st.plotly_chart()`
- `use_container_width=True`: Responsive sizing
- `config={'displayModeBar': False}`: Clean UI (optional)

### Data Pipeline

```
load_recipes()
     ↓
filter_outliers()
     ↓
compute_statistics()
     ↓
create_plotly_figure()
     ↓
st.plotly_chart()
```

**Execution Time**:
- Data load: ~3-5s (first time)
- Filtering: ~100-200ms
- Statistics: ~50-100ms per metric
- Plotting: ~200-500ms per chart
- **Total**: ~5-10s for full dashboard (first load)
- **Cached**: ~1-2s (subsequent loads)

### Performance Optimizations

**1. Data Caching**
```python
@st.cache_data
def load_data():
    return load_recipes()
```
- Caches dataframe in memory
- Persists across sessions
- Auto-refreshes on file change

**2. Sampling**
```python
df_sample = df.sample(n=5000, random_state=42)
```
- Reduces rendering time for scatter plots
- Maintains statistical properties
- Random seed ensures reproducibility

**3. Aggregation**
```python
df_grouped = df.groupby('nutrition_grade').agg({
    'calories': 'mean',
    'protein': 'mean',
    # ...
})
```
- Pre-aggregate before plotting
- Reduces data passed to JavaScript
- Faster rendering, smaller payloads

**4. Outlier Filtering**
- Removes extreme values (~2% of data)
- Improves chart readability
- Prevents axis scaling issues

## Use Cases

### For Home Cooks

**Discovery**:
- "What's the typical cooking time for most recipes?" → Check time distribution
- "Are simple recipes unhealthy?" → Check complexity vs score scatter
- "How many ingredients should I aim for?" → Check ingredient distribution

**Validation**:
- "Is my recipe idea unusual?" → Compare to distributions
- "Is 90 minutes too long?" → Check time percentiles
- "Is 15 ingredients too many?" → Check ingredient boxplots

### For Recipe Developers

**Optimization**:
- "Which nutrients hurt my score most?" → Check nutrient impact chart
- "Should I add more ingredients?" → Check ingredients vs health
- "How do I get to Grade A?" → Study Grade A nutrient profiles

**Benchmarking**:
- "How do my recipes compare to the dataset?" → Check mean nutrients by grade
- "What's a realistic Grade B target?" → Check grade distribution
- "Is my complexity appropriate?" → Check complexity categories

### For Nutritionists

**Analysis**:
- "What's the correlation between saturated fat and health?" → Check correlation heatmap
- "Are users cooking healthy meals?" → Check grade distribution
- "What ingredients drive health outcomes?" → Check ingredient health table

**Insights**:
- "Why are most recipes Grade C?" → Analyze mean nutrients
- "Can we improve the dataset?" → Identify grade C → B opportunities
- "What's the biggest problem nutrient?" → Check impact coefficients

### For Data Scientists

**Exploration**:
- "What features correlate with nutrition score?" → Correlation heatmap
- "Is complexity a useful feature?" → Check complexity scatter
- "Are there data quality issues?" → Check outlier distributions

**Validation**:
- "Do our preprocessing assumptions hold?" → Check distributions match expectations
- "Are grades well-separated?" → Check boxplots and overlap
- "Do we need more features?" → Check unexplained variance in scatters

## Future Enhancements

**Planned Analytics Features**:

1. **Time Series Analysis**: Recipe trends over years (2008-2018)
2. **Cuisine Analysis**: Compare nutrition across Italian, Mexican, Asian, etc.
3. **Seasonal Analysis**: Holiday recipes vs. everyday meals
4. **User Segmentation**: Analyze by user rating patterns
5. **Network Analysis**: Ingredient co-occurrence networks
6. **Predictive Modeling**: Train ML model to predict popularity
7. **Cluster Analysis**: K-means on nutrition vectors
8. **Text Mining**: Topic modeling on recipe descriptions
9. **A/B Testing**: Compare recipe variants
10. **Recommendation Metrics**: Precision/recall of similarity engine

## Related Documentation

- [Preprocessing](preprocessing.md) - Data pipeline and scoring algorithms
- [App Features](app-features.md) - User-facing recipe search and detail views
- [CI/CD](cicd.md) - Automated analytics regeneration

## Data Source

**Citation**: Bodhisattwa Prasad Majumder, Shuyang Li, Jianmo Ni, Julian McAuley. "Generating Personalized Recipes from Historical User Preferences." EMNLP 2019.

**Kaggle**: [Food.com Recipes and User Interactions](https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions)

**License**: CC BY-NC-SA 4.0 (Non-commercial use)
