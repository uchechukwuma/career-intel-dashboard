# ============================================
# AI-POWERED INSIGHTS - USING CONFIG COLORS
# ============================================

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import requests
from src.database import init_connection
from src.config import COLORS, HIGH_IMPACT_THRESHOLD

def get_latest_weekly_report():
    """Fetch the latest weekly executive report from MongoDB."""
    try:
        client = init_connection()
        if client is None:
            return None
        
        db_name = None
        if "mongo" in st.secrets:
            db_name = st.secrets["mongo"].get("database", "career_intelligence_v2")
        else:
            import os
            db_name = os.getenv("MONGODB_DATABASE", "career_intelligence_v2")
        
        db = client[db_name]
        collection = db["executive_reports"]
        
        # Get the most recent report
        latest = collection.find_one(
            sort=[("generated_at", -1)]
        )
        
        if latest:
            # Convert ObjectId to string
            latest["_id"] = str(latest["_id"])
            return latest
        else:
            return None
            
    except Exception as e:
        st.warning(f"Could not fetch weekly report: {e}")
        return None

def render_insights_section(is_premium):
    """Render the insights section with REAL data from MongoDB."""
    
    if not is_premium:
        return
    
    st.subheader("🧠 Weekly Intelligence Briefing")
    
    # Fetch the latest report
    report = get_latest_weekly_report()
    
    if report:
        # ===== FIXED: Report metadata with dark text on light background =====
        st.markdown("### 📊 Report Overview")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            week_display = report.get('week_display', 'N/A')
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center;">
                <p style="color: #666; margin: 0; font-size: 0.8rem;">Report Week</p>
                <p style="color: #0A0F1F; font-weight: bold; font-size: 1.4rem; margin: 5px 0;">{week_display}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            generated = report.get('generated_at', 'N/A')[:10]
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center;">
                <p style="color: #666; margin: 0; font-size: 0.8rem;">Generated</p>
                <p style="color: #0A0F1F; font-weight: bold; font-size: 1.4rem; margin: 5px 0;">{generated}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            signals_count = len(report.get('top_signals', []))
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; text-align: center;">
                <p style="color: #666; margin: 0; font-size: 0.8rem;">Top Signals</p>
                <p style="color: #0A0F1F; font-weight: bold; font-size: 1.4rem; margin: 5px 0;">{signals_count}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Executive Summary - Dark text
        if report.get('executive_summary'):
            st.markdown(f"""
            <div style="background-color: #f0f7ff; padding: 20px; border-radius: 10px; margin: 15px 0; border-left: 5px solid {COLORS['primary']};">
                <strong style="color: {COLORS['dark']};">📊 Executive Summary</strong><br>
                <span style="color: {COLORS['dark']};">{report['executive_summary']}</span>
            </div>
            """, unsafe_allow_html=True)
        
        # Top Signals
        if report.get('top_signals'):
            st.markdown("### 🔴 Top Signals This Week")
            
            for signal in report['top_signals'][:5]:
                signal_type = signal.get('signal_type', 'other')
                if signal_type == 'layoff':
                    bg_color = "#FFE5E5"
                    border_color = COLORS['danger']
                elif signal_type == 'hiring':
                    bg_color = "#E5FFE5"
                    border_color = COLORS['success']
                elif signal_type == 'strike':
                    bg_color = "#FFF0E5"
                    border_color = COLORS['warning']
                else:
                    bg_color = "#F0F7FF"
                    border_color = COLORS['primary']
                
                st.markdown(f"""
                <div style="background-color: {bg_color}; padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 5px solid {border_color};">
                    <div style="display: flex; justify-content: space-between;">
                        <strong style="color: {COLORS['dark']};">#{signal.get('rank', '')} {signal.get('title', '')}</strong>
                        <span style="background-color: {border_color}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 0.8rem;">{signal.get('composite_score', '')}</span>
                    </div>
                    <div style="margin: 5px 0; color: #333;">
                        <small>Sources: {', '.join(signal.get('sources', []))} | {signal.get('date', '')}</small>
                    </div>
                    <p style="color: {COLORS['dark']}; margin: 10px 0;"><strong>IMPACT:</strong> {signal.get('impact', '')}</p>
                    <p style="color: {COLORS['dark']}; margin: 10px 0;"><strong>ACTION:</strong> {signal.get('action', '')}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # ===== FIXED: Trend Velocity with dark text on light background =====
        if report.get('trend_velocity'):
            st.markdown("### 📊 Trend Velocity")
            trend = report['trend_velocity']
    
            if trend:
                # Create 3 columns for display
                cols = st.columns(3)
                items = list(trend.items())
        
                for i, (key, value) in enumerate(items):
                    if i < 6:  # Show up to 6 metrics
                        with cols[i % 3]:
                            # Format the key nicely
                            display_key = key.replace('_', ' ').title()
                    
                            # Fix AI casing
                            if 'Ai' in display_key:
                                display_key = display_key.replace('Ai', 'AI')
                            if 'Mom' in display_key:
                                display_key = display_key.replace('Mom', 'MoM')
                    
                            # Display with dark text on light background
                            st.markdown(f"""
                            <div style="background-color: #f0f2f6; padding: 12px; border-radius: 8px; margin-bottom: 8px;">
                                <p style="color: #666; font-size: 0.8rem; margin: 0;">{display_key}</p>
                                <p style="color: #0A0F1F; font-weight: bold; font-size: 1.1rem; margin: 0;">{value}</p>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.info("No trend data available")
        
        # Risk Matrix - Only show if real data
        if report.get('risk_matrix'):
            risk = report['risk_matrix']
            
            has_real_data = False
            if risk.get('critical') and len(risk['critical']) > 0:
                has_real_data = True
            if risk.get('high') and len(risk['high']) > 0:
                has_real_data = True
            if risk.get('hiring') and len(risk['hiring']) > 0:
                has_real_data = True
            
            if has_real_data:
                st.markdown("### ⚠️ Risk Matrix")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if risk.get('critical'):
                        st.markdown(f"""
                        <div style="background-color: {COLORS['danger']}; padding: 10px; border-radius: 5px; color: white; margin-bottom: 10px;">
                            <strong>CRITICAL</strong>
                        </div>
                        """, unsafe_allow_html=True)
                        for item in risk['critical'][:2]:
                            st.markdown(f"""
                            <div style="background-color: #FFE5E5; padding: 10px; border-radius: 5px; margin: 5px 0; border-left: 3px solid {COLORS['danger']};">
                                <strong style="color: {COLORS['dark']};">{item.get('company', '')}</strong><br>
                                <small style="color: #333;">{item.get('topic', '')}</small>
                            </div>
                            """, unsafe_allow_html=True)
                
                with col2:
                    if risk.get('high'):
                        st.markdown(f"""
                        <div style="background-color: {COLORS['warning']}; padding: 10px; border-radius: 5px; color: white; margin-bottom: 10px;">
                            <strong>HIGH</strong>
                        </div>
                        """, unsafe_allow_html=True)
                        for item in risk['high'][:2]:
                            st.markdown(f"""
                            <div style="background-color: #FFF0E5; padding: 10px; border-radius: 5px; margin: 5px 0; border-left: 3px solid {COLORS['warning']};">
                                <strong style="color: {COLORS['dark']};">{item.get('company', '')}</strong><br>
                                <small style="color: #333;">{item.get('topic', '')}</small>
                            </div>
                            """, unsafe_allow_html=True)
                
                with col3:
                    if risk.get('hiring'):
                        st.markdown(f"""
                        <div style="background-color: {COLORS['success']}; padding: 10px; border-radius: 5px; color: white; margin-bottom: 10px;">
                            <strong>HIRING</strong>
                        </div>
                        """, unsafe_allow_html=True)
                        for item in risk['hiring'][:2]:
                            st.markdown(f"""
                            <div style="background-color: #E5FFE5; padding: 10px; border-radius: 5px; margin: 5px 0; border-left: 3px solid {COLORS['success']};">
                                <strong style="color: {COLORS['dark']};">{item.get('company', '')}</strong><br>
                                <small style="color: #333;">{item.get('role', '')}</small>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.info("Risk matrix being calibrated...")
        
        # Forecast - Dark text
        if report.get('forecast'):
            st.markdown("### 🔮 Next Week Forecast")
            for item in report['forecast']:
                st.markdown(f"""
                <div style="background-color: #F0F0F0; padding: 12px; border-radius: 8px; margin: 8px 0;">
                    <strong style="color: {COLORS['dark']};">📅 {item.get('date', '')}:</strong>
                    <span style="color: #333;"> {item.get('event', '')}</span>
                    {f'<br><small style="color: #666;">{item.get("detail", "")}</small>' if item.get('detail') else ''}
                </div>
                """, unsafe_allow_html=True)
        
        # PDF Download Button
        st.markdown("### 📥 Download Full Report")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📄 Download PDF Report", use_container_width=True):
                st.info("PDF generation in progress. Check back later.")
        
        with col2:
            if st.button("📊 View Raw Data", use_container_width=True):
                st.json(report)
    
    else:
        # No report available yet
        st.info("""
        💡 **Weekly intelligence report coming soon!**
        
        Our AI is analyzing this week's signals. The first report will be available within 24 hours.
        
        In the meantime, explore the live dashboard below.
        """)
        
        # Show placeholder with better visibility
        st.markdown(f"""
        <div style="background-color: #F0F7FF; padding: 20px; border-radius: 10px; border-left: 5px solid {COLORS['primary']}; margin: 15px 0;">
            <h4 style="color: {COLORS['dark']};">Sample Insights (Demo Mode)</h4>
            <ul style="color: {COLORS['dark']}; list-style-type: none; padding-left: 0;">
                <li style="margin-bottom: 10px; color: {COLORS['dark']};">🔴 <strong>Layoffs accelerating:</strong> Meta planning 16,000 cuts, VW restructuring 50,000 by 2030</li>
                <li style="margin-bottom: 10px; color: {COLORS['dark']};">🟠 <strong>Labor unrest:</strong> Lufthansa pilots strike disrupting hundreds of flights</li>
                <li style="margin-bottom: 10px; color: {COLORS['dark']};">🔵 <strong>AI transformation:</strong> SAP restructuring around AI, Oracle cuts due to AI pressure</li>
                <li style="margin-bottom: 10px; color: {COLORS['dark']};">🟢 <strong>Watch next week:</strong> More airline strikes, continued tech sector volatility</li>
            </ul>
            <p style="color: #666;">⚡ Full AI insights coming soon with weekly reports</p>
        </div>
        """, unsafe_allow_html=True)