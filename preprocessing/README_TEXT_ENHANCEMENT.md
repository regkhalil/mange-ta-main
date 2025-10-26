# Recipe Text Enhancement Pipeline

This directory contains the text enhancement and cleaning pipeline for recipe data.

## Core Modules

### 1. `text_cleaner.py`
Cleans and standardizes text across all recipe columns with appropriate capitalization rules:
- **Names & Ingredients**: Title Case ("Mom's Apple Pie", "Brown Sugar")
- **Descriptions & Steps**: Sentence case with proper noun capitalization
- **Tags**: lowercase ("dessert", "30-minutes-or-less")

Features:
- Restores 35+ contraction patterns (can't, won't, didn't)
- Capitalizes proper nouns (Italian, Christmas, Mom, France, etc.)
- Normalizes whitespace and punctuation
- Handles possessives correctly

### 2. `recipe_descriptions_hybrid.py`
Enhances recipe descriptions by integrating metadata while preserving user stories:
- Extracts cooking techniques (Slow Cooker, Oven-Baked, Grilled, etc.)
- Identifies main ingredients (filters generic items like salt, oil)
- Formats cooking time naturally ("about 2 hours", "quick and ready in 15 minutes")
- Adds meal type, cuisine, and dietary information
- Creates single-sentence format: "[Technique] [meal type] recipe with [ingredients], ready in [time] — [user description]"

Features:
- Smart time formatting (rounds to hours/30-min increments for 2+ hours, shows days for 24+ hours)
- Ingredient truncation with preposition removal
- Fallback handling for recipes with no metadata
- Natural language integration

## Usage

### Run the Complete Pipeline

```bash
python run_text_enhancement.py
```

This will:
1. Load `data/RAW_recipes.csv`
2. Enhance all recipe descriptions
3. Clean all text columns with proper capitalization
4. Save to `data/recipes_enhanced_final.csv`
5. Generate detailed logs in `logs/text_enhancement_TIMESTAMP.log`

### Use in Code

```python
from preprocessing.text_cleaner import clean_recipe_data
from preprocessing.recipe_descriptions_hybrid import enhance_recipe_descriptions

# Enhance descriptions
df_enhanced = enhance_recipe_descriptions(
    df,
    original_desc_col='description',
    time_col='minutes',
    tags_col='tags',
    ingredients_col='ingredients',
    output_col='description_enhanced'
)

# Clean all text
df_clean = clean_recipe_data(
    df_enhanced,
    clean_name=True,
    clean_description=True,
    clean_steps=True,
    clean_tags=True,
    clean_ingredients=True
)
```

## Example Output

**Original**: "arriba baked winter squash mexican style"
**Enhanced & Cleaned**: "Side dish vegetarian recipe with winter squash and Mexican seasoning, ready in 55 minutes — Autumn is my favorite time of year to cook! This recipe can be prepared either spicy or sweet, your choice! Two of my posted mexican-inspired seasoning mix recipes are offered as suggestions."

## Logging

All operations are logged with:
- Timestamps
- Progress indicators
- Statistics (enhancement rates, cleaning counts)
- Error handling with detailed messages

Logs are saved to `logs/text_enhancement_TIMESTAMP.log`

## Notes

- Processes entire dataset (~231K recipes) in approximately 10 minutes
- Maintains data integrity while enhancing readability
- Handles edge cases: missing descriptions, zero cook times, long cook times (days), etc.
- Safe for production use with comprehensive error handling
