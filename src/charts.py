# ============================================
# CHART GENERATION FUNCTIONS - USING CONFIG
# ============================================

import streamlit as st
import pandas as pd
import plotly.express as px
from src.clean import clean_entity_name
from src.config import COLORS

def plot_top_companies(df):
    """Generate top companies bar chart with cleaned names."""
    if 'extracted_companies' not in df.columns:
        return None
    
    company_counts = {}
    
    # Count from extracted_companies with cleaned names
    for comps in df['extracted_companies'].dropna():
        if isinstance(comps, list):
            for comp in comps:
                if comp and isinstance(comp, str):
                    clean_comp = clean_entity_name(comp)
                    company_counts[clean_comp] = company_counts.get(clean_comp, 0) + 1
    
    # Count from extracted_company with cleaned names
    for comp in df['extracted_company'].dropna():
        if comp and isinstance(comp, str):
            clean_comp = clean_entity_name(comp)
            company_counts[clean_comp] = company_counts.get(clean_comp, 0) + 1
    
    if not company_counts:
        return None
    
    # Sort alphabetically for display
    comp_df = pd.DataFrame(
        [(k, v) for k, v in company_counts.items() if k],
        columns=['Company', 'Mentions']
    ).sort_values(['Company', 'Mentions'], ascending=[True, False])
    
    # Take top 10 by mentions after alphabetical sort
    comp_df = comp_df.sort_values('Mentions', ascending=False).head(10)
    
    if comp_df.empty:
        return None
    
    fig = px.bar(
        comp_df,
        x='Company',
        y='Mentions',
        title='Most Mentioned Companies',
        color='Mentions',
        color_continuous_scale='blues'
    )
    fig.update_layout(xaxis_tickangle=-45)
    return fig

def plot_score_distribution(df):
    """Generate score distribution histogram."""
    fig = px.histogram(
        df,
        x='final_score',
        nbins=20,
        title='Article Relevance Scores',
        color_discrete_sequence=[COLORS['primary']]
    )
    fig.update_layout(xaxis_title="Score (%)", yaxis_title="Number of Articles")
    return fig

def plot_top_topics(df):
    """Generate top topics horizontal bar chart with cleaned names."""
    if 'extracted_topics' not in df.columns:
        return None
    
    topic_counts = {}
    for topics in df['extracted_topics'].dropna():
        if isinstance(topics, list):
            for topic in topics:
                if topic and isinstance(topic, str):
                    clean_topic = clean_entity_name(topic)
                    topic_counts[clean_topic] = topic_counts.get(clean_topic, 0) + 1
    
    if not topic_counts:
        return None
    
    # Sort alphabetically for display
    topic_df = pd.DataFrame(
        [(k, v) for k, v in topic_counts.items()],
        columns=['Topic', 'Mentions']
    ).sort_values(['Topic', 'Mentions'], ascending=[True, False])
    
    # Take top 10 by mentions after alphabetical sort
    topic_df = topic_df.sort_values('Mentions', ascending=False).head(10)
    
    fig = px.bar(
        topic_df,
        y='Topic',
        x='Mentions',
        orientation='h',
        title='Trending Topics',
        color='Mentions',
        color_continuous_scale='greens'
    )
    return fig

def plot_source_distribution(df):
    """Generate source distribution pie chart."""
    source_counts = df['verified_source_name'].value_counts().head(8)
    
    if source_counts.empty:
        return None
    
    fig = px.pie(
        values=source_counts.values,
        names=source_counts.index,
        title='Article Distribution by Source'
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig