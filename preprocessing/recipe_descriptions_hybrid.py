"""
Enhanced recipe descriptor module - Hybrid approach.

Combines original user descriptions with extracted metadata naturally,
without parentheses or awkward formatting.
"""

import ast
import logging
import re
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


def extract_metadata_tags(tags_str: str) -> dict:
    """
    Extract useful metadata from recipe tags.
    
    Returns dict with cuisine, dietary, meal_type, difficulty, occasion lists.
    """
    try:
        tags = ast.literal_eval(tags_str) if isinstance(tags_str, str) else []
    except:
        tags = []
    
    # Cuisine tags
    cuisine_keywords = ['american', 'italian', 'mexican', 'asian', 'chinese', 'indian', 
                       'french', 'greek', 'thai', 'japanese', 'spanish', 'german', 
                       'middle-eastern', 'cajun', 'southern', 'southwestern']
    cuisines = [t for t in tags if any(k in t.lower() for k in cuisine_keywords)]
    
    # Dietary tags
    dietary_keywords = ['vegetarian', 'vegan', 'low-fat', 'low-calorie', 'healthy', 
                       'low-sodium', 'low-cholesterol', 'gluten-free', 'dairy-free',
                       'sugar-free', 'low-carb', 'high-protein']
    dietary = [t for t in tags if any(k in t.lower() for k in dietary_keywords)]
    
    # Meal type
    meal_keywords = ['breakfast', 'lunch', 'dinner', 'brunch', 'snack', 'appetizer', 
                    'dessert', 'main-dish', 'side-dish', 'salad', 'soup']
    meals = [t for t in tags if any(k in t.lower() for k in meal_keywords)]
    
    # Difficulty
    difficulty_keywords = ['easy', 'beginner', 'simple', '5-ingredients-or-less', 
                          'quick', '15-minutes-or-less', '30-minutes-or-less']
    difficulty = [t for t in tags if any(k in t.lower() for k in difficulty_keywords)]
    
    # Occasion
    occasion_keywords = ['holiday', 'christmas', 'thanksgiving', 'summer', 'winter',
                        'party', 'picnic', 'weeknight', 'kid-friendly', 'romantic']
    occasions = [t for t in tags if any(k in t.lower() for k in occasion_keywords)]
    
    return {
        'cuisine': cuisines[:2],  # Top 2
        'dietary': dietary[:2],
        'meal': meals[:2],
        'difficulty': difficulty[:1],
        'occasion': occasions[:1]
    }


def format_tag(tag: str) -> str:
    """Format a tag for natural language (remove hyphens, capitalize)."""
    return tag.replace('-', ' ').title()


def format_time(minutes: Optional[int]) -> str:
    """
    Format cooking time in a natural, readable way.
    
    Args:
        minutes: Time in minutes
        
    Returns:
        Formatted time string (e.g., "about 30 minutes", "approximately 2 hours")
    """
    if not minutes or minutes <= 0:
        return ""
    
    # Under 5 minutes
    if minutes < 5:
        return f"about {minutes} minutes"
    
    # 5-59 minutes: round to nearest 5
    elif minutes < 60:
        rounded = round(minutes / 5) * 5
        if rounded == minutes:
            return f"{minutes} minutes"
        else:
            return f"approximately {rounded} minutes"
    
    # 60-119 minutes: "about 1 hour" or "1 hour 15 minutes"
    elif minutes < 120:
        if minutes == 60:
            return "1 hour"
        elif minutes <= 75:
            return "about 1 hour"
        elif minutes <= 90:
            return "about 1 hour 15 minutes"
        else:
            return "approximately 1 hour 30 minutes"
    
    # 24+ hours (1440+ minutes): use days
    elif minutes >= 1440:
        days = minutes / 1440
        if minutes % 1440 == 0:
            day_str = "day" if int(days) == 1 else "days"
            return f"over {int(days)} {day_str}"
        else:
            # Round up to next day
            day_str = "day" if int(days) + 1 == 1 else "days"
            return f"over {int(days) + 1} {day_str}"
    
    # 2-23 hours: use rounded hour or hour + 30 min approximations
    else:
        hours = minutes / 60
        remainder = minutes % 60
        
        # Exact hours
        if remainder == 0:
            return f"{int(hours)} hours"
        # 0-15 min: round down to hour
        elif remainder <= 15:
            return f"about {int(hours)} hours"
        # 15-45 min: use hour + 30 min
        elif remainder <= 45:
            return f"about {int(hours)} hours 30 minutes"
        # 45-60 min: round up to next hour
        else:
            return f"about {int(hours) + 1} hours"


def extract_technique_from_tags(tags_list: list) -> Optional[str]:
    """
    Extract cooking technique from tags.
    
    Returns:
        Technique string like "Baked", "Grilled", "No-Cook", etc.
    """
    # Priority order - check specific techniques first
    technique_keywords = [
        ('crock-pot-slow-cooker', 'Slow Cooker'),
        ('slow-cooker', 'Slow Cooker'),
        ('crock-pot', 'Crock Pot'),
        ('pressure-cooker', 'Pressure Cooker'),
        ('instant-pot', 'Instant Pot'),
        ('no-cook', 'No-Cook'),
        ('grilled', 'Grilled'),
        ('roasted', 'Roasted'),
        ('baked', 'Baked'),
        ('broiled', 'Broiled'),
        ('smoked', 'Smoked'),
        ('deep-fried', 'Deep Fried'),
        ('pan-fried', 'Pan-Fried'),
        ('fried', 'Fried'),
        ('sauteed', 'Sautéed'),
        ('stir-fry', 'Stir-Fried'),
        ('steamed', 'Steamed'),
        ('poached', 'Poached'),
        ('braised', 'Braised'),
        ('microwaved', 'Microwaved'),
        ('microwave', 'Microwaved'),
        ('stove-top', 'Stovetop'),
        ('oven', 'Oven-Baked'),
        ('canning', 'Canned'),
        ('freezer', 'Freezer-Friendly')
    ]
    
    # Check each tag for technique keywords in priority order
    for tag in tags_list:
        tag_lower = tag.lower()
        for keyword, technique in technique_keywords:
            if keyword == tag_lower or keyword in tag_lower:
                return technique
    
    return None


def extract_main_ingredients(ingredients_str: str, max_ingredients: int = 2) -> list:
    """
    Extract and clean the main (first few) ingredients from the recipe.
    
    Args:
        ingredients_str: String or list of ingredients
        max_ingredients: Maximum number of ingredients to return
        
    Returns:
        List of cleaned ingredient names
    """
    try:
        ingredients = ast.literal_eval(ingredients_str) if isinstance(ingredients_str, str) else ingredients_str
    except:
        return []
    
    if not ingredients:
        return []
    
    # Get first few ingredients and clean them
    main_ingredients = []
    for ingredient in ingredients[:max_ingredients + 3]:  # Get extras in case we skip some
        # Clean ingredient name
        cleaned = ingredient.lower().strip()
        
        # Skip very generic ingredients
        skip_words = ['salt', 'pepper', 'water', 'oil', 'butter', 'sugar', 
                     'flour', 'salt and pepper', 'cooking spray', 'vegetable oil',
                     'olive oil', 'canola oil', 'eggs']
        if cleaned in skip_words:
            continue
        
        # Take first part if there are measurements
        parts = cleaned.split()
        # Skip leading numbers and measurements
        skip_measurements = ['cup', 'cups', 'tablespoon', 'tablespoons', 'teaspoon', 
                           'teaspoons', 'pound', 'pounds', 'ounce', 'ounces', 
                           'lb', 'lbs', 'oz', 'tbsp', 'tsp', 'pkg', 'package']
        
        cleaned_parts = []
        for part in parts:
            # Skip if it's a number or measurement
            if part.replace('.', '').replace('/', '').replace('-', '').isdigit():
                continue
            if part in skip_measurements:
                continue
            cleaned_parts.append(part)
        
        if cleaned_parts:
            ingredient_name = ' '.join(cleaned_parts)
            
            # Shorten very long ingredient names
            if len(ingredient_name) > 25:
                # Take first key words
                words = ingredient_name.split()
                if len(words) > 3:
                    ingredient_name = ' '.join(words[:3])
                    # Remove trailing prepositions or conjunctions
                    trailing_words = ['with', 'and', 'or', 'in', 'on', 'of', 'for']
                    while ingredient_name.split()[-1].lower() in trailing_words:
                        words = ingredient_name.split()[:-1]
                        if not words:  # Don't remove all words
                            break
                        ingredient_name = ' '.join(words)
            
            # Capitalize for display
            ingredient_name = ingredient_name.title()
            main_ingredients.append(ingredient_name)
            
            if len(main_ingredients) >= max_ingredients:
                break
    
    return main_ingredients


def create_enhanced_description(
    original_desc: str,
    minutes: Optional[int],
    metadata: dict,
    ingredients_list: Optional[list] = None,
    raw_tags: Optional[list] = None,
    include_time_when_short: bool = True
) -> str:
    """
    Create enhanced description as a single natural sentence.
    Format: "[Technique] [meal type] with [ingredients], ready in [time] — [original description]."
    
    The metadata, ingredients, and duration come first, then the user's description is appended.
    """
    has_desc = original_desc and len(original_desc.strip()) > 0
    original_desc = original_desc.strip() if has_desc else ""
    
    # Extract technique from raw tags (more reliable than metadata)
    technique = None
    if raw_tags:
        technique = extract_technique_from_tags(raw_tags)
    
    # Format time
    time_str = format_time(minutes) if minutes and minutes < 1440 else ""  # Cap at 24 hours (1 day)
    
    # Build metadata descriptors
    descriptors = []
    
    # Add technique first (if found)
    if technique:
        descriptors.append(technique.lower())
    
    # Add meal type
    if metadata['meal']:
        meal = format_tag(metadata['meal'][0])
        # Clean up redundant words and normalize
        meal = meal.replace('-Dish', '').replace('-', ' ')
        if 'Side' in meal:
            meal = 'side dish'
        elif 'Main' in meal:
            meal = 'main dish'
        elif 'Appetizer' in meal:
            meal = 'appetizer'
        elif 'Dessert' in meal:
            meal = 'dessert'
        elif 'Breakfast' in meal:
            meal = 'breakfast'
        elif 'Lunch' in meal:
            meal = 'lunch'
        elif 'Dinner' in meal:
            meal = 'dinner'
        elif 'Snack' in meal:
            meal = 'snack'
        else:
            meal = meal.lower()
        
        # Skip generic tags
        if meal.lower() not in ['course', 'preparation', 'occasion']:
            descriptors.append(meal)
    
    # Add cuisine
    if metadata['cuisine']:
        cuisine = format_tag(metadata['cuisine'][0])
        # Skip generic tags
        if cuisine not in ['North American', 'Preparation', 'Cuisine']:
            descriptors.append(cuisine.lower())
    
    # Add dietary (most distinctive one)
    if metadata['dietary']:
        dietary = format_tag(metadata['dietary'][0])
        descriptors.append(dietary.lower())
    
    # Build template with ingredients
    template_parts = []
    
    if descriptors:
        # Capitalize first descriptor for start of sentence
        desc_text = ' '.join(descriptors[:3])  # Max 3 descriptors
        desc_text = desc_text[0].upper() + desc_text[1:] if desc_text else ""
        
        # Add ingredients if available
        if ingredients_list and len(ingredients_list) > 0:
            ingredients_str = ' and '.join(ingredients_list) if len(ingredients_list) <= 2 else ', '.join(ingredients_list[:-1]) + ' and ' + ingredients_list[-1]
            template_parts.append(f"{desc_text} recipe with {ingredients_str.lower()}")
        else:
            template_parts.append(desc_text + " recipe")
    elif ingredients_list and len(ingredients_list) > 0:
        # No descriptors but we have ingredients - show them
        ingredients_str = ' and '.join(ingredients_list) if len(ingredients_list) <= 2 else ', '.join(ingredients_list[:-1]) + ' and ' + ingredients_list[-1]
        template_parts.append(f"Recipe with {ingredients_str.lower()}")
    
    # Add time with special handling for quick recipes
    if time_str:
        # For very short times (under 15 min), emphasize speed
        if minutes and minutes > 0 and minutes <= 15:
            template_parts.append(f"quick and ready in {time_str}")
        else:
            template_parts.append(f"ready in {time_str}")
    
    # Build the final sentence
    if template_parts:
        template = ', '.join(template_parts)
        
        if has_desc:
            # Ensure original description starts with lowercase (will be mid-sentence)
            clean_desc = original_desc.rstrip('.')
            if clean_desc and clean_desc[0].isupper():
                clean_desc = clean_desc[0].lower() + clean_desc[1:]
            
            # Template first, then user description
            return f"{template} — {clean_desc}."
        else:
            # No user description, just the template
            return f"{template}."
    
    else:
        # No template parts - ensure description is properly capitalized
        if has_desc:
            clean_desc = original_desc.rstrip('.')
            # Capitalize first letter
            if clean_desc:
                clean_desc = clean_desc[0].upper() + clean_desc[1:] if len(clean_desc) > 1 else clean_desc.upper()
            return f"{clean_desc}."
        else:
            return ""
    if template_parts:
        template = ', '.join(template_parts)
        
        if has_desc:
            # Ensure original description starts with lowercase (will be mid-sentence)
            clean_desc = original_desc.rstrip('.')
            if clean_desc and clean_desc[0].isupper():
                clean_desc = clean_desc[0].lower() + clean_desc[1:]
            
            # Template first, then user description
            return f"{template} — {clean_desc}."
        else:
            # No user description, just the template
            return f"{template}."
    
    else:
        # No metadata or time, just return user description with proper capitalization
        if has_desc:
            clean_desc = original_desc.rstrip('.')
            if clean_desc and clean_desc[0].islower():
                clean_desc = clean_desc[0].upper() + clean_desc[1:]
            return f"{clean_desc}."
        else:
            return ""


def enhance_recipe_descriptions(
    df: pd.DataFrame,
    original_desc_col: str = 'description',
    time_col: str = 'minutes',
    tags_col: str = 'tags',
    ingredients_col: str = 'ingredients',
    output_col: str = 'description_enhanced',
    inplace: bool = False
) -> pd.DataFrame:
    """
    Enhance recipe descriptions by combining original text with metadata and ingredients.
    
    Args:
        df: DataFrame with recipe data
        original_desc_col: Column with original descriptions
        time_col: Column with cooking time in minutes
        tags_col: Column with recipe tags
        ingredients_col: Column with recipe ingredients
        output_col: Name for new enhanced description column
        inplace: Whether to modify DataFrame in place
        
    Returns:
        DataFrame with enhanced descriptions
    """
    if not inplace:
        df = df.copy()
    
    logger.info(f"Enhancing descriptions for {len(df)} recipes")
    
    def enhance_row(row):
        # Get original description
        orig_desc = row[original_desc_col] if pd.notna(row[original_desc_col]) else ""
        
        # Get time (only if reasonable)
        minutes = None
        if pd.notna(row[time_col]) and 0 < row[time_col] < 10000:  # Cap at very high but realistic times
            minutes = int(row[time_col])
        
        # Get raw tags for technique extraction
        raw_tags = None
        if pd.notna(row[tags_col]):
            try:
                raw_tags = ast.literal_eval(row[tags_col]) if isinstance(row[tags_col], str) else row[tags_col]
            except:
                raw_tags = []
        
        # Extract metadata from tags
        metadata = extract_metadata_tags(row[tags_col])
        
        # Extract main ingredients
        ingredients = None
        if ingredients_col in row and pd.notna(row[ingredients_col]):
            ingredients = extract_main_ingredients(row[ingredients_col], max_ingredients=2)
        
        # Create enhanced description
        return create_enhanced_description(orig_desc, minutes, metadata, ingredients, raw_tags)
    
    df[output_col] = df.apply(enhance_row, axis=1)
    
    # Statistics
    enhanced = df[output_col].notna() & (df[output_col] != "")
    logger.info(f"Enhanced {enhanced.sum()} descriptions")
    
    return df


# Convenience function for demo
def demo_enhancement(sample_size: int = 20):
    """Demonstrate description enhancement on sample recipes."""
    import pandas as pd
    
    logger.info(f"Loading {sample_size} sample recipes")
    df = pd.read_csv('data/RAW_recipes.csv', nrows=sample_size)
    
    # Enhance descriptions
    df_enhanced = enhance_recipe_descriptions(df)
    
    print("="*80)
    print("DESCRIPTION ENHANCEMENT DEMO")
    print("="*80)
    
    for i in range(min(10, len(df))):
        print(f"\n{i+1}. Recipe: {df.iloc[i]['name']}")
        print("-"*80)
        
        orig = df.iloc[i]['description'] if pd.notna(df.iloc[i]['description']) else "[No description]"
        enhanced = df_enhanced.iloc[i]['description_enhanced']
        
        print(f"Original ({len(orig)} chars):")
        print(f"  {orig[:150]}..." if len(orig) > 150 else f"  {orig}")
        
        print(f"\nEnhanced ({len(enhanced)} chars):")
        print(f"  {enhanced[:150]}..." if len(enhanced) > 150 else f"  {enhanced}")
        print()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    demo_enhancement(sample_size=20)
