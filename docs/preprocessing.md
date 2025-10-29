# Preprocessing Pipeline

The preprocessing pipeline is the data engineering backbone of Mange ta main. It transforms raw recipe and interaction data from Food.com into a clean, enriched dataset optimized for the recommendation engine and analytics dashboards. The pipeline runs automatically via CI/CD or can be executed locally for development.

## Overview

The preprocessing pipeline takes approximately 10-15 minutes to process the full dataset of ~231,637 recipes and ~1.1M user interactions. The pipeline is orchestrated by the main `preprocess.py` script, which coordinates multiple specialized modules to perform data cleaning, feature extraction, and enrichment.

### Input Data

The pipeline processes several raw CSV files located in the `data/` directory:

- **`RAW_recipes.csv`**: Core recipe data (~231K recipes)
  - Recipe names, descriptions, ingredients, cooking steps
  - Preparation time, nutrition facts (7 components)
  - Tags, number of steps and ingredients
  
- **`RAW_interactions.csv`**: User behavior data (~1.1M interactions)
  - User ratings (1-5 scale)
  - Recipe reviews and feedback
  - Timestamps and user engagement metrics

### Output Data

The pipeline generates two essential files:

- **`preprocessed_recipes.csv`**: Enhanced recipe dataset with 17 columns
  - Cleaned and enriched text (names, descriptions, steps, tags, ingredients)
  - Nutrition scores and letter grades (A-E)
  - Vegetarian classification
  - Popularity metrics (ratings, review counts, popularity scores)
  - Extracted calories for quick access

- **`similarity_matrix.pkl`**: Precomputed similarity data structure
  - Sparse feature matrix for all recipes
  - ID-to-index bidirectional mappings
  - Fitted vectorizers for ingredients, tags, and names
  - Enables sub-second recipe recommendations

## Pipeline Architecture

The preprocessing pipeline follows a modular architecture with well-defined stages:

```
RAW Data
    │
    ├─> Load & Parse
    │       │
    │       └─> Vegetarian Classification
    │
    ├─> Feature Extraction
    │       │
    │       └─> Similarity Matrix Generation
    │
    ├─> Nutrition Analysis
    │       │
    │       └─> Weighted Balance Scoring (A-E grades)
    │
    ├─> Text Enhancement
    │       │
    │       ├─> Metadata Integration (cooking time, techniques, ingredients)
    │       └─> Text Cleaning (capitalization, contractions, proper nouns)
    │
    ├─> Popularity Computation
    │       │
    │       ├─> Load User Interactions
    │       ├─> Aggregate Ratings & Reviews
    │       └─> Compute Popularity Scores (70% rating, 30% volume)
    │
    └─> Final Assembly
            │
            ├─> Column Selection & Renaming
            └─> Export preprocessed_recipes.csv + similarity_matrix.pkl
```

## Pipeline Stages

### 1. Data Loading & Vegetarian Classification

**Module**: `preprocess_utils.py`, `prepare_vege_recipes.py`

The pipeline begins by loading the raw recipe data and immediately classifying recipes as vegetarian or non-vegetarian based on ingredient analysis.

**Vegetarian Classification Logic**:
- Scans ingredient lists for meat, poultry, seafood keywords
- Handles edge cases (e.g., "chicken of the sea" tuna, "sea salt" false positives)
- Uses compiled regex patterns for performance (~231K recipes in seconds)
- Adds `is_vegetarian` boolean column

**Key Features**:
- Type-safe data loading with pandas dtype specifications
- Handles missing values and malformed data gracefully
- Validates nutrition arrays (7-component format)
- Comprehensive logging of data quality metrics

### 2. Similarity Matrix Generation

**Module**: `prepare_similarity_matrix.py`

This stage creates the mathematical foundation for the recommendation engine by extracting features and computing a sparse similarity matrix.

#### Feature Extraction

The pipeline extracts and vectorizes three types of textual features:

1. **Recipe Names** (weight: 5.0x)
   - TF-IDF vectorization with CountVectorizer
   - High weight ensures recipes with similar names rank highly
   - Example: "chocolate chip cookies" → matches "cookies", "chocolate"

2. **Ingredients** (weight: 1.0x)
   - Ingredient lists parsed from string format
   - Each ingredient becomes a feature dimension
   - Enables "find recipes with similar ingredients" functionality

3. **Tags** (weight: 1.0x)
   - Recipe metadata tags (e.g., "dessert", "quick", "italian")
   - Captures recipe categories and characteristics
   - Supports filtering by cooking style and difficulty

4. **Ease Features** (weight: 5.0x)
   - Numeric features: `n_steps` (number of steps), `minutes` (cook time)
   - MinMax normalized to 0-1 range
   - Ensures recipes with similar complexity are recommended together

#### Similarity Computation

The extracted features are combined into a sparse matrix (CSR format) for efficient storage and computation:

- **Sparse Matrix**: Only non-zero values stored (~99% sparsity)
- **Cosine Similarity**: Measures recipe similarity (0 = unrelated, 1 = identical)
- **ID Mappings**: Bidirectional dictionaries for fast lookups
  - `id_to_index`: Recipe ID → Matrix row index
  - `index_to_id`: Matrix row index → Recipe ID

**Performance**:
- Matrix generation: ~30 seconds for 231K recipes
- Similarity query: <50ms per recipe (5-10 recommendations)
- Matrix size: ~50-80 MB (pickled)

### 3. Nutrition Scoring

**Module**: `nutrition_scoring.py`

The nutrition scoring system implements an evidence-based algorithm grounded in WHO, USDA, AHA (American Heart Association), and EFSA dietary guidelines.

#### Scoring Algorithm: Weighted Balance Score

The algorithm uses a three-component scoring model:

**Component 1: Weighted Base Score (0-100 points)**

Each of 7 nutrients is scored individually (0-10 points) based on healthy ranges:

| Nutrient | Weight | Rationale |
|----------|--------|-----------|
| Saturated Fat | 25% | Highest priority - direct CVD risk (WHO/AHA) |
| Protein | 20% | Essential macronutrient, muscle maintenance |
| Sodium | 15% | Direct hypertension/stroke risk (WHO) |
| Total Fat | 13% | Context-dependent (quality matters) |
| Sugar | 12% | Indirect metabolic harm, inflammation |
| Calories | 10% | Energy balance foundation |
| Carbohydrates | 5% | Quality matters more than quantity |

**Component 2: Balance Bonus (0-10 points)**
- +2 points per nutrient in optimal range (capped at +10)
- Rewards nutritionally well-rounded recipes
- Prevents single-nutrient optimization (e.g., extremely high protein)

**Component 3: Extreme Penalties (0-30 points)**
- Additional penalties for dangerously high levels
- Based on WHO/EFSA safety thresholds
- Examples:
  - Saturated fat >100% DV: Atherogenic risk
  - Sodium >50% DV (>1150mg): Hypertension risk
  - Protein >150% DV (>75g): Kidney stress risk

#### Healthy Ranges

All nutrients use **Percent Daily Value (%DV)** format except calories (kcal):

| Nutrient | Optimal Range | Daily Value |
|----------|---------------|-------------|
| Calories | 150-600 kcal | 2000 kcal |
| Protein | 30-70% DV | 50g |
| Total Fat | 6-32% DV | 78g |
| Saturated Fat | 0-35% DV | 20g |
| Sugar | 0-30% DV | 50g (added) |
| Sodium | 0-20% DV | 2300mg |
| Carbohydrates | 7-22% DV | 275g |

Ranges are calibrated for a single meal (assuming 3 meals/day + snacks).

#### Grade Assignment

Normalized scores (10-98) are mapped to letter grades:

- **A (85-98)**: Excellent nutrition - well-balanced, minimal concerns
- **B (70-84)**: Good nutrition - mostly healthy choices
- **C (55-69)**: Acceptable - some nutritional trade-offs
- **D (40-54)**: Poor - significant nutritional concerns
- **E (10-39)**: Very poor - multiple red flags

**Output Columns**:
- `nutrition_score`: Float (10-98 range)
- `nutrition_grade`: String (A-E letter grade)
- `calories`: Float (extracted from nutrition array for quick access)

### 4. Text Enhancement

**Modules**: `recipe_descriptions_hybrid.py`, `text_cleaner.py`

The text enhancement stage transforms raw recipe text into polished, readable content optimized for display and search.

#### Description Enhancement

**Process**: Enriches recipe descriptions by integrating metadata while preserving user stories.

**What It Adds**:
1. **Cooking Techniques**: Extracted from tags (e.g., "Slow Cooker", "Oven-Baked", "Grilled")
2. **Main Ingredients**: Filters generic items (salt, oil, water), keeps distinctive ingredients
3. **Cooking Time**: Natural language formatting
   - <60 min: "ready in 25 minutes"
   - 1-2 hours: "about 2 hours"
   - >24 hours: "2 days" (e.g., fermentation, marinating)
4. **Meal Type & Cuisine**: Derived from tags (e.g., "Italian side dish")
5. **Dietary Info**: Vegetarian, quick meals, holiday recipes

**Format**: `[Technique] [meal type] recipe with [ingredients], ready in [time] — [original user description]`

**Example Transformation**:

```
Before: "arriba baked winter squash mexican style"

After:  "Side dish vegetarian recipe with winter squash and Mexican 
         seasoning, ready in 55 minutes — Autumn is my favorite time 
         of year to cook! This recipe can be prepared either spicy 
         or sweet, your choice!"
```

#### Text Cleaning

**Process**: Standardizes capitalization, punctuation, and grammar across all text columns.

**Cleaning Rules**:
- **Names & Ingredients**: Title Case ("Mom's Apple Pie", "Brown Sugar")
- **Descriptions & Steps**: Sentence case with proper noun preservation
- **Tags**: lowercase ("dessert", "30-minutes-or-less")

**Features**:
- Restores 35+ contraction patterns (can't, won't, didn't)
- Capitalizes 100+ proper nouns (Italian, Christmas, France, Mom, etc.)
- Normalizes whitespace and punctuation
- Handles possessives correctly (Mom's, Dad's)
- Preserves existing well-formatted text

**Performance**: ~231K recipes processed in ~10 minutes

### 5. Popularity Computation

**Module**: `compute_popularity.py`

The popularity module analyzes user interaction data to identify trending and highly-rated recipes.

#### Data Processing

**Step 1: Load & Clean Interactions**
- Loads ~1.1M user ratings from `RAW_interactions.csv`
- Removes invalid ratings (outside 1-5 scale)
- Filters duplicate ratings (same user/recipe pair)
- Removes entries with missing user_id or recipe_id

**Step 2: Aggregate Metrics**

For each recipe, computes:

1. **Average Rating**: Mean of all user ratings (1-5 scale)
   - Rounded to 2 decimal places
   - Used to measure recipe quality

2. **Review Count**: Total number of user ratings
   - Integer count
   - Indicates recipe popularity and engagement

3. **Popularity Score**: Composite metric (0-1 scale)
   - Formula: `0.7 × normalized_rating + 0.3 × normalized_review_count`
   - Normalized rating: `(avg_rating - 1) / 4` → [0, 1]
   - Normalized review count: `log(1 + reviews) / log(1 + max_reviews)` → [0, 1]
   - **70% quality weight**: Emphasizes highly-rated recipes
   - **30% volume weight**: Considers engagement and popularity
   - Log transformation reduces skewness from viral recipes

#### Default Values

Recipes without user interactions receive default values:
- `review_count`: 0
- `average_rating`: 3.0 (neutral rating)
- `popularity_score`: 0.0 (no engagement data)

**Statistics** (typical dataset):
- ~40-50% of recipes have user reviews
- Average rating: 4.2-4.5 (users tend to rate favorites)
- Review count median: 3-5 reviews
- Review count max: 100-500+ for viral recipes

### 6. Final Assembly

**Process**: Selects, renames, and exports the final dataset.

**Column Selection**: The pipeline outputs 17 essential columns:

| Column | Type | Description |
|--------|------|-------------|
| `name` | str | Cleaned recipe name (Title Case) |
| `id` | int | Unique recipe identifier |
| `minutes` | int | Total cooking time |
| `tags` | str | Cleaned category tags (lowercase) |
| `n_steps` | int | Number of cooking steps |
| `steps` | str | Cleaned cooking instructions |
| `description` | str | Enhanced & cleaned description |
| `ingredients` | str | Cleaned ingredient list (Title Case) |
| `n_ingredients` | int | Number of ingredients |
| `nutrition` | str | Full nutrition array [7 values] |
| `nutrition_score` | float | Balanced nutrition score (10-98) |
| `nutrition_grade` | str | Letter grade (A-E) |
| `is_vegetarian` | bool | Vegetarian classification |
| `calories` | float | Extracted calories value (kcal) |
| `review_count` | int | Number of user reviews |
| `average_rating` | float | Mean user rating (1-5) |
| `popularity_score` | float | Composite popularity metric (0-1) |

**Data Types**: Optimized for memory efficiency
- Integers: `int64` for IDs, `int32` for counts
- Floats: `float32` for ratings/scores
- Strings: Default pandas object type
- Final CSV size: ~150-200 MB (uncompressed)

## Running the Pipeline

### Local Execution

**Basic preprocessing** (saves to `data/` directory only):

```bash
python preprocessing/preprocess.py
```

**With Google Drive deployment**:

```bash
python preprocessing/preprocess.py --deploy
```

**Custom data/logs directories**:

```bash
python preprocessing/preprocess.py --data-dir /path/to/data --logs-dir /path/to/logs
```

### Using Make

The project includes a Makefile for convenience:

```bash
# Install dependencies and run preprocessing
make dev

# Run preprocessing only
make preprocess
```

### CI/CD Execution

The pipeline runs automatically via GitHub Actions when:
- Changes are pushed to `preprocessing/` directory
- Workflow file is modified
- Manually triggered via Actions tab

See the [CI/CD documentation](cicd.md) for details on automatic execution.

## Configuration & Environment

### Required Dependencies

Core Python packages (installed via `uv` or `pip`):

```toml
# From pyproject.toml
pandas >= 2.0.0          # Data manipulation
numpy >= 1.24.0          # Numerical operations
scikit-learn >= 1.3.0    # ML features and vectorization
scipy >= 1.11.0          # Sparse matrices and cosine similarity
```

### Google Drive Integration

For the `--deploy` flag to work, the pipeline requires Google Drive credentials:

**Required Files** (in `credentials/` directory):
- `credentials.json`: Service account JSON from Google Cloud Console
- `token.json`: OAuth token for Google Drive API access
- `folder_id.txt`: Target Google Drive folder ID

**Setup**:
1. Create a Google Cloud project
2. Enable Google Drive API
3. Create service account and download credentials
4. Run authentication flow to generate token
5. Share target folder with service account email

**CI/CD**: Credentials stored as GitHub Secrets and injected at runtime

### Logging

The pipeline generates comprehensive logs in the `logs/` directory:

**Log Format**:
- Filename: `preprocessing_YYYYMMDD_HHMMSS.log`
- Level: INFO (with WARNING/ERROR for issues)
- Format: `[timestamp] [level] [module] message`

**What's Logged**:
- Pipeline progress and timing
- Data quality metrics (missing values, outliers)
- Processing statistics (rows processed, features extracted)
- Errors and warnings with stack traces
- Final output summaries (file sizes, row counts)

**Log Retention**: Logs are retained for 30 days in CI/CD (GitHub Actions artifacts)

## Performance & Optimization

### Processing Time

Typical execution on Ubuntu Linux (4 CPU cores, 8GB RAM):

| Stage | Time | Notes |
|-------|------|-------|
| Data Loading | ~5s | Pandas CSV parsing |
| Vegetarian Classification | ~3s | Regex matching on 231K recipes |
| Similarity Matrix | ~30s | Feature extraction + sparse matrix |
| Nutrition Scoring | ~15s | Complex scoring algorithm |
| Text Enhancement | ~8 min | LLM-style metadata integration |
| Text Cleaning | ~2 min | Regex-based text standardization |
| Popularity Computation | ~10s | Aggregation on 1.1M interactions |
| Final Export | ~5s | CSV writing |
| **Total** | **~10-12 min** | End-to-end pipeline |

### Memory Usage

- **Peak RAM**: ~2-3 GB (sparse matrices in memory)
- **Output Size**: 
  - `preprocessed_recipes.csv`: ~150-200 MB
  - `similarity_matrix.pkl`: ~50-80 MB
- **Optimization**: Sparse matrix format saves ~95% memory vs dense

### Scalability

The pipeline is optimized for datasets up to ~500K recipes:

- **Bottlenecks**: 
  - Text enhancement (compute-bound, O(n) operations)
  - Similarity matrix (memory-bound, O(n²) for dense)
  
- **Scaling Strategies**:
  - Use sparse matrices (already implemented)
  - Parallel processing for text operations (future work)
  - Incremental processing for very large datasets
  - Database backend for interaction data (future work)

## Troubleshooting

### Common Issues

**1. Missing Input Files**

```
FileNotFoundError: RAW_recipes.csv not found
```

**Solution**: Ensure raw data files are in `data/` directory. Download from Kaggle if needed.

**2. Memory Errors**

```
MemoryError: Unable to allocate array
```

**Solution**: 
- Close other applications
- Increase swap space
- Use a machine with more RAM (8GB+ recommended)

**3. Google Drive Upload Fails**

```
Error: Failed to authenticate with Google Drive
```

**Solution**:
- Verify credentials files exist in `credentials/`
- Re-run authentication flow to refresh token
- Check service account has write permissions to target folder

**4. Malformed Nutrition Data**

```
Warning: X recipes with invalid nutrition data
```

**Solution**: This is expected - some recipes have incomplete data. The pipeline assigns neutral scores to these recipes.

### Debugging Tips

**Enable verbose logging**:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Inspect intermediate outputs**:

```python
# After each stage, save intermediate CSV
df.to_csv('data/debug_stage_X.csv', index=False)
```

**Profile performance**:

```python
import time
start = time.time()
# ... stage code ...
print(f"Stage took {time.time() - start:.2f}s")
```

**Check data quality**:

```python
# Missing values
print(df.isnull().sum())

# Duplicates
print(df.duplicated(subset=['id']).sum())

# Value ranges
print(df[['nutrition_score', 'popularity_score']].describe())
```

## Data Quality & Validation

The pipeline includes several quality checks:

### Input Validation

- ✓ Recipe IDs are unique integers
- ✓ Nutrition arrays have exactly 7 components
- ✓ Ratings are in valid range (1-5)
- ✓ Required columns present in raw data

### Output Validation

- ✓ No duplicate recipe IDs
- ✓ Nutrition scores in expected range (10-98)
- ✓ All grades are A-E
- ✓ Popularity scores normalized (0-1)
- ✓ Text fields are non-empty strings

### Handling Edge Cases

**Missing Descriptions**: Empty strings preserved, no placeholder text added

**Zero Cook Time**: Valid for no-cook recipes (salads, beverages)

**Extreme Cook Times**: Handled gracefully (e.g., "2 days" for fermentation)

**Very Long Recipes**: No truncation - full content preserved

**Special Characters**: Unicode properly handled, not stripped

## Future Enhancements

Planned improvements to the preprocessing pipeline:

1. **Incremental Processing**: Only reprocess changed recipes
2. **Parallel Execution**: Multi-process text enhancement
3. **Advanced NLP**: Semantic embeddings for better similarity
4. **Image Processing**: Extract recipe images and validate URLs
5. **Nutrition Extraction**: Parse free-text ingredient lists to compute nutrition
6. **Quality Scoring**: Detect low-quality or spam recipes
7. **A/B Testing Support**: Generate multiple preprocessed variants
8. **Database Backend**: Replace CSV files with PostgreSQL/SQLite

## Related Documentation

- [CI/CD Workflows](cicd.md) - Automated preprocessing execution
- [Getting Started](getting-started.md) - Local setup and development
- [Services API](reference/services.md) - How the app consumes preprocessed data

## References

**Data Source**: 
- Kaggle Dataset: [Food.com Recipes and Interactions](https://www.kaggle.com/datasets/shuyangli94/food-com-recipes-and-user-interactions)
- Original dataset: ~231K recipes, 1.1M interactions (2008-2018)

**Nutritional Guidelines**:
- WHO: [Healthy Diet Fact Sheet](https://www.who.int/news-room/fact-sheets/detail/healthy-diet)
- USDA: [Dietary Guidelines for Americans 2020-2025](https://www.dietaryguidelines.gov/)
- AHA: [Saturated Fat Recommendations](https://www.heart.org/en/healthy-living/healthy-eating/eat-smart/fats/saturated-fats)
- EFSA: [Dietary Reference Values](https://www.efsa.europa.eu/en/topics/topic/dietary-reference-values)

**Machine Learning**:
- Scikit-learn: [Text Feature Extraction](https://scikit-learn.org/stable/modules/feature_extraction.html)
- SciPy: [Sparse Matrices](https://docs.scipy.org/doc/scipy/reference/sparse.html)
