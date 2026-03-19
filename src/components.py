# ============================================
# UI COMPONENTS - FIXED CLOUD VISIBILITY
# ============================================

import streamlit as st
from src.config import COLORS, BADGE_THRESHOLDS
from src.clean import get_clean_company_string, get_clean_topics_string

def render_metric_card(title, value, icon, color_gradient, subtitle=None):
    """Render a uniform metric card with taller height."""
    subtitle_html = f'<p style="color: rgba(255,255,255,0.9); margin: 8px 0 0 0; font-size: 0.8rem; line-height: 1.3;">{subtitle}</p>' if subtitle else ''
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {color_gradient[0]} 0%, {color_gradient[1]} 100%);
        padding: 15px 10px;
        border-radius: 12px;
        text-align: center;
        height: 180px;
        width: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-sizing: border-box;
        margin: 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    ">
        <div style="flex-grow: 1; display: flex; flex-direction: column; justify-content: center;">
            <h3 style="color: white; margin: 0 0 5px 0; font-size: 1.5rem;">{icon}</h3>
            <h2 style="color: #0A0F1F; margin: 0 0 5px 0; font-size: 1.8rem; font-weight: bold;">{value}</h2>
            <p style="color: white; margin: 0; font-weight: 500; font-size: 1rem;">{title}</p>
        </div>
        {subtitle_html}
    </div>
    """, unsafe_allow_html=True)

def render_quality_badge(quality_pct, total_quality, total_raw):
    """Render quality indicator in sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"""
    <div style="background-color: #4CAF50; color: white; padding: 10px; border-radius: 5px; text-align: center;">
        <strong>📊 SIGNAL QUALITY</strong><br>
        Showing {total_quality} high-quality signals<br>
        ({quality_pct:.1f}% of total)
    </div>
    """, unsafe_allow_html=True)

def render_article_card(article):
    """Render a single article card with dark text."""
    companies = get_clean_company_string(article)
    topics = get_clean_topics_string(article)
    
    score = article['final_score']
    if score >= BADGE_THRESHOLDS['hot']:
        badge_color = COLORS['success']
        badge_text = "🔥 HOT"
    elif score >= BADGE_THRESHOLDS['trending']:
        badge_color = COLORS['warning']
        badge_text = "📈 TRENDING"
    else:
        badge_color = COLORS['primary']
        badge_text = "📊 SIGNAL"
    
    date_str = article['published_at'].strftime('%d.%m.%Y') if article['published_at'] else ''
    source = article['verified_source_name'][:20] + ('...' if len(article['verified_source_name']) > 20 else '')
    
    st.markdown(f"""
    <div style="background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 15px; border-left: 5px solid {badge_color};">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="background-color: {badge_color}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 0.7rem; font-weight: bold;">{badge_text}</span>
            <span style="color: #666; font-size: 0.8rem;">{date_str}</span>
        </div>
        <p style="font-weight: bold; margin-bottom: 8px; color: #0A0F1F;">{article['headline'][:80]}{'...' if len(article['headline']) > 80 else ''}</p>
        <div style="display: flex; gap: 10px; margin-bottom: 5px; flex-wrap: wrap;">
            <span style="background-color: #f0f2f6; padding: 2px 8px; border-radius: 12px; font-size: 0.7rem; color: #0A0F1F;">📰 {source}</span>
            <span style="background-color: #f0f2f6; padding: 2px 8px; border-radius: 12px; font-size: 0.7rem; color: #0A0F1F;">⭐ {score:.0f}%</span>
        </div>
        {f'<div style="margin-top: 8px;"><span style="color: #333; font-size: 0.8rem;">🏢 {companies[:50]}{"..." if len(companies) > 50 else ""}</span></div>' if companies else ''}
    </div>
    """, unsafe_allow_html=True)

def render_professional_header():
    """Render the professional header bar."""
    st.markdown("""
    <div style="background: linear-gradient(90deg, #0A0F1F 0%, #1E2A4A 100%); padding: 15px; border-radius: 10px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; color: white; font-size: 0.9rem; flex-wrap: wrap;">
            <div>📊 <strong>1,700+</strong> articles processed</div>
            <div>📰 <strong>23</strong> German sources</div>
            <div>⚡ <strong>Daily</strong> updates</div>
            <div>🎯 B2B Intelligence</div>
        </div>
    </div>
    """, unsafe_allow_html=True)