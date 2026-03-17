# ============================================
# MAIN STREAMLIT APPLICATION
# ============================================

import streamlit as st
from datetime import datetime

# Import our modules
from src.config import QUALITY_THRESHOLD, PREMIUM_PRICE_MONTHLY
from src.database import init_connection, load_data
from src.clean import get_clean_company_string, get_clean_topics_string
from src.filters import get_unique_companies, get_unique_topics, apply_filters
from src.charts import (
    plot_top_companies, plot_score_distribution,
    plot_top_topics, plot_source_distribution
)
from src.components import (
    render_metric_card, render_quality_badge,
    render_article_card, render_professional_header
)
from src.insights import render_insights_section
from src.export import render_export_section

# Page config
st.set_page_config(
    page_title="Career Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 10px;
    }
    .premium-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.7rem;
        margin-left: 8px;
    }
    @media (max-width: 768px) {
        .metric-card h2 {
            font-size: 1.2rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Title with premium badge
st.markdown("""
    <h1 style='display: flex; align-items: center; gap: 10px;'>
        📊 Career Intelligence Dashboard
        <span class='premium-badge'>PREMIUM</span>
    </h1>
""", unsafe_allow_html=True)
st.markdown("German labor market signals — updated daily from 23+ sources")

# Professional header
render_professional_header()

# Check premium access
def check_premium_access():
    """Check if user has premium access."""
    if 'premium' not in st.session_state:
        st.session_state.premium = False
    
    with st.sidebar.expander("🔐 Premium Access", expanded=not st.session_state.premium):
        password = st.text_input("Enter password", type="password")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔓 Unlock", use_container_width=True):
                # Get password from secrets or env
                premium_pass = None
                if "premium" in st.secrets:
                    premium_pass = st.secrets["premium"].get("password")
                else:
                    import os
                    premium_pass = os.getenv("PREMIUM_PASSWORD")
                
                if password == premium_pass:
                    st.session_state.premium = True
                    st.success("✅ Access granted!")
                    st.rerun()
                else:
                    st.error("❌ Invalid password")
        with col2:
            if st.button("🔗 Subscribe", use_container_width=True):
                st.markdown(f"[Get access →](https://careerintelligence.carrd.co)")
    
    return st.session_state.premium

is_premium = check_premium_access()

# Load data
with st.spinner("🔄 Loading latest signals..."):
    if is_premium:
        days = st.sidebar.slider("📅 Time window (days)", 7, 180, 30)
        df = load_data(days_back=days, is_premium=True)
    else:
        df = load_data(days_back=7, is_premium=False)
        st.sidebar.info(
            "🔍 **Free Preview**\n\n"
            "Showing last 7 days only.\n\n"
            f"[Subscribe for full access](https://careerintelligence.carrd.co) 📈"
        )

if df.empty:
    st.warning("⚠️ No data found. Check your MongoDB connection.")
    st.stop()

# ============================================
# TWO-TIER DATA APPROACH
# ============================================

# STATS DATA: All articles for accurate trends (after filters are applied)
# But we'll apply filters first, then separate

# QUALITY DATA: Only high-signal articles for display and download
# We'll create this after filters

# Sidebar filters
st.sidebar.header("🔍 Filters")

# Source filter
sources = df['verified_source_name'].dropna().unique().tolist()
selected_sources = st.sidebar.multiselect(
    "📰 Sources",
    options=sources,
    default=sources[:5] if len(sources) > 5 and is_premium else sources[:3]
)

# Min score filter
min_score = st.sidebar.slider("🎯 Min relevance score (%)", 0, 100, 0)

# Company filter
unique_companies = get_unique_companies(df)
selected_companies = st.sidebar.multiselect("🏢 Companies", options=unique_companies) if unique_companies else []

# Topic filter
unique_topics = get_unique_topics(df)
selected_topics = st.sidebar.multiselect("🔥 Topics", options=unique_topics) if unique_topics else []

# Apply filters
filtered_df = apply_filters(df, selected_sources, min_score, selected_companies, selected_topics)

# Now separate into stats (all) and quality (only >40%)
stats_df = filtered_df.copy()
quality_df = filtered_df[filtered_df['final_score'] > QUALITY_THRESHOLD].copy()

# Show quality stats
total_raw = len(stats_df)
total_quality = len(quality_df)
quality_pct = (total_quality / total_raw * 100) if total_raw > 0 else 0
render_quality_badge(quality_pct, total_quality, total_raw)

# ============================================
# METRICS SECTION
# ============================================
st.subheader("📈 Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    render_metric_card("Total Signals", len(stats_df), "📄", ("#667eea", "#764ba2"))

with col2:
    avg_score = stats_df['final_score'].mean()
    quality_avg = quality_df['final_score'].mean() if len(quality_df) > 0 else 0
    render_metric_card(
        "Avg Score", 
        f"{avg_score:.1f}%", 
        "⭐", 
        ("#00C2FF", "#0077B6"),
        subtitle=f"Quality: {quality_avg:.1f}%"
    )

with col3:
    if 'verified_source_name' in stats_df.columns:
        top_source = stats_df['verified_source_name'].value_counts().index[0] if len(stats_df) > 0 else "N/A"
        display_source = top_source[:15] + "..." if len(top_source) > 15 else top_source
        render_metric_card("Top Source", display_source, "📰", ("#FFD700", "#FFA500"))

with col4:
    time_range = f"Last {days} days" if is_premium else "Last 7 days"
    render_metric_card("Time Range", time_range, "📅", ("#FF6B6B", "#C92A2A"))

# ============================================
# INSIGHTS SECTION (Premium Only)
# ============================================
render_insights_section(is_premium)

# ============================================
# CHARTS SECTION
# ============================================
st.subheader("📊 Trends")

# Row 1
col1, col2 = st.columns(2)

with col1:
    st.markdown("**🔥 Most Mentioned Companies**")
    fig = plot_top_companies(stats_df)  # Using stats data for accurate trends
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No company data available")

with col2:
    st.markdown("**📊 Article Relevance Scores**")
    fig = plot_score_distribution(stats_df)
    st.plotly_chart(fig, use_container_width=True)

# Row 2
col1, col2 = st.columns(2)

with col1:
    st.markdown("**🔥 Trending Topics**")
    fig = plot_top_topics(stats_df)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No topic data available")

with col2:
    st.markdown("**📰 Top Sources**")
    fig = plot_source_distribution(stats_df)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No source data available")

# ============================================
# ARTICLE CARDS (Using QUALITY data)
# ============================================
st.subheader("📰 Top Quality Signals")
st.markdown(f"Showing {len(quality_df)} high-quality signals (score >{QUALITY_THRESHOLD}%)")

if len(quality_df) > 0:
    top_articles = quality_df.sort_values('final_score', ascending=False).head(20)
    
    for i in range(0, len(top_articles), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(top_articles):
                with cols[j]:
                    render_article_card(top_articles.iloc[i + j])
else:
    st.info("No high-quality signals match your filters. Try adjusting your criteria.")

# ============================================
# CSV EXPORT (Premium Only, using QUALITY data)
# ============================================
render_export_section(is_premium, filtered_df, quality_df)

# ============================================
# PREMIUM UPSELL FOR FREE USERS
# ============================================
if not is_premium:
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info(
            f"🚀 **Upgrade to Premium**\n\n"
            f"• 📊 6 months of historical data\n"
            f"• 📈 Advanced filters\n"
            f"• 📉 Clean CSV exports\n"
            f"• 🧠 AI-powered insights\n\n"
            f"[👉 Subscribe for €{PREMIUM_PRICE_MONTHLY}/month](https://careerintelligence.carrd.co)"
        )

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "🚀 Built with Streamlit • Data from 23+ German sources • Updated daily<br>"
    "© 2026 Career Intelligence • All rights reserved"
    "</div>",
    unsafe_allow_html=True
)