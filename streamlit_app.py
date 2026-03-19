# ============================================
# MAIN STREAMLIT APPLICATION
# ============================================

import streamlit as st
from datetime import datetime, timedelta

# Import our modules
from src.config import QUALITY_THRESHOLD, PREMIUM_PRICE_MONTHLY, HIGH_IMPACT_THRESHOLD, COLORS
from src.database import init_connection, load_data
from src.clean import get_clean_company_string, get_clean_topics_string, clean_entity_name
from src.filters import get_unique_companies, get_unique_topics, apply_filters, consolidate_topics
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
    .topic-group {
        margin-bottom: 10px;
        padding: 8px;
        background-color: #f8f9fa;
        border-radius: 5px;
        border-left: 3px solid #00C2FF;
    }
    .topic-group strong {
        color: #0A0F1F;
    }
    .debug-info {
        font-size: 0.8rem;
        color: #666;
        margin-top: 5px;
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

# Load data with appropriate spinner
if is_premium:
    days = st.sidebar.slider("📅 Time window (days)", 7, 180, 30)
    # No spinner here - the progress bar in load_data handles it
    df = load_data(days_back=days, is_premium=True)
else:
    days = 7  # Default for free users
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
# DEBUG: Check score distribution (optional)
# ============================================
if st.sidebar.checkbox("Show Score Debug", False):
    st.sidebar.markdown("### 📊 Score Distribution")
    if 'final_score' in df.columns:
        score_ranges = {
            "90-100%": len(df[df['final_score'] >= 90]),
            "70-89%": len(df[(df['final_score'] >= 70) & (df['final_score'] < 90)]),
            "50-69%": len(df[(df['final_score'] >= 50) & (df['final_score'] < 70)]),
            "40-49%": len(df[(df['final_score'] >= 40) & (df['final_score'] < 50)]),
            "<40%": len(df[df['final_score'] < 40]),
        }
        for range_name, count in score_ranges.items():
            st.sidebar.write(f"{range_name}: {count} articles")
    
    # Check field existence
    st.sidebar.markdown("### 🔧 Field Check")
    for field in ['timeliness', 'geographic_relevance', 'career_impact']:
        if field in df.columns:
            non_zero = (df[field] > 0).sum()
            st.sidebar.write(f"{field}: {non_zero}/{len(df)} non-zero")

# ============================================
# FILTER FOR RECENT ARTICLES (Last 7 days for display)
# ============================================

def filter_recent_articles(df, days=7):
    """Filter dataframe to only include articles from last N days."""
    if 'published_at' in df.columns:
        cutoff = datetime.now() - timedelta(days=days)
        return df[df['published_at'] > cutoff]
    return df

# ============================================
# TWO-TIER DATA APPROACH
# ============================================

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

# Company filter with search
unique_companies = get_unique_companies(df)
if unique_companies:
    st.sidebar.markdown("**🔍 Search Companies**")
    company_search = st.sidebar.text_input("Filter companies", placeholder="e.g., SAP, VW", key="company_search")
    
    filtered_companies = [c for c in unique_companies if company_search.lower() in c.lower()] if company_search else unique_companies
    
    selected_companies = st.sidebar.multiselect(
        f"🏢 Companies ({len(filtered_companies)} available)",
        options=filtered_companies
    ) if filtered_companies else []
else:
    selected_companies = []

# ============================================
# TOPIC FILTER - OPTIMIZED WITH SIMPLE MODE
# ============================================

unique_topics = get_unique_topics(df)
selected_topics = []
expanded_selected = []

if unique_topics:
    st.sidebar.markdown("### 🔥 Topics")
    
    # Performance toggle - default to simple mode for speed
    use_simple_topics = st.sidebar.checkbox(
        "✓ Use simple topic list (faster)", 
        value=True,
        help="Disable topic grouping for better performance. Grouping can be slow with many topics."
    )
    
    st.sidebar.markdown("**🔍 Search Topics**")
    topic_search = st.sidebar.text_input("Filter topics", placeholder="e.g., AI, Workplace", key="topic_search")
    
    if use_simple_topics:
        # ===== SIMPLE MODE (FAST) =====
        filtered_topics = [t for t in unique_topics if topic_search.lower() in t.lower()] if topic_search else unique_topics
        
        selected_topics = st.sidebar.multiselect(
            f"Topics ({len(filtered_topics)} available)",
            options=sorted(filtered_topics)
        )
        expanded_selected = selected_topics
        
        # Show performance note
        st.sidebar.caption("⚡ Simple mode enabled for speed")
        
    else:
        # ===== GROUPED MODE (SLOWER BUT PRETTIER) =====
        with st.sidebar.spinner("Grouping topics..."):
            # Apply search filter before grouping
            if topic_search:
                filtered_for_group = [t for t in unique_topics if topic_search.lower() in t.lower()]
            else:
                filtered_for_group = unique_topics
            
            # Get topic groups
            topic_groups = consolidate_topics(filtered_for_group)
            
            # Create display list
            flat_topics = []
            group_map = {}  # Map display names to actual groups
            
            for group in topic_groups:
                if len(group) == 1:
                    display_name = group[0]
                    flat_topics.append(display_name)
                    group_map[display_name] = group
                else:
                    main_topic = max(group, key=len)
                    display_name = f"{main_topic} (+{len(group)-1} similar)"
                    flat_topics.append(display_name)
                    group_map[display_name] = group
            
            selected_display = st.sidebar.multiselect(
                f"Topic Groups ({len(flat_topics)} available)",
                options=sorted(flat_topics)
            )
            
            # Expand selections for actual filtering
            expanded_selected = []
            for disp in selected_display:
                if disp in group_map:
                    expanded_selected.extend(group_map[disp])
                else:
                    expanded_selected.append(disp)
            
            selected_topics = selected_display
            
            # Show performance note
            st.sidebar.caption("🐢 Grouped mode enabled (may be slower)")

# Apply filters
filtered_df = apply_filters(df, selected_sources, min_score, selected_companies, expanded_selected)

# Now separate into stats (all) and quality (only >40%)
stats_df = filtered_df.copy()
quality_df = filtered_df[filtered_df['final_score'] > QUALITY_THRESHOLD].copy()

# Show quality stats
total_raw = len(stats_df)
total_quality = len(quality_df)
quality_pct = (total_quality / total_raw * 100) if total_raw > 0 else 0
render_quality_badge(quality_pct, total_quality, total_raw)

# ============================================
# METRICS SECTION - UNIFORM SIZE
# ============================================
st.subheader("📈 Overview")

# Create equal width columns
col1, col2, col3, col4 = st.columns(4, gap="medium")

with col1:
    render_metric_card("Total Signals", len(stats_df), "📄", ("#667eea", "#764ba2"))

with col2:
    avg_score = stats_df['final_score'].mean()
    quality_avg = quality_df['final_score'].mean() if len(quality_df) > 0 else 0
    
    # Calculate high impact using 50% threshold
    high_impact_count = len(stats_df[stats_df['final_score'] > HIGH_IMPACT_THRESHOLD])
    
    render_metric_card(
        "Avg Score", 
        f"{avg_score:.1f}%", 
        "⭐", 
        ("#00C2FF", "#0077B6"),
        subtitle=f"Quality: {quality_avg:.1f}% | High Impact: {high_impact_count}"
    )

with col3:
    if 'verified_source_name' in stats_df.columns:
        top_source = stats_df['verified_source_name'].value_counts().index[0] if len(stats_df) > 0 else "N/A"
        display_source = top_source[:15] + "..." if len(top_source) > 15 else top_source
        render_metric_card("Top Source", display_source, "📰", ("#FFD700", "#FFA500"))

with col4:
    time_range = f"Last {days} days" if is_premium else "Last 7 days"
    
    # Calculate German focus with 50% threshold
    german_focus_count = len(stats_df[stats_df['geographic_relevance'] > HIGH_IMPACT_THRESHOLD]) if 'geographic_relevance' in stats_df.columns else 0
    german_focus_pct = (german_focus_count / len(stats_df) * 100) if len(stats_df) > 0 else 0
    
    # Calculate avg freshness
    avg_freshness = stats_df['timeliness'].mean() if 'timeliness' in stats_df.columns else 0
    
    render_metric_card(
        "Time Range", 
        time_range, 
        "📅", 
        ("#FF6B6B", "#C92A2A"),
        subtitle=f"German: {german_focus_pct:.0f}% | Fresh: {avg_freshness:.0f}%"
    )

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
    fig = plot_top_companies(stats_df)
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
# ARTICLE CARDS (Using QUALITY data, last 7 days only)
# ============================================
st.subheader("📰 Top Quality Signals")
st.markdown(f"Showing high-quality signals (score >{QUALITY_THRESHOLD}%)")

if len(quality_df) > 0:
    # Try to get recent articles (last 7 days)
    recent_quality = filter_recent_articles(quality_df, 7)
    
    if len(recent_quality) > 0:
        display_df = recent_quality
        st.caption(f"📅 Last 7 days: {len(recent_quality)} signals")
    else:
        display_df = quality_df
        st.caption(f"⚠️ No signals from last 7 days. Showing best available: {len(quality_df)} signals")
    
    top_articles = display_df.sort_values('final_score', ascending=False).head(20)
    
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