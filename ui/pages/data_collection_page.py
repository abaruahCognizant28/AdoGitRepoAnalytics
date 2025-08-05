"""
Data collection page for running analytics tasks with request tracking
"""

import streamlit as st
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.config import get_config
from src.database import DatabaseManager
from src.polling_service import is_polling_service_running


def show():
    """Show data collection page"""
    st.header("📊 Data Collection")
    
    # Check if configuration is valid
    try:
        config = get_config()
        if not validate_configuration(config):
            return
    except Exception as e:
        st.error(f"❌ Configuration error: {str(e)}")
        st.info("Please configure the tool in the Configuration page first.")
        return
    
    # Main interface - toggle between new request and existing requests
    tab1, tab2 = st.tabs(["🆕 New Request", "📋 Existing Requests"])
    
    with tab1:
        show_new_request_interface()
    
    with tab2:
        show_existing_requests_interface()


def validate_configuration(config) -> bool:
    """Validate that configuration is complete"""
    errors = []
    
    if not getattr(config, 'azure_pat', None):
        errors.append("Azure DevOps Personal Access Token not configured")
    
    if not getattr(config, 'azure_org_url', None):
        errors.append("Azure DevOps Organization URL not configured")
    
    if not getattr(config, 'organization', None):
        errors.append("Organization name not configured")
    
    if not st.session_state.get('db_initialized', False):
        errors.append("Database not initialized")
    
    if errors:
        st.error("❌ Configuration incomplete:")
        for error in errors:
            st.write(f"• {error}")
        st.info("Please complete the configuration in the Configuration page.")
        return False
    
    return True


def show_new_request_interface():
    """Show interface for creating new analytics requests"""
    st.subheader("🎯 Create New Analytics Request")
    
    # Initialize session state
    if 'selected_project_id' not in st.session_state:
        st.session_state.selected_project_id = None
    if 'selected_repo_ids' not in st.session_state:
        st.session_state.selected_repo_ids = []
    
    # Step 1: Project Selection
    st.markdown("### 1. Select Project (Required)")
    
    try:
        # Get projects from database
        projects = get_projects_from_database()
        
        if not projects:
            st.error("❌ No projects found in database")
            st.info("Please ensure projects are configured and database is initialized.")
            return
        
        # Create project selection
        project_options = {f"{project.name}": project.id for project in projects}
        project_names = list(project_options.keys())
        
        selected_project_name = st.selectbox(
            "Choose a project:",
            options=[""] + project_names,
            index=0,
            help="Select the project containing repositories you want to analyze"
        )
        
        if selected_project_name:
            st.session_state.selected_project_id = project_options[selected_project_name]
            st.success(f"✅ Selected project: {selected_project_name}")
        else:
            st.session_state.selected_project_id = None
            st.session_state.selected_repo_ids = []
        
    except Exception as e:
        st.error(f"❌ Error loading projects: {str(e)}")
        return
    
    # Step 2: Repository Selection (only if project selected)
    if st.session_state.selected_project_id:
        st.markdown("### 2. Select Repositories (At least 1 required)")
        
        try:
            # Get repositories for selected project
            repositories = get_repositories_from_database(st.session_state.selected_project_id)
            
            if not repositories:
                st.warning("⚠️ No repositories found in selected project")
                return
            
            # Repository selection with checkboxes
            st.write(f"Select repositories from **{selected_project_name}**:")
            
            # Select All/None buttons
            col1, col2, col3 = st.columns([1, 1, 4])
            with col1:
                if st.button("☑️ Select All"):
                    st.session_state.selected_repo_ids = [repo.id for repo in repositories]
                    st.rerun()
            
            with col2:
                if st.button("☐ Select None"):
                    st.session_state.selected_repo_ids = []
                    st.rerun()
            
            # Repository checkboxes
            selected_repos = []
            for repo in repositories:
                is_selected = st.checkbox(
                    f"📁 {repo.name}",
                    value=repo.id in st.session_state.selected_repo_ids,
                    key=f"repo_{repo.id}",
                    help=f"Repository: {repo.name}"
                )
                if is_selected:
                    selected_repos.append(repo)
                    if repo.id not in st.session_state.selected_repo_ids:
                        st.session_state.selected_repo_ids.append(repo.id)
                elif repo.id in st.session_state.selected_repo_ids:
                    st.session_state.selected_repo_ids.remove(repo.id)
            
            # Show selected count
            if st.session_state.selected_repo_ids:
                st.info(f"✅ {len(st.session_state.selected_repo_ids)} repositories selected")
            
        except Exception as e:
            st.error(f"❌ Error loading repositories: {str(e)}")
            return
    
    # Step 3: Submit Request
    if st.session_state.selected_project_id and st.session_state.selected_repo_ids:
        st.markdown("### 3. Submit Request")
        
        # Show summary
        with st.expander("📋 Request Summary", expanded=True):
            st.write(f"**Project:** {selected_project_name}")
            st.write(f"**Repositories:** {len(st.session_state.selected_repo_ids)} selected")
            
            # Show selected repo names
            selected_repo_names = []
            for repo in repositories:
                if repo.id in st.session_state.selected_repo_ids:
                    selected_repo_names.append(repo.name)
            
            st.write("**Selected Repositories:**")
            for name in selected_repo_names:
                st.write(f"  • {name}")
        
        # Submit button
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🚀 Submit Request", type="primary"):
                submit_analytics_request(selected_project_name, st.session_state.selected_repo_ids)


def show_existing_requests_interface():
    """Show interface for viewing existing analytics requests"""
    st.subheader("📋 Analytics Request Status")
    
    try:
        # Get all requests from database
        requests = get_analytics_requests_from_database()
        
        if not requests:
            st.info("📭 No analytics requests found")
            return
        
        # Filter options
        col1, col2 = st.columns([1, 3])
        with col1:
            status_filter = st.selectbox(
                "Filter by status:",
                options=["All", "Requested", "Running", "Completed", "Failed"],
                index=0
            )
        
        # Filter requests
        if status_filter != "All":
            filtered_requests = [r for r in requests if r.status == status_filter]
        else:
            filtered_requests = requests
        
        if not filtered_requests:
            st.info(f"📭 No requests found with status: {status_filter}")
            return
        
        # Show requests in a table-like format
        for request in filtered_requests:
            show_request_card(request)
        
        # Auto-refresh for running requests
        running_requests = [r for r in requests if r.status == "Running"]
        if running_requests:
            # Auto-refresh every 5 seconds for running requests
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ Error loading requests: {str(e)}")


def show_request_card(request):
    """Show a single request as an expandable card"""
    # Status emoji
    status_emoji = {
        "Requested": "🕐",
        "Running": "🔄", 
        "Completed": "✅",
        "Failed": "❌"
    }
    
    # Card header
    with st.container():
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            st.write(f"**{status_emoji.get(request.status, '📊')} Request #{request.id}**")
            st.write(f"Project: {request.project_name}")
        
        with col2:
            st.write("**Status**")
            st.write(request.status)
        
        with col3:
            st.write("**Requested**")
            st.write(request.requested_date.strftime("%Y-%m-%d"))
        
        with col4:
            st.write("**Repositories**")
            st.write(f"{len(request.repository_ids)} repos")
    
    # Expandable details
    with st.expander(f"📝 Details for Request #{request.id}", expanded=False):
        detail_col1, detail_col2 = st.columns(2)
        
        with detail_col1:
            st.write(f"**Request ID:** {request.id}")
            st.write(f"**Project:** {request.project_name}")
            st.write(f"**Status:** {request.status}")
            st.write(f"**Requested Date:** {request.requested_date}")
            
            if request.started_date:
                st.write(f"**Started Date:** {request.started_date}")
            
            if request.completed_date:
                st.write(f"**Completed Date:** {request.completed_date}")
        
        with detail_col2:
            # Show repository names
            st.write("**Repositories:**")
            try:
                repo_names = get_repository_names_by_ids(request.repository_ids)
                for name in repo_names:
                    st.write(f"  • {name}")
            except:
                st.write(f"  • {len(request.repository_ids)} repositories")
            
            # Show progress for running requests
            if request.status == "Running" and request.progress_info:
                progress = request.progress_info
                total = progress.get("total_repos", len(request.repository_ids))
                completed = progress.get("completed_repos", 0)
                current = progress.get("current_repo", "")
                
                st.write("**Progress:**")
                progress_pct = completed / total if total > 0 else 0
                st.progress(progress_pct)
                st.write(f"{completed}/{total} repositories completed")
                
                if current:
                    st.write(f"Currently processing: {current}")
        
        # Show error message for failed requests
        if request.status == "Failed" and request.error_message:
            st.error(f"**Error:** {request.error_message}")
        
        # Show result files for completed requests
        if request.status == "Completed" and request.result_files:
            st.success("**Generated Files:**")
            for file_path in request.result_files:
                st.write(f"  📄 {file_path}")
    
    st.markdown("---")


def submit_analytics_request(project_name: str, repository_ids: list):
    """Submit a new analytics request"""
    try:
        # Check if polling service is running
        if not is_polling_service_running():
            st.error("❌ Background processing service is not running. Please restart the application.")
            return
        
        # Create request in database
        request = create_analytics_request_in_database(project_name, repository_ids)
        
        if request:
            st.success(f"✅ Analytics request #{request.id} created successfully!")
            st.info(f"🔄 Request added to processing queue")
            
            st.success(f"🚀 Request #{request.id} will be processed by the background service")
            st.info("You can monitor progress in the 'Existing Requests' tab")
            
            # Information about persistent processing
            st.info(
                "ℹ️ **Background Processing:** This request will be processed by the built-in "
                "background service. Processing will continue even if you close this tab."
            )
            
            # Clear selections
            st.session_state.selected_project_id = None
            st.session_state.selected_repo_ids = []
            
            # Auto-switch to existing requests tab
            st.balloons()
            
        else:
            st.error("❌ Failed to create analytics request")
            
    except Exception as e:
        st.error(f"❌ Error submitting request: {str(e)}")


# Database helper functions

@st.cache_data(ttl=60)  # Cache for 1 minute
def get_projects_from_database():
    """Get projects from database"""
    try:
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            db_manager = DatabaseManager()
            projects = loop.run_until_complete(db_manager.get_projects())
            return projects
        finally:
            loop.close()
    except Exception as e:
        st.error(f"Error loading projects: {e}")
        return []


@st.cache_data(ttl=60)  # Cache for 1 minute
def get_repositories_from_database(project_id: str):
    """Get repositories from database for a project"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            db_manager = DatabaseManager()
            repositories = loop.run_until_complete(db_manager.get_repositories(project_id))
            return repositories
        finally:
            loop.close()
    except Exception as e:
        st.error(f"Error loading repositories: {e}")
        return []


def get_analytics_requests_from_database():
    """Get analytics requests from database"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            db_manager = DatabaseManager()
            requests = loop.run_until_complete(db_manager.get_analytics_requests())
            return requests
        finally:
            loop.close()
    except Exception as e:
        st.error(f"Error loading requests: {e}")
        return []


def create_analytics_request_in_database(project_name: str, repository_ids: list):
    """Create analytics request in database"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            db_manager = DatabaseManager()
            request = loop.run_until_complete(
                db_manager.store_analytics_request(project_name, repository_ids)
            )
            return request
        finally:
            loop.close()
    except Exception as e:
        st.error(f"Error creating request: {e}")
        return None


def get_repository_names_by_ids(repository_ids: list):
    """Get repository names by their IDs"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            db_manager = DatabaseManager()
            names = []
            for repo_id in repository_ids:
                repo = loop.run_until_complete(db_manager.get_repository(repo_id))
                if repo:
                    names.append(repo.name)
            return names
        finally:
            loop.close()
    except Exception as e:
        return [f"Repository ID: {rid}" for rid in repository_ids] 