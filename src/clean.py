# ============================================
# ENTITY CLEANING FUNCTIONS
# ============================================

from src.config import ACRONYMS

def clean_entity_name(entity):
    """
    Clean and normalize entity names (topics or companies).
    
    - Replaces underscores with spaces
    - Converts to title case
    - Handles common acronyms
    - Removes extra whitespace
    """
    if not isinstance(entity, str):
        return entity
    
    # Replace underscores with spaces and strip
    cleaned = entity.replace('_', ' ').strip()
    
    # If empty after cleaning, return original
    if not cleaned:
        return entity
    
    # Convert to title case (each word starts with capital)
    cleaned = cleaned.title()
    
    # Check if cleaned version matches any acronym
    if cleaned in ACRONYMS:
        return cleaned
    
    # Try uppercase version without spaces
    cleaned_upper = cleaned.upper().replace(' ', '')
    for acro in ACRONYMS:
        acro_clean = acro.upper().replace(' ', '')
        if cleaned_upper == acro_clean:
            return acro
    
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
    return ', '.join(companies) if companies else ''


def get_clean_topics_string(row):
    """Convert topics list to clean string for export."""
    if isinstance(row.get('extracted_topics'), list):
        return ', '.join([t for t in row['extracted_topics'] if t])
    return ''