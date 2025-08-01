"""
Main Streamlit UI for Azure DevOps Git Repository Analytics Tool
"""

import streamlit as st
import sys
from pathlib import Path
import asyncio
import logging
from datetime import datetime
import json
import os

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from streamlit_option_menu import option_menu

# Import our modules
from src.config import get_config, reload_config
from src.analytics_engine import AnalyticsEngine
from src.database import DatabaseManager

# Import UI pages
from pages import config_page, data_collection_page, analytics_page, database_page


def setup_page_config():
    """Setup Streamlit page configuration"""
    st.set_page_config(
        page_title="Git Analytics Tool",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )


def setup_session_state():
    """Initialize session state variables"""
    if 'config_saved' not in st.session_state:
        st.session_state.config_saved = False
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = {}
    if 'selected_repositories' not in st.session_state:
        st.session_state.selected_repositories = []
    if 'db_initialized' not in st.session_state:
        st.session_state.db_initialized = False


def main_navigation():
    """Main navigation menu"""
    with st.sidebar:
        st.title("📊 Git Analytics")
        st.markdown("---")
        
        selected = option_menu(
            menu_title=None,
            options=["🔧 Configuration", "📊 Data Collection", "📈 Analytics", "🗄️ Database"],
            icons=["gear", "download", "bar-chart", "database"],
            menu_icon="cast",
            default_index=0,
            orientation="vertical",
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "orange", "font-size": "18px"},
                "nav-link": {
                    "font-size": "16px",
                    "text-align": "left",
                    "margin": "0px",
                    "--hover-color": "#eee",
                },
                "nav-link-selected": {"background-color": "#02ab21"},
            }
        )
        
        # Show connection status
        st.markdown("---")
        show_connection_status()
        
        return selected


def show_connection_status():
    """Show current configuration status"""
    st.subheader("Status")
    
    try:
        config = get_config()
        
        # Check Azure DevOps configuration
        if hasattr(config, 'azure_pat') and config.azure_pat:
            st.success("✅ Azure DevOps Token")
        else:
            st.error("❌ Azure DevOps Token")
        
        if hasattr(config, 'azure_org_url') and config.azure_org_url:
            st.success("✅ Organization URL")
        else:
            st.error("❌ Organization URL")
        
        if hasattr(config, 'projects') and config.projects:
            st.success(f"✅ {len(config.projects)} Projects")
        else:
            st.error("❌ No Projects")
        
        # Database status
        if hasattr(config, 'database') and config.database.enabled:
            st.success("✅ Database Enabled")
        else:
            st.warning("⚠️ Database Disabled")
            
    except Exception as e:
        st.error(f"❌ Configuration Error: {str(e)}")


def show_header():
    """Show application header"""
    st.title("🔍 Azure DevOps Git Repository Analytics")
    st.markdown(
        """
        **Comprehensive analytics tool for Azure DevOps Git repositories**
        
        This tool provides detailed insights into your development processes, including:
        - Commit patterns and trends
        - Author productivity and collaboration
        - Code quality metrics
        - Security and performance indicators
        """
    )
    st.markdown("---")


def main():
    """Main application entry point"""
    setup_page_config()
    setup_session_state()
    
    # Navigation
    selected_page = main_navigation()
    
    # Main content area
    show_header()
    
    # Route to selected page
    if selected_page == "🔧 Configuration":
        config_page.show()
    elif selected_page == "📊 Data Collection":
        data_collection_page.show()
    elif selected_page == "📈 Analytics":
        analytics_page.show()
    elif selected_page == "🗄️ Database":
        database_page.show()


if __name__ == "__main__":
    main() 