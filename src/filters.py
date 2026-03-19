
# ============================================
# FILTERING AND DATA PREPARATION - WITH FUZZY GROUPING
# ============================================

import streamlit as st
from collections import Counter
import pandas as pd
from difflib import SequenceMatcher
from src.clean import clean_entity_name

def consolidate_topics(topics_list, threshold=0.8):
    """Group similar topics together using fuzzy matching."""
    if not topics_list:
        return []
    
    # Clean all topics first
    cleaned = [clean_entity_name(t) for t in topics_list if t]
    cleaned = list(set(cleaned))  # Remove exact duplicates
    
    groups = []
    used = set()
    
    for i, topic1 in enumerate(cleaned):
        if i in used:
            continue
        
        group = [topic1]
        used.add(i)
        
        for j, topic2 in enumerate(cleaned[i+1:], i+1):
            if j in used:
                continue
            
            # Check similarity
            similarity = SequenceMatcher(None, topic1.lower(), topic2.lower()).ratio()
            
            # Special handling for common variations
            if topic1.lower().replace(' ', '') == topic2.lower().replace(' ', ''):
                similarity = 1.0
            
            # Handle acronyms
            if len(topic1) <= 5 and topic1.isupper() and topic2.upper() == topic1:
                similarity = 1.0
            
            if similarity > threshold:
                group.append(topic2)
                used.add(j)
        
        groups.append(group)
    
    return groups

def get_unique_companies(df):
    """Extract and sort unique companies from dataframe."""
    all_companies = []
    for comps in df['extracted_companies'].dropna():
        if isinstance(comps, list):
            all_companies.extend(comps)
    # Add single company field
    single_companies = df['extracted_company'].dropna().tolist()
    all_companies.extend(single_companies)
    
    if all_companies:
        # Clean each company name
        cleaned_companies = [clean_entity_name(c) for c in all_companies if c]
        # Remove duplicates and sort alphabetically
        unique_cleaned = sorted(set(cleaned_companies))
        return unique_cleaned
    return []

def get_unique_topics(df):
    """Extract and return unique topics with grouping info."""
    all_topics = []
    for topics in df['extracted_topics'].dropna():
        if isinstance(topics, list):
            all_topics.extend(topics)
    
    if all_topics:
        # Clean each topic
        cleaned_topics = [clean_entity_name(t) for t in all_topics if t]
        # Remove duplicates and sort
        return sorted(set(cleaned_topics))
    return []

def apply_filters(df, selected_sources, min_score, selected_companies, selected_topics):
    """Apply all selected filters to dataframe."""
    filtered_df = df.copy()
    
    if selected_sources:
        filtered_df = filtered_df[filtered_df['verified_source_name'].isin(selected_sources)]
    
    filtered_df = filtered_df[filtered_df['final_score'] >= min_score]
    
    if selected_companies:
        # Clean selected companies for comparison
        cleaned_selected = [clean_entity_name(c) for c in selected_companies]
        
        filtered_df = filtered_df[
            filtered_df['extracted_companies'].apply(
                lambda x: any(clean_entity_name(comp) in cleaned_selected for comp in x) if isinstance(x, list) else False
            ) | filtered_df['extracted_company'].apply(
                lambda x: clean_entity_name(x) in cleaned_selected if pd.notna(x) else False
            )
        ]
    
    if selected_topics:
        # Clean selected topics for comparison
        cleaned_selected = [clean_entity_name(t) for t in selected_topics]
        
        filtered_df = filtered_df[
            filtered_df['extracted_topics'].apply(
                lambda x: any(clean_entity_name(topic) in cleaned_selected for topic in x) if isinstance(x, list) else False
            )
        ]
    
    return filtered_df

# Cache for topic groups to avoid recomputing on every rerun
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_topic_groups(_df, topics_list=None):
    """
    Cached function to compute topic groups.
    The underscore in _df tells st.cache_data to ignore it for hashing.
    """
    if topics_list is None:
        # Extract topics from dataframe if not provided
        all_topics = []
        for topics in _df['extracted_topics'].dropna():
            if isinstance(topics, list):
                all_topics.extend(topics)
        topics_list = [clean_entity_name(t) for t in all_topics if t]
    
    if not topics_list:
        return []
    
    # Clean and deduplicate
    cleaned = list(set(topics_list))
    cleaned.sort()
    
    groups = []
    used = set()
    
    for i, topic1 in enumerate(cleaned):
        if i in used:
            continue
        
        group = [topic1]
        used.add(i)
        
        for j, topic2 in enumerate(cleaned[i+1:], i+1):
            if j in used:
                continue
            
            # Quick checks before expensive SequenceMatcher
            if len(topic1) <= 5 and topic1.isupper() and topic2.upper() == topic1:
                similarity = 1.0
            elif topic1.lower().replace(' ', '') == topic2.lower().replace(' ', ''):
                similarity = 1.0
            else:
                # Only run SequenceMatcher if names are somewhat similar in length
                if abs(len(topic1) - len(topic2)) > 5:
                    continue
                similarity = SequenceMatcher(None, topic1.lower(), topic2.lower()).ratio()
            
            if similarity > 0.8:
                group.append(topic2)
                used.add(j)
        
        groups.append(group)
    
    return groups