# ============================================
# FILTERING AND DATA PREPARATION
# ============================================

import streamlit as st
from collections import Counter
import pandas as pd


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
        company_counter = Counter(all_companies)
        return sorted([c for c in set(all_companies) if c], 
                     key=lambda x: (-company_counter[x], x))
    return []


def get_unique_topics(df):
    """Extract and sort unique topics from dataframe."""
    all_topics = []
    for topics in df['extracted_topics'].dropna():
        if isinstance(topics, list):
            all_topics.extend(topics)
    
    if all_topics:
        topic_counter = Counter(all_topics)
        return sorted([t for t in set(all_topics) if t],
                     key=lambda x: (-topic_counter[x], x))
    return []


def apply_filters(df, selected_sources, min_score, selected_companies, selected_topics):
    """Apply all selected filters to dataframe."""
    filtered_df = df.copy()
    
    if selected_sources:
        filtered_df = filtered_df[filtered_df['verified_source_name'].isin(selected_sources)]
    
    filtered_df = filtered_df[filtered_df['final_score'] >= min_score]
    
    if selected_companies:
        filtered_df = filtered_df[
            filtered_df['extracted_companies'].apply(
                lambda x: any(comp in x for comp in selected_companies) if isinstance(x, list) else False
            ) | filtered_df['extracted_company'].isin(selected_companies)
        ]
    
    if selected_topics:
        filtered_df = filtered_df[
            filtered_df['extracted_topics'].apply(
                lambda x: any(topic in x for topic in selected_topics) if isinstance(x, list) else False
            )
        ]
    
    return filtered_df