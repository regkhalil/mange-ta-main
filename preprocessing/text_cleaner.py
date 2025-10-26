"""
Text cleaning module for recipe data.

This module provides comprehensive text cleaning functionality that can handle:
- Single text strings (descriptions)
- List columns stored as strings (tags, steps, ingredients)
- Proper capitalization, contractions, and punctuation
"""

import ast
import logging
import re
from typing import List, Optional, Union

import pandas as pd

# Set up logger for this module
logger = logging.getLogger(__name__)


def clean_text(text: str, apply_title_case: bool = False, is_sentence: bool = False) -> str:
    """
    Clean and properly format text strings.
    
    Restores contractions, fixes apostrophes, normalizes whitespace,
    and optionally applies title case or sentence case.
    
    Args:
        text: Raw text string
        apply_title_case: If True, applies title case capitalization (for names/titles)
        is_sentence: If True, capitalizes first letter only (for descriptions/sentences)
        
    Returns:
        Cleaned and formatted text
    """
    if not text or pd.isna(text):
        return ""
    
    # Restore common contractions from spaced versions
    contraction_patterns = {
        r"\bcan\s+t\b": "can't",
        r"\bdon\s+t\b": "don't",
        r"\bwon\s+t\b": "won't",
        r"\bdidn\s+t\b": "didn't",
        r"\bwouldn\s+t\b": "wouldn't",
        r"\bshouldn\s+t\b": "shouldn't",
        r"\bcouldn\s+t\b": "couldn't",
        r"\bisn\s+t\b": "isn't",
        r"\baren\s+t\b": "aren't",
        r"\bwasn\s+t\b": "wasn't",
        r"\bweren\s+t\b": "weren't",
        r"\bhasn\s+t\b": "hasn't",
        r"\bhaven\s+t\b": "haven't",
        r"\bhadn\s+t\b": "hadn't",
        r"\bit\s+s\b": "it's",
        r"\bthat\s+s\b": "that's",
        r"\bwhat\s+s\b": "what's",
        r"\bhere\s+s\b": "here's",
        r"\bthere\s+s\b": "there's",
        r"\bwho\s+s\b": "who's",
        r"\blet\s+s\b": "let's",
        r"\bwe\s+ll\b": "we'll",
        r"\bthey\s+ll\b": "they'll",
        r"\byou\s+ll\b": "you'll",
        r"\bhe\s+ll\b": "he'll",
        r"\bshe\s+ll\b": "she'll",
        r"\bi\s+ll\b": "I'll",
        r"\bwe\s+re\b": "we're",
        r"\bthey\s+re\b": "they're",
        r"\byou\s+re\b": "you're",
        r"\bi\s+m\b": "I'm",
        r"\bi\s+ve\b": "I've",
        r"\bwe\s+ve\b": "we've",
        r"\bthey\s+ve\b": "they've",
        r"\byou\s+ve\b": "you've",
    }
    
    for pattern, replacement in contraction_patterns.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Restore possessives (mom s -> mom's, grandma s -> grandma's)
    # More specific pattern to avoid false positives
    text = re.sub(r"\b([a-zA-Z]{3,})\s+s\b", r"\1's", text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Fix common punctuation issues
    text = re.sub(r'\s+([.,!?;:])', r'\1', text)  # Remove space before punctuation
    text = re.sub(r'([.,!?;:])\s*([.,!?;:])', r'\1\2', text)  # Remove duplicate punctuation
    
    # Apply capitalization
    if apply_title_case:
        text = _apply_smart_title_case(text)
    elif is_sentence:
        # Capitalize first letter and proper nouns
        if text:
            # Capitalize first letter after sentence start (. ! ? or em dash —)
            text = re.sub(r'(^|[.!?]\s+|—\s*)([a-z])', lambda m: m.group(1) + m.group(2).upper(), text)
            # Ensure very first character is capitalized
            if text[0].islower():
                text = text[0].upper() + text[1:]
            
            # Capitalize proper nouns (names, nationalities, countries)
            text = _capitalize_proper_nouns(text)
    
    return text


def _capitalize_proper_nouns(text: str) -> str:
    """
    Capitalize proper nouns like names, nationalities, and countries in sentence text.
    
    Args:
        text: Text to process
        
    Returns:
        Text with proper nouns capitalized
    """
    # Common proper nouns to capitalize
    proper_nouns = {
        # Family/People
        'mom', 'dad', 'grandma', 'grandpa', 'nana', 'papa', 'aunt', 'uncle',
        'mother', 'father', 'grandmother', 'grandfather',
        
        # Nationalities/Regions
        'italian', 'french', 'mexican', 'chinese', 'japanese', 'indian', 'thai',
        'american', 'canadian', 'british', 'english', 'spanish', 'greek', 'german',
        'korean', 'vietnamese', 'moroccan', 'lebanese', 'turkish', 'polish',
        'russian', 'brazilian', 'peruvian', 'argentinian', 'cuban', 'caribbean',
        'mediterranean', 'asian', 'european', 'latin', 'southern', 'northern',
        'eastern', 'western', 'midwestern', 'southwestern', 'cajun', 'creole',
        
        # Countries/Places
        'italy', 'france', 'mexico', 'china', 'japan', 'india', 'thailand',
        'america', 'canada', 'england', 'spain', 'greece', 'germany', 'korea',
        'vietnam', 'morocco', 'lebanon', 'turkey', 'poland', 'russia', 'brazil',
        'peru', 'argentina', 'cuba', 'texas', 'california', 'new york', 'chicago',
        
        # Holidays
        'christmas', 'thanksgiving', 'easter', 'halloween', 'valentine',
        
        # Days/Months
        'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
        'january', 'february', 'march', 'april', 'may', 'june', 'july',
        'august', 'september', 'october', 'november', 'december'
    }
    
    words = text.split()
    result = []
    
    for word in words:
        # Check if word (without punctuation) is a proper noun
        clean_word = word.strip('.,!?;:()[]"\'')
        if clean_word.lower() in proper_nouns:
            # Capitalize and preserve surrounding punctuation
            prefix = word[:len(word) - len(word.lstrip('.,!?;:()[]"\''))]
            suffix = word[len(clean_word) + len(prefix):]
            result.append(prefix + clean_word.capitalize() + suffix)
        else:
            result.append(word)
    
    return ' '.join(result)


def _apply_smart_title_case(text: str) -> str:
    """
    Apply title case with smart handling of small words and special terms.
    
    Args:
        text: Text to capitalize
        
    Returns:
        Text with proper title case
    """
    # Words that should stay lowercase (unless first/last word)
    small_words = {
        'a', 'an', 'and', 'as', 'at', 'but', 'by', 'for', 'in', 'nor',
        'of', 'on', 'or', 'so', 'the', 'to', 'up', 'yet', 'with'
    }
    
    # Words that should always be capitalized
    always_caps = {
        'mom', 'dad', 'grandma', 'grandpa', 'nana', 'papa', 'aunt', 'uncle', 'i'
    }
    
    words = text.split()
    result = []
    
    for i, word in enumerate(words):
        # Skip words with apostrophes for now (handled separately)
        if "'" in word:
            # Handle contractions: capitalize the part before the apostrophe
            parts = word.split("'")
            if parts[0].lower() in always_caps or i == 0:
                result.append(parts[0].capitalize() + "'" + "'".join(parts[1:]))
            else:
                result.append(parts[0].lower() + "'" + "'".join(parts[1:]))
        elif word.lower() in always_caps:
            result.append(word.capitalize())
        elif word.lower() in small_words and i != 0 and i != len(words) - 1:
            result.append(word.lower())
        else:
            result.append(word.capitalize())
    
    return ' '.join(result)


def clean_list_column(
    text_or_list: Union[str, List[str]], 
    apply_title_case: bool = False,
    capitalize_first: bool = False
) -> List[str]:
    """
    Clean a column that contains a list stored as a string.
    
    Handles columns like 'tags', 'steps', 'ingredients' that are stored as
    string representations of Python lists.
    
    Args:
        text_or_list: Either a string representation of a list (e.g., "['item1', 'item2']")
                     or an actual list
        apply_title_case: If True, applies title case to each list item (for names)
        capitalize_first: If True, capitalizes first letter only (for sentences like steps)
        
    Returns:
        List of cleaned strings
    """
    # Parse the string to a list if needed
    if isinstance(text_or_list, str):
        try:
            items = ast.literal_eval(text_or_list)
            if not isinstance(items, list):
                logger.warning(f"Expected list but got {type(items)}: {text_or_list[:50]}")
                return []
        except (ValueError, SyntaxError) as e:
            logger.warning(f"Failed to parse list: {text_or_list[:50]}... Error: {e}")
            return []
    elif isinstance(text_or_list, list):
        items = text_or_list
    else:
        logger.warning(f"Unexpected type {type(text_or_list)}")
        return []
    
    # Clean each item in the list
    cleaned_items = []
    for item in items:
        if isinstance(item, str):
            cleaned = clean_text(
                item, 
                apply_title_case=apply_title_case,
                is_sentence=capitalize_first
            )
            if cleaned:  # Only add non-empty strings
                cleaned_items.append(cleaned)
        else:
            # Keep non-string items as-is (shouldn't happen but handle gracefully)
            cleaned_items.append(str(item))
    
    return cleaned_items


def clean_dataframe_text_columns(
    df: pd.DataFrame,
    text_columns: Optional[List[str]] = None,
    list_columns: Optional[List[str]] = None,
    apply_title_case_to_lists: bool = False,
    inplace: bool = False
) -> pd.DataFrame:
    """
    Clean multiple text and list columns in a DataFrame.
    
    Args:
        df: Input DataFrame
        text_columns: List of column names containing plain text (e.g., ['description'])
        list_columns: List of column names containing string-encoded lists (e.g., ['tags', 'steps'])
        apply_title_case_to_lists: Whether to apply title case to list items
        inplace: If True, modifies df in place. Otherwise returns a copy.
        
    Returns:
        DataFrame with cleaned text columns (adds '_cleaned' suffix to column names)
    """
    if not inplace:
        df = df.copy()
    
    text_columns = text_columns or []
    list_columns = list_columns or []
    
    # Clean simple text columns
    for col in text_columns:
        if col not in df.columns:
            logger.warning(f"Column '{col}' not found in DataFrame")
            continue
        
        logger.info(f"Cleaning text column: {col}")
        new_col = f"{col}_cleaned"
        # Descriptions and similar text should have first letter capitalized
        df[new_col] = df[col].apply(lambda x: clean_text(x, apply_title_case=False, is_sentence=True))
    
    # Clean list columns
    for col in list_columns:
        if col not in df.columns:
            logger.warning(f"Column '{col}' not found in DataFrame")
            continue
        
        logger.info(f"Cleaning list column: {col}")
        new_col = f"{col}_cleaned"
        # Determine capitalization based on column type
        # Steps should capitalize first letter (sentences)
        # Ingredients should use title case (like names)
        # Tags generally stay lowercase unless specified
        if col == 'steps':
            capitalize_first = True
            title_case = False
        elif col == 'ingredients':
            capitalize_first = False
            title_case = True
        else:
            capitalize_first = False
            title_case = apply_title_case_to_lists
        
        df[new_col] = df[col].apply(
            lambda x: clean_list_column(
                x, 
                apply_title_case=title_case,
                capitalize_first=capitalize_first
            )
        )
    
    return df


def clean_recipe_data(
    df: pd.DataFrame,
    clean_name: bool = True,
    clean_description: bool = True,
    clean_steps: bool = True,
    clean_tags: bool = True,
    clean_ingredients: bool = True,
    inplace: bool = False
) -> pd.DataFrame:
    """
    Convenience function to clean common recipe columns.
    
    Args:
        df: Input DataFrame with recipe data
        clean_name: Clean the 'name' column (applies title case)
        clean_description: Clean the 'description' column
        clean_steps: Clean the 'steps' column (list)
        clean_tags: Clean the 'tags' column (list)
        clean_ingredients: Clean the 'ingredients' column (list)
        inplace: If True, modifies df in place
        
    Returns:
        DataFrame with cleaned columns (adds '_cleaned' suffix)
    """
    if not inplace:
        df = df.copy()
    
    logger.info("Starting comprehensive recipe data cleaning")
    
    # Clean name with title case
    if clean_name and 'name' in df.columns:
        logger.info("Cleaning 'name' column with title case")
        df['name_cleaned'] = df['name'].apply(lambda x: clean_text(x, apply_title_case=True))
    
    # Clean description with sentence case
    if clean_description and 'description' in df.columns:
        logger.info("Cleaning 'description' column")
        df['description_cleaned'] = df['description'].apply(
            lambda x: clean_text(x, apply_title_case=False, is_sentence=True)
        )
    
    # Clean list columns
    if clean_steps and 'steps' in df.columns:
        logger.info("Cleaning 'steps' column")
        df['steps_cleaned'] = df['steps'].apply(
            lambda x: clean_list_column(x, apply_title_case=False, capitalize_first=True)
        )
    
    if clean_tags and 'tags' in df.columns:
        logger.info("Cleaning 'tags' column")
        df['tags_cleaned'] = df['tags'].apply(
            lambda x: clean_list_column(x, apply_title_case=False, capitalize_first=False)
        )
    
    if clean_ingredients and 'ingredients' in df.columns:
        logger.info("Cleaning 'ingredients' column")
        # Apply title case to ingredients (like names) - capitalize all words except small words
        df['ingredients_cleaned'] = df['ingredients'].apply(
            lambda x: clean_list_column(x, apply_title_case=True, capitalize_first=False)
        )
    
    logger.info("Recipe data cleaning completed")
    return df


# Convenience function for quick testing
def demo_cleaning(sample_size: int = 5):
    """
    Demonstrate text cleaning on sample recipes.
    
    Args:
        sample_size: Number of recipes to sample
    """
    import pandas as pd
    
    logger.info(f"Loading {sample_size} sample recipes for demo")
    df = pd.read_csv('data/RAW_recipes.csv', nrows=sample_size)
    
    # Clean all recipe columns
    df_cleaned = clean_recipe_data(df, inplace=False)
    
    print("="*80)
    print("TEXT CLEANING DEMO")
    print("="*80)
    
    for i in range(min(3, len(df))):
        print(f"\n{'='*80}")
        print(f"RECIPE {i+1}: {df.iloc[i]['name']}")
        print(f"{'='*80}")
        
        # Show name cleaning
        print(f"\nNAME:")
        print(f"  Before: {df.iloc[i]['name']}")
        print(f"  After:  {df_cleaned.iloc[i]['name_cleaned']}")
        
        # Show description cleaning
        if pd.notna(df.iloc[i]['description']):
            print(f"\nDESCRIPTION:")
            print(f"  Before: {df.iloc[i]['description'][:80]}...")
            print(f"  After:  {df_cleaned.iloc[i]['description_cleaned'][:80]}...")
        
        # Show first 3 steps
        steps_orig = ast.literal_eval(df.iloc[i]['steps'])
        steps_clean = df_cleaned.iloc[i]['steps_cleaned']
        print(f"\nSTEPS (first 3):")
        for j in range(min(3, len(steps_orig))):
            print(f"  Before: {steps_orig[j][:60]}...")
            print(f"  After:  {steps_clean[j][:60]}...")
            print()


if __name__ == "__main__":
    # Set up logging for demo
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run demo
    demo_cleaning(sample_size=5)
