import streamlit as st
import pymongo
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import certifi
from collections import Counter
import requests


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

# MongoDB connection

@st.cache_resource
def init_connection():
    """Connect to MongoDB Atlas using secrets."""
    try:
        import certifi
        from pymongo.server_api import ServerApi
        
        if "mongo" in st.secrets:
            connection_string = st.secrets["mongo"]["url"]
            db_name = st.secrets["mongo"]["database"]
            collection_name = st.secrets["mongo"]["collection"]
        else:
            import os
            from dotenv import load_dotenv
            load_dotenv()
            connection_string = os.getenv("MONGODB_URI")
            db_name = os.getenv("MONGODB_DATABASE", "career_intelligence_v2")
            collection_name = os.getenv("MONGODB_COLLECTION", "career_articles")
            
            if not connection_string:
                st.error("MongoDB connection string not found")
                return None
        
        # SIMPLE connection - let PyMongo handle SSL automatically
        client = pymongo.MongoClient(
            connection_string,
            tlsCAFile=certifi.where(),  # Use this instead of context
            server_api=ServerApi('1'),
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000,
            socketTimeoutMS=45000,
            retryWrites=True,
            retryReads=True
        )
        
        # Test connection
        client.admin.command('ping')
        
        # Show success
        db = client[db_name]
        collection = db[collection_name]
        count = collection.count_documents({})
        st.success(f"✅ Connected to MongoDB! Found {count} articles")
        
        return client
        
    except Exception as e:
        st.error(f"❌ Connection failed: {e}")
        import traceback
        st.error(f"Full error: {traceback.format_exc()}")
        return None

# Access control
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
                st.markdown("[Get access →](https://careerintelligence.carrd.co)")
    
    return st.session_state.premium

# ============================================
# ENTITY CLEANING FUNCTIONS
# ============================================

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
    
    # Common acronyms that should stay uppercase
    acronyms = [
        # German labor market specific
        'AI', 'HR', 'ML', 'CEO', 'CTO', 'CFO', 'COO', 'CIO', 'CTO',
        'API', 'SaaS', 'IAB', 'BMAS', 'DGB', 'FAZ', 'MDR', 'RND', 'DPA',
        'EU', 'USA', 'UK', 'IT', 'KI', 'AG', 'GMBH', 'SE', 'PLC',
        
        # Companies
        'SAP', 'IBM', 'BMW', 'VW', 'DB', 'DHL', 'Lufthansa', 'Siemens',
        'BASF', 'Bayer', 'Mercedes', 'Audi', 'Porsche', 'Adidas', 'Puma',
        'Deutsche Telekom', 'Telekom', 'Vodafone', 'O2', 'E.ON', 'RWE',
        
        # Tech
        'AWS', 'GCP', 'Azure', 'OpenAI', 'Anthropic', 'Meta', 'Google',
        'Microsoft', 'Apple', 'Amazon', 'Netflix', 'Oracle', 'Salesforce',
        'Adobe', 'Intel', 'Nvidia', 'AMD', 'TSMC', 'Samsung',
        
        # Media
        'ARD', 'ZDF', 'RTL', 'ProSieben', 'Sat.1', 'Axel Springer',
        
        # Organizations
        'IG Metall', 'Verdi', 'IG BCE', 'DGB', 'BDA', 'DIHK', 'ZDH',
        'Ifo', 'IAB', 'DIW', 'RWI', 'ZEW', 'IW', 'KOF'
    ]
    
    # Check if cleaned version matches any acronym
    # Try exact match with cleaned
    if cleaned in acronyms:
        return cleaned
    
    # Try uppercase version without spaces
    cleaned_upper = cleaned.upper().replace(' ', '')
    for acro in acronyms:
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

# ============================================
# DATA LOADING WITH CLEANING
# ============================================

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data(days_back=30, is_premium=False):
    """Load articles from last N days with entity cleaning."""
    client = init_connection()
    if client is None:
        return pd.DataFrame()
    
    try:
        # Get database info
        db_name = None
        collection_name = None
        
        if "mongo" in st.secrets:
            db_name = st.secrets["mongo"].get("database", "career_intelligence_v2")
            collection_name = st.secrets["mongo"].get("collection", "career_articles")
        else:
            import os
            db_name = os.getenv("MONGODB_DATABASE", "career_intelligence_v2")
            collection_name = os.getenv("MONGODB_COLLECTION", "career_articles")
        
        db = client[db_name]
        collection = db[collection_name]
        
        # Premium users get more data
        if is_premium:
            cutoff = datetime.utcnow() - timedelta(days=days_back)
            limit = 2000
        else:
            cutoff = datetime.utcnow() - timedelta(days=7)  # Free users: 7 days only
            limit = 200
        
        # Query
        cursor = collection.find({
            "is_processed": True,
            "published_at": {"$gte": cutoff}
        }).sort("published_at", -1).limit(limit)
        
        data = list(cursor)
        if not data:
            return pd.DataFrame()
        
        # Convert to DataFrame and extract fields
        rows = []
        for article in data:
            scores = article.get('scores', {})
            
            # Get extracted companies and clean them
            extracted_companies = article.get('extracted_companies', [])
            if isinstance(extracted_companies, list):
                extracted_companies = clean_entity_list(extracted_companies)
            
            # Get extracted topics and clean them
            extracted_topics = article.get('extracted_topics', [])
            if isinstance(extracted_topics, list):
                extracted_topics = clean_entity_list(extracted_topics)
            
            # Clean single extracted company if present
            extracted_company = article.get('extracted_company')
            if extracted_company and isinstance(extracted_company, str):
                extracted_company = clean_entity_name(extracted_company)
            
            row = {
                'id': str(article['_id']),
                'headline': article.get('headline', ''),
                'verified_source_name': article.get('verified_source_name', 'Unknown'),
                'source_id': article.get('source_id', 'unknown'),
                'published_at': article.get('published_at'),
                'final_score': scores.get('final_score', 0) * 100,  # Convert to percentage
                'signal_strength': scores.get('signal_strength_score', 0) * 100,
                'career_impact': scores.get('career_impact_score', 0) * 100,
                'company_significance': scores.get('company_significance_score', 0) * 100,
                'timeliness': scores.get('timeliness_score', 0) * 100,
                'geographic_relevance': scores.get('geographic_relevance_score', 0) * 100,
                'career_actionability': scores.get('career_actionability_score', 0) * 100,
                'extracted_company': extracted_company,
                'extracted_companies': extracted_companies,
                'extracted_topics': extracted_topics,
            }
            rows.append(row)
        
        df = pd.DataFrame(rows)
        
        # Convert date
        if 'published_at' in df.columns:
            df['published_at'] = pd.to_datetime(df['published_at'])
        
        return df
        
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        return pd.DataFrame()

# Check premium access
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
            "[Subscribe for full access](https://careerintelligence.carrd.co) 📈"
        )

if df.empty:
    st.warning("⚠️ No data found. Check your MongoDB connection.")
    st.stop()

# ============================================
# ADDITIONAL CLEANING FOR DISPLAY
# ============================================

# Ensure all entity fields are cleaned (re-run cleaning just to be safe)
if 'extracted_companies' in df.columns:
    df['extracted_companies'] = df['extracted_companies'].apply(
        lambda x: clean_entity_list(x) if isinstance(x, list) else x
    )

if 'extracted_topics' in df.columns:
    df['extracted_topics'] = df['extracted_topics'].apply(
        lambda x: clean_entity_list(x) if isinstance(x, list) else x
    )

if 'extracted_company' in df.columns:
    df['extracted_company'] = df['extracted_company'].apply(
        lambda x: clean_entity_name(x) if isinstance(x, str) else x
    )

# Sidebar filters
st.sidebar.header("🔍 Filters")

# Source filter - using verified_source_name
sources = df['verified_source_name'].dropna().unique().tolist()
selected_sources = st.sidebar.multiselect(
    "📰 Sources",
    options=sources,
    default=sources[:5] if len(sources) > 5 and is_premium else sources[:3]
)

# Min score filter
min_score = st.sidebar.slider("🎯 Min relevance score (%)", 0, 100, 0)

# Company filter
all_companies = []
for comps in df['extracted_companies'].dropna():
    if isinstance(comps, list):
        all_companies.extend(comps)
# Add single company field
single_companies = df['extracted_company'].dropna().tolist()
all_companies.extend(single_companies)

if all_companies:
    # Count frequencies and sort
    company_counter = Counter(all_companies)
    unique_companies = sorted([c for c in set(all_companies) if c], 
                              key=lambda x: (-company_counter[x], x))
    
    selected_companies = st.sidebar.multiselect(
        "🏢 Companies",
        options=unique_companies
    )
else:
    selected_companies = []

# Topic filter
all_topics = []
for topics in df['extracted_topics'].dropna():
    if isinstance(topics, list):
        all_topics.extend(topics)

if all_topics:
    topic_counter = Counter(all_topics)
    unique_topics = sorted([t for t in set(all_topics) if t],
                          key=lambda x: (-topic_counter[x], x))
    
    selected_topics = st.sidebar.multiselect(
        "🔥 Topics",
        options=unique_topics
    )
else:
    selected_topics = []

# Apply filters
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

# Metrics row
st.subheader("📈 Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "📄 Total Articles",
        len(filtered_df),
        help="Number of articles matching your filters"
    )
with col2:
    avg_score = filtered_df['final_score'].mean()
    st.metric(
        "⭐ Avg Score",
        f"{avg_score:.1f}%",
        help="Average relevance score"
    )
with col3:
    if 'verified_source_name' in filtered_df.columns:
        top_source = filtered_df['verified_source_name'].value_counts().index[0] if len(filtered_df) > 0 else "N/A"
        st.metric(
            "📰 Top Source",
            top_source,
            help="Most active news source"
        )
with col4:
    if is_premium:
        st.metric(
            "📅 Time Range",
            f"Last {days} days",
            help="Premium: Full access"
        )
    else:
        st.metric(
            "📅 Time Range",
            "Last 7 days",
            help="Free preview"
        )

# Charts
st.subheader("📊 Trends")

# Row 1
col1, col2 = st.columns(2)

with col1:
    # Top companies
    if 'extracted_companies' in filtered_df.columns:
        st.markdown("**🔥 Top Companies**")
        company_counts = {}
        
        # Count from extracted_companies
        for comps in filtered_df['extracted_companies'].dropna():
            if isinstance(comps, list):
                for comp in comps:
                    if comp and isinstance(comp, str):
                        company_counts[comp] = company_counts.get(comp, 0) + 1
        
        # Count from extracted_company
        for comp in filtered_df['extracted_company'].dropna():
            if comp and isinstance(comp, str):
                company_counts[comp] = company_counts.get(comp, 0) + 1
        
        if company_counts:
            comp_df = pd.DataFrame(
                [(k, v) for k, v in company_counts.items() if k],
                columns=['Company', 'Mentions']
            ).sort_values('Mentions', ascending=False).head(10)
            
            if not comp_df.empty:
                fig = px.bar(
                    comp_df,
                    x='Company',
                    y='Mentions',
                    title='Top Companies by Mentions',
                    color='Mentions',
                    color_continuous_scale='blues'
                )
                fig.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No company data available")

with col2:
    # Score distribution
    st.markdown("**📊 Score Distribution**")
    fig = px.histogram(
        filtered_df,
        x='final_score',
        nbins=20,
        title='Article Score Distribution',
        color_discrete_sequence=['#00C2FF']
    )
    fig.update_layout(xaxis_title="Score (%)", yaxis_title="Number of Articles")
    st.plotly_chart(fig, use_container_width=True)

# Row 2
col1, col2 = st.columns(2)

with col1:
    # Topics
    if 'extracted_topics' in filtered_df.columns:
        st.markdown("**🔥 Hot Topics**")
        topic_counts = {}
        for topics in filtered_df['extracted_topics'].dropna():
            if isinstance(topics, list):
                for topic in topics:
                    if topic and isinstance(topic, str):
                        # Double-check cleaning on display (safety)
                        clean_topic = clean_entity_name(topic)
                        topic_counts[clean_topic] = topic_counts.get(clean_topic, 0) + 1
        
        if topic_counts:
            topic_df = pd.DataFrame(
                [(k, v) for k, v in topic_counts.items()],
                columns=['Topic', 'Mentions']
            ).sort_values('Mentions', ascending=False).head(10)
            
            fig = px.bar(
                topic_df,
                y='Topic',
                x='Mentions',
                orientation='h',
                title='Hot Topics',
                color='Mentions',
                color_continuous_scale='greens'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No topic data available")

with col2:
    # Sources
    st.markdown("**📰 Top Sources**")
    source_counts = filtered_df['verified_source_name'].value_counts().head(8)
    
    if not source_counts.empty:
        fig = px.pie(
            values=source_counts.values,
            names=source_counts.index,
            title='Article Distribution by Source'
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No source data available")

# Data table
st.subheader("📋 Signals")
st.markdown(f"Showing {len(filtered_df)} articles")

# Prepare display columns
display_df = filtered_df.copy()

# Clean company strings for display one more time
def get_clean_company_string(row):
    companies = []
    if row['extracted_company'] and isinstance(row['extracted_company'], str):
        companies.append(row['extracted_company'])
    if isinstance(row['extracted_companies'], list):
        companies.extend(row['extracted_companies'])
    # Remove duplicates
    companies = list(dict.fromkeys(companies))
    return ', '.join(companies) if companies else ''

display_df['companies'] = display_df.apply(get_clean_company_string, axis=1)

# Select columns for display
display_cols = ['headline', 'verified_source_name', 'companies', 'final_score', 'published_at']
display_cols = [col for col in display_cols if col in display_df.columns]

display_df = display_df.sort_values('final_score', ascending=False)[display_cols].head(50)

# Rename columns for display
display_df.columns = ['Headline', 'Source', 'Companies', 'Score', 'Date']

# Format date
if 'Date' in display_df.columns:
    display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d')

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Score": st.column_config.NumberColumn(format="%.1f%%")
    }
)

# Export
csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download CSV",
    data=csv,
    file_name=f"career_signals_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv",
    use_container_width=True
)

# Premium upsell for free users
if not is_premium:
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info(
            "🚀 **Upgrade to Premium**\n\n"
            "• 📊 6 months of historical data\n"
            "• 📈 Advanced filters\n"
            "• 📉 Export unlimited data\n"
            "• 🔔 Daily email alerts\n\n"
            "[👉 Subscribe for €0/month](https://careerintelligence.carrd.co)"
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