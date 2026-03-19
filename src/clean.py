# ============================================
# ENTITY CLEANING FUNCTIONS - USING CONFIG
# ============================================

from src.config import ACRONYMS

def format_entity_properly(entity):
    """Format entity with proper casing (AI, not Ai)."""
    if not entity or not isinstance(entity, str):
        return entity
    
    # Build acronym lookup from config
    acronym_dict = {acro.lower(): acro for acro in ACRONYMS}
    
    # Also add common variations
    special_cases = {
        'ki': 'KI',
        'kI': 'KI',
        'iT': 'IT',
        'ag': 'AG',
        'gmbh': 'GmbH',
        'dax': 'DAX',
    }
    acronym_dict.update({k.lower(): v for k, v in special_cases.items()})
    
    # Check if it's an acronym (case insensitive)
    entity_lower = entity.lower().strip()
    if entity_lower in acronym_dict:
        return acronym_dict[entity_lower]
    
    # Otherwise, do smart title case
    words = entity.split()
    formatted = []
    for word in words:
        word_lower = word.lower()
        if word_lower in acronym_dict:
            formatted.append(acronym_dict[word_lower])
        elif len(word) > 2 and word.isupper():
            # If it's already uppercase, keep it
            formatted.append(word)
        else:
            # Normal title case
            formatted.append(word.capitalize())
    
    return ' '.join(formatted)

def clean_entity_name(entity):
    """
    Clean and normalize entity names (topics or companies).
    
    - Replaces underscores with spaces
    - Handles common acronyms (AI, not Ai)
    - Removes extra whitespace
    """
    if not isinstance(entity, str):
        return entity
    
    # Replace underscores with spaces and strip
    cleaned = entity.replace('_', ' ').strip()
    
    # If empty after cleaning, return original
    if not cleaned:
        return entity
    
    # Format with proper casing
    cleaned = format_entity_properly(cleaned)
    
    # Special case for "And" in company names
    cleaned = cleaned.replace(' And ', ' and ')
    
    # Special case for "Der", "Die", "Das" (German articles)
    cleaned = cleaned.replace(' Der ', ' der ')
    cleaned = cleaned.replace(' Die ', ' die ')
    cleaned = cleaned.replace(' Das ', ' das ')
    cleaned = cleaned.replace(' Des ', ' des ')
    cleaned = cleaned.replace(' Dem ', ' dem ')
    cleaned = cleaned.replace(' Den ', ' den ')
    
    # Special case for prepositions
    cleaned = cleaned.replace(' In ', ' in ')
    cleaned = cleaned.replace(' An ', ' an ')
    cleaned = cleaned.replace(' Auf ', ' auf ')
    cleaned = cleaned.replace(' Aus ', ' aus ')
    cleaned = cleaned.replace(' Bei ', ' bei ')
    cleaned = cleaned.replace(' Mit ', ' mit ')
    cleaned = cleaned.replace(' Von ', ' von ')
    cleaned = cleaned.replace(' Zu ', ' zu ')
    
    return cleaned

def clean_entity_list(entity_list):
    """
    Clean a list of entity names.
    
    - Applies clean_entity_name to each item
    - Removes duplicates
    - Filters out empty strings
    """
    if not isinstance(entity_list, list):
        return entity_list
    
    cleaned = []
    for entity in entity_list:
        if entity and isinstance(entity, str):
            cleaned_entity = clean_entity_name(entity)
            if cleaned_entity and cleaned_entity.strip():
                cleaned.append(cleaned_entity)
    
    # Remove duplicates while preserving order
    seen = set()
    deduped = []
    for entity in cleaned:
        if entity not in seen:
            seen.add(entity)
            deduped.append(entity)
    
    return deduped

def get_clean_company_string(row):
    """Convert companies to clean string for display and export."""
    companies = []
    if row.get('extracted_company') and isinstance(row['extracted_company'], str):
        companies.append(row['extracted_company'])
    if isinstance(row.get('extracted_companies'), list):
        companies.extend(row['extracted_companies'])
    # Remove duplicates
    companies = list(dict.fromkeys(companies))
    
    # Sort alphabetically
    companies.sort()
    
    return ', '.join(companies) if companies else ''

def get_clean_topics_string(row):
    """Convert topics list to clean string for export."""
    if isinstance(row.get('extracted_topics'), list):
        topics = [t for t in row['extracted_topics'] if t]
        # Sort alphabetically
        topics.sort()
        return ', '.join(topics)
    return ''