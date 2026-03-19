# ============================================
# DATABASE CONNECTION AND DATA LOADING - FIXED
# ============================================

import streamlit as st
import pymongo
import pandas as pd
from datetime import datetime, timedelta
import certifi
from pymongo.server_api import ServerApi
from src.clean import clean_entity_list, clean_entity_name
import time

@st.cache_resource
def init_connection():
    """Connect to MongoDB Atlas using secrets."""
    try:
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
        
        # Add timeout to prevent hanging
        client = pymongo.MongoClient(
            connection_string,
            tlsCAFile=certifi.where(),
            server_api=ServerApi('1'),
            serverSelectionTimeoutMS=5000,  # Reduced from 30000 to 5 seconds
            connectTimeoutMS=5000,           # 5 second connection timeout
            socketTimeoutMS=30000,
            retryWrites=True,
            retryReads=True
        )
        
        # Test connection with short timeout
        client.admin.command('ping')
        
        return client
        
    except pymongo.errors.ServerSelectionTimeoutError:
        st.error("❌ MongoDB connection timeout. Check your network and credentials.")
        return None
    except Exception as e:
        st.error(f"❌ Connection failed: {e}")
        return None


@st.cache_data(ttl=3600, show_spinner=False)  # We'll handle spinner manually
def load_data(days_back=30, is_premium=False):
    """Load articles from last N days with entity cleaning."""
    client = init_connection()
    if client is None:
        return pd.DataFrame()
    
    # Create a progress placeholder
    progress_bar = st.progress(0, text="Connecting to database...")
    
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
        
        progress_bar.progress(20, text="Building query...")
        
        # Premium users get more data
        if is_premium:
            cutoff = datetime.utcnow() - timedelta(days=days_back)
            limit = 2000
            progress_text = f"Loading {days_back} days of premium data..."
        else:
            cutoff = datetime.utcnow() - timedelta(days=7)
            limit = 200
            progress_text = "Loading 7 days of free preview..."
        
        progress_bar.progress(40, text=progress_text)
        
        # Query with timeout
        cursor = collection.find({
            "is_processed": True,
            "published_at": {"$gte": cutoff}
        }).sort("published_at", -1).limit(limit)
        
        progress_bar.progress(60, text="Fetching articles...")
        
        # Convert to list with timeout
        data = list(cursor)
        if not data:
            progress_bar.empty()
            return pd.DataFrame()
        
        progress_bar.progress(80, text="Processing articles...")
        
        # Convert to DataFrame and extract fields
        rows = []
        total = len(data)
        for idx, article in enumerate(data):
            # Update progress every 10%
            if idx % (total // 10 + 1) == 0:
                progress_bar.progress(80 + int(20 * idx / total), 
                                     text=f"Processing {idx}/{total} articles...")
            
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
            
            # When creating the row dictionary, ensure scores are floats:
            row = {
                'id': str(article['_id']),
                'headline': article.get('headline', ''),
                'verified_source_name': article.get('verified_source_name', 'Unknown'),
                'source_id': article.get('source_id', 'unknown'),
                'published_at': article.get('published_at'),
                'final_score': float(scores.get('final_score', 0)) * 100,
                'signal_strength': float(scores.get('signal_strength_score', 0)) * 100,
                'career_impact': float(scores.get('career_impact_score', 0)) * 100,
                'company_significance': float(scores.get('company_significance_score', 0)) * 100,
                'timeliness': float(scores.get('timeliness_score', 0)) * 100,
                'geographic_relevance': float(scores.get('geographic_relevance_score', 0)) * 100,
                'career_actionability': float(scores.get('career_actionability_score', 0)) * 100,
                'extracted_company': extracted_company,
                'extracted_companies': extracted_companies,
                'extracted_topics': extracted_topics,
            }
            rows.append(row)
        
        progress_bar.progress(100, text="Finalizing...")
        
        df = pd.DataFrame(rows)
        
        # Convert date
        if 'published_at' in df.columns:
            df['published_at'] = pd.to_datetime(df['published_at'])
        
        # Clear progress bar
        progress_bar.empty()
        
        return df
        
    except pymongo.errors.ServerSelectionTimeoutError:
        progress_bar.empty()
        st.error("❌ MongoDB query timeout. Please try again.")
        return pd.DataFrame()
    except Exception as e:
        progress_bar.empty()
        st.error(f"❌ Error loading data: {e}")
        return pd.DataFrame()