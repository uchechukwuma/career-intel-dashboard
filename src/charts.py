# ============================================
# CHART GENERATION FUNCTIONS
# ============================================

import streamlit as st
import pandas as pd
import plotly.express as px
from src.clean import clean_entity_name


def plot_top_companies(df):
    """Generate top companies bar chart."""
    if 'extracted_companies' not in df.columns:
        return None
    
    company_counts = {}
    
    # Count from extracted_companies
    for comps in df['extracted_companies'].dropna():
        if isinstance(comps, list):
            for comp in comps:
                if comp and isinstance(comp, str):
                    company_counts[comp] = company_counts.get(comp, 0) + 1
    
    # Count from extracted_company
    for comp in df['extracted_company'].dropna():
        if comp and isinstance(comp, str):
            company_counts[comp] = company_counts.get(comp, 0) + 1
    
    if not company_counts:
        return None
    
    comp_df = pd.DataFrame(
        [(k, v) for k, v in company_counts.items() if k],
        columns=['Company', 'Mentions']
    ).sort_values('Mentions', ascending=False).head(10)
    
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
        color_discrete_sequence=['#00C2FF']
    )
    fig.update_layout(xaxis_title="Score (%)", yaxis_title="Number of Articles")
    return fig


def plot_top_topics(df):
    """Generate top topics horizontal bar chart."""
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
    
    topic_df = pd.DataFrame(
        [(k, v) for k, v in topic_counts.items()],
        columns=['Topic', 'Mentions']
    ).sort_values('Mentions', ascending=False).head(10)
    
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