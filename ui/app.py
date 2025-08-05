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
from src.polling_service import start_polling_service, is_polling_service_running, get_polling_service

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


@st.cache_resource
def get_database_manager():
    """Get cached database manager instance"""
    return DatabaseManager()


async def initialize_database():
    """Initialize database if not already done"""
    if not st.session_state.get('db_initialized', False):
        try:
            db_manager = get_database_manager()
            await db_manager.initialize()
            
            # Check if database needs seeding from config
            organizations = await db_manager.get_organizations()
            if not organizations:
                st.info("Initializing database from configuration...")
                await db_manager.seed_from_config()
                st.success("Database initialized successfully!")
            
            st.session_state.db_initialized = True
            return True
        except Exception as e:
            st.error(f"Failed to initialize database: {e}")
            return False
    return True


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
    if 'polling_service_started' not in st.session_state:
        st.session_state.polling_service_started = False


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
        
        # Check database status
        if st.session_state.get('db_initialized', False):
            st.success("✅ Database Initialized")
            
            # Show database statistics
            try:
                db_manager = get_database_manager()
                if asyncio.get_event_loop().is_running():
                    # We're in an async context, handle carefully
                    with st.spinner("Loading database stats..."):
                        # Use st.cache or other method for async operations in Streamlit
                        pass
                else:
                    # Synchronous context
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        orgs = loop.run_until_complete(db_manager.get_organizations())
                        projects = loop.run_until_complete(db_manager.get_projects())
                        repositories = loop.run_until_complete(db_manager.get_repositories())
                        
                        st.info(f"📊 {len(orgs)} Orgs, {len(projects)} Projects, {len(repositories)} Repos")
                    finally:
                        loop.close()
                        
            except Exception as e:
                st.warning(f"⚠️ Database stats unavailable: {str(e)[:50]}...")
        else:
            st.error("❌ Database Not Initialized")
            
        # Check projects from config or database
        if hasattr(config, 'projects') and config.projects:
            st.success(f"✅ {len(config.projects)} Projects (Config)")
        else:
            st.error("❌ No Projects")
        
        # Database status
        if hasattr(config, 'database') and config.database.enabled:
            st.success("✅ Database Enabled")
        else:
            st.warning("⚠️ Database Disabled")
        
        # Polling service status
        if is_polling_service_running():
            st.success("✅ Background Processing Service")
            service = get_polling_service()
            status = service.get_status()
            if status['processing_count'] > 0:
                st.info(f"🔄 Processing {status['processing_count']} request(s)")
        else:
            st.error("❌ Background Processing Service")
            
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
    
    # Initialize database on startup
    if not st.session_state.get('db_initialized', False):
        with st.spinner("Initializing database..."):
            try:
                # Run database initialization
                if asyncio.get_event_loop().is_running():
                    # We're already in an async context
                    success = asyncio.create_task(initialize_database())
                else:
                    # Create new event loop
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        success = loop.run_until_complete(initialize_database())
                    finally:
                        loop.close()
                
                if not success:
                    st.error("Failed to initialize database. Some features may not work correctly.")
            except Exception as e:
                st.error(f"Database initialization error: {e}")
    
    # Start polling service if database is initialized and service not already started
    if st.session_state.get('db_initialized', False) and not st.session_state.get('polling_service_started', False):
        try:
            with st.spinner("Starting background processing service..."):
                start_polling_service()
                st.session_state.polling_service_started = True
                st.success("🚀 Background processing service started")
        except Exception as e:
            st.error(f"Failed to start background processing service: {e}")
    
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