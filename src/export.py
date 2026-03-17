# ============================================
# CLEAN CSV EXPORT FUNCTIONS
# ============================================

import streamlit as st
import pandas as pd
from datetime import datetime
from src.clean import get_clean_company_string, get_clean_topics_string


def render_export_section(is_premium, filtered_df, quality_data):
    """Render CSV export section with clean data."""
    if not is_premium:
        st.info("🔒 CSV export is a premium feature. [Subscribe](https://careerintelligence.carrd.co) for access to clean, analysis-ready data.")
        return
    
    st.subheader("📥 Export Data")
    
    # Prepare clean export dataframe from QUALITY data only
    export_df = quality_data.copy()
    
    # Add clean company and topic strings
    export_df['Companies'] = export_df.apply(get_clean_company_string, axis=1)
    export_df['Topics'] = export_df.apply(get_clean_topics_string, axis=1)
    
    # Build final export dataframe with user-friendly columns
    final_export = pd.DataFrame()
    final_export['Headline'] = export_df['headline']
    final_export['Source'] = export_df['verified_source_name']
    final_export['Date'] = export_df['published_at'].dt.strftime('%Y-%m-%d') if 'published_at' in export_df.columns else ''
    final_export['Relevance Score (%)'] = export_df['final_score'].round(1)
    final_export['Companies'] = export_df['Companies']
    final_export['Topics'] = export_df['Topics']
    
    # Remove any rows with empty headlines
    final_export = final_export[final_export['Headline'].notna() & (final_export['Headline'] != '')]
    
    # Show preview of what will be exported
    with st.expander("📋 Preview export data (first 5 rows)"):
        st.dataframe(final_export.head(5), use_container_width=True)
    
    # Export button with clean filename
    csv = final_export.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Clean CSV (Premium)",
        data=csv,
        file_name=f"career_intelligence_export_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True,
        help="Download a clean CSV with only the most relevant columns for analysis"
    )
    
    # Add option to include technical columns for power users
    with st.expander("⚙️ Advanced Export Options"):
        st.markdown("Include technical columns for deeper analysis (for researchers/data analysts)")
        
        if st.checkbox("Include technical columns (scores, IDs, etc.)"):
            tech_export = quality_data.copy()
            
            # Format dates
            if 'published_at' in tech_export.columns:
                tech_export['published_at'] = tech_export['published_at'].dt.strftime('%Y-%m-%d %H:%M')
            
            # Clean companies and topics for technical export too
            tech_export['companies_clean'] = tech_export.apply(get_clean_company_string, axis=1)
            tech_export['topics_clean'] = tech_export.apply(get_clean_topics_string, axis=1)
            
            # Select technical columns
            tech_cols = ['headline', 'verified_source_name', 'published_at', 'final_score', 
                        'signal_strength', 'career_impact', 'company_significance', 
                        'timeliness', 'geographic_relevance', 'career_actionability',
                        'companies_clean', 'topics_clean']
            
            tech_export = tech_export[[c for c in tech_cols if c in tech_export.columns]]
            
            tech_csv = tech_export.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Download Technical CSV (with scores)",
                data=tech_csv,
                file_name=f"career_intelligence_technical_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )