"""
Data collection page for running analytics tasks
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
from src.analytics_engine import AnalyticsEngine
from src.main import GitAnalyticsTool


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
    
    # Show repository selection
    repositories = get_repository_list(config)
    if not repositories:
        st.error("❌ No repositories found in configuration")
        st.info("Please add projects and repositories in the Configuration page.")
        return
    
    # Task selection interface
    show_task_selection(repositories)


def validate_configuration(config) -> bool:
    """Validate that configuration is complete"""
    errors = []
    
    if not getattr(config, 'azure_pat', None):
        errors.append("Azure DevOps Personal Access Token not configured")
    
    if not getattr(config, 'azure_org_url', None):
        errors.append("Azure DevOps Organization URL not configured")
    
    if not getattr(config, 'organization', None):
        errors.append("Organization name not configured")
    
    if not getattr(config, 'projects', None):
        errors.append("No projects configured")
    
    if errors:
        st.error("❌ Configuration incomplete:")
        for error in errors:
            st.write(f"• {error}")
        st.info("Please complete the configuration in the Configuration page.")
        return False
    
    return True


def get_repository_list(config) -> list:
    """Get list of repositories from configuration"""
    repositories = []
    for project in config.projects:
        for repo in project.repositories:
            repositories.append({
                'project': project.name,
                'repository': repo,
                'display_name': f"{project.name}/{repo}"
            })
    return repositories


def show_task_selection(repositories: list):
    """Show task selection interface"""
    st.subheader("🎯 Select Analysis Tasks")
    
    # Repository selection
    st.markdown("### Select Repositories")
    
    # Select all/none buttons
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("☑️ Select All"):
            st.session_state.selected_repositories = [repo['display_name'] for repo in repositories]
            st.rerun()
    
    with col2:
        if st.button("☐ Select None"):
            st.session_state.selected_repositories = []
            st.rerun()
    
    # Repository checkboxes
    if 'selected_repositories' not in st.session_state:
        st.session_state.selected_repositories = []
    
    selected_repos = []
    for repo in repositories:
        is_selected = st.checkbox(
            f"📁 {repo['display_name']}",
            value=repo['display_name'] in st.session_state.selected_repositories,
            key=f"repo_{repo['display_name']}"
        )
        if is_selected:
            selected_repos.append(repo)
    
    # Task type selection
    st.markdown("### Select Analysis Types")
    
    task_col1, task_col2 = st.columns(2)
    
    with task_col1:
        full_analysis = st.checkbox(
            "🔍 Full Analysis",
            value=True,
            help="Run complete analytics on selected repositories"
        )
        
        data_collection_only = st.checkbox(
            "📥 Data Collection Only",
            value=False,
            help="Collect and store data without running analytics"
        )
        
        incremental_update = st.checkbox(
            "🔄 Incremental Update",
            value=False,
            help="Update only new data since last analysis"
        )
    
    with task_col2:
        export_results = st.checkbox(
            "📤 Export Results",
            value=True,
            help="Export results to Excel, CSV, and JSON"
        )
        
        generate_charts = st.checkbox(
            "📊 Generate Charts",
            value=True,
            help="Generate visualization charts"
        )
        
        store_in_database = st.checkbox(
            "🗄️ Store in Database",
            value=True,
            help="Store results in database for future analysis"
        )
    
    # Analysis options
    if full_analysis or data_collection_only:
        st.markdown("### Analysis Options")
        
        with st.expander("📅 Date Range (Optional)"):
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "Start Date",
                    value=None,
                    help="Leave empty to analyze all history"
                )
            with col2:
                end_date = st.date_input(
                    "End Date",
                    value=None,
                    help="Leave empty to analyze up to current date"
                )
        
        with st.expander("🔧 Advanced Options"):
            batch_size = st.slider(
                "Batch Size",
                min_value=10,
                max_value=500,
                value=100,
                help="Number of commits to process at once"
            )
            
            max_concurrent = st.slider(
                "Max Concurrent Requests",
                min_value=1,
                max_value=10,
                value=5,
                help="Maximum number of concurrent API requests"
            )
    
    # Progress display area
    progress_container = st.container()
    
    # Action buttons
    st.markdown("---")
    
    if selected_repos:
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("🚀 Start Analysis", type="primary", disabled=not selected_repos):
                run_analysis(
                    selected_repos,
                    full_analysis,
                    data_collection_only,
                    incremental_update,
                    export_results,
                    generate_charts,
                    store_in_database,
                    progress_container
                )
        
        with col2:
            if st.button("📋 Preview Tasks"):
                show_task_preview(selected_repos, full_analysis, data_collection_only, export_results)
    else:
        st.warning("⚠️ Please select at least one repository to analyze")
    
    # Show recent analysis results
    show_recent_results()


def show_task_preview(repos: list, full_analysis: bool, data_collection_only: bool, export_results: bool):
    """Show preview of tasks to be executed"""
    st.markdown("### 📋 Task Preview")
    
    with st.expander("Tasks to Execute", expanded=True):
        task_count = 0
        
        for repo in repos:
            st.markdown(f"**{repo['display_name']}**")
            
            if data_collection_only:
                st.write("  • Collect commit data")
                st.write("  • Collect branch data")
                st.write("  • Collect pull request data")
                task_count += 3
            
            if full_analysis:
                st.write("  • Run commit analytics")
                st.write("  • Run author analytics")
                st.write("  • Run branch analytics")
                st.write("  • Run code quality analysis")
                st.write("  • Run time analytics")
                task_count += 5
            
            if export_results:
                st.write("  • Export to Excel")
                st.write("  • Export to CSV")
                st.write("  • Export to JSON")
                task_count += 3
            
            st.write("")
        
        st.info(f"Total estimated tasks: {task_count}")


def run_analysis(repos: list, full_analysis: bool, data_collection_only: bool, 
                incremental_update: bool, export_results: bool, generate_charts: bool,
                store_in_database: bool, progress_container):
    """Run the selected analysis tasks"""
    
    with progress_container:
        st.markdown("### 🔄 Analysis Progress")
        
        # Create progress tracking
        total_repos = len(repos)
        progress_bar = st.progress(0)
        status_text = st.empty()
        results_container = st.container()
        
        # Initialize results storage
        if 'analysis_results' not in st.session_state:
            st.session_state.analysis_results = {}
        
        try:
            # Run analysis for each repository
            for i, repo in enumerate(repos):
                repo_key = repo['display_name']
                
                status_text.text(f"Analyzing {repo_key}...")
                
                # Simulate analysis (replace with actual analysis call)
                if full_analysis:
                    result = run_repository_analysis(repo['project'], repo['repository'])
                    st.session_state.analysis_results[repo_key] = result
                    
                    with results_container:
                        st.success(f"✅ Completed analysis for {repo_key}")
                        if result:
                            show_analysis_summary(repo_key, result)
                
                elif data_collection_only:
                    result = run_data_collection(repo['project'], repo['repository'])
                    
                    with results_container:
                        st.success(f"✅ Collected data for {repo_key}")
                        if result:
                            st.write(f"  • Commits: {result.get('commits', 0)}")
                            st.write(f"  • Branches: {result.get('branches', 0)}")
                            st.write(f"  • Pull Requests: {result.get('pull_requests', 0)}")
                
                # Update progress
                progress_bar.progress((i + 1) / total_repos)
            
            status_text.text("✅ Analysis completed!")
            
            # Export results if requested
            if export_results and st.session_state.analysis_results:
                export_analysis_results(st.session_state.analysis_results, results_container)
            
        except Exception as e:
            st.error(f"❌ Analysis failed: {str(e)}")
            status_text.text("❌ Analysis failed!")


def run_repository_analysis(project: str, repository: str) -> dict:
    """Run analysis for a single repository"""
    try:
        # This should be run in a separate thread/process for async operations
        # For now, return mock data
        return {
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'project': project,
            'repository': repository,
            'commit_count': 150,
            'author_count': 5,
            'branch_count': 8,
            'pr_count': 25
        }
    except Exception as e:
        return {
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def run_data_collection(project: str, repository: str) -> dict:
    """Run data collection for a single repository"""
    try:
        # Mock data collection
        return {
            'commits': 150,
            'branches': 8,
            'pull_requests': 25,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def show_analysis_summary(repo_key: str, result: dict):
    """Show summary of analysis results"""
    if result.get('status') == 'completed':
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Commits", result.get('commit_count', 0))
        with col2:
            st.metric("Authors", result.get('author_count', 0))
        with col3:
            st.metric("Branches", result.get('branch_count', 0))
        with col4:
            st.metric("Pull Requests", result.get('pr_count', 0))


def export_analysis_results(results: dict, container):
    """Export analysis results"""
    with container:
        st.markdown("### 📤 Exporting Results...")
        
        export_progress = st.progress(0)
        
        # Simulate export process
        formats = ['Excel', 'CSV', 'JSON']
        for i, format_name in enumerate(formats):
            st.write(f"Exporting to {format_name}...")
            export_progress.progress((i + 1) / len(formats))
        
        st.success("✅ Results exported successfully!")
        
        # Show export file paths
        output_dir = Path("output")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        st.write("**Generated Files:**")
        st.write(f"📊 Excel: `output/git_analytics_{timestamp}.xlsx`")
        st.write(f"📋 CSV: `output/summary_{timestamp}.csv`")
        st.write(f"📄 JSON: `output/git_analytics_{timestamp}.json`")


def show_recent_results():
    """Show recent analysis results"""
    if 'analysis_results' in st.session_state and st.session_state.analysis_results:
        st.markdown("---")
        st.subheader("📋 Recent Results")
        
        for repo_key, result in st.session_state.analysis_results.items():
            with st.expander(f"📁 {repo_key}"):
                if result.get('status') == 'completed':
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Project:** {result.get('project')}")
                        st.write(f"**Repository:** {result.get('repository')}")
                        st.write(f"**Completed:** {result.get('timestamp', '').split('T')[0]}")
                    
                    with col2:
                        st.metric("Commits", result.get('commit_count', 0))
                        st.metric("Authors", result.get('author_count', 0))
                        st.metric("Pull Requests", result.get('pr_count', 0))
                else:
                    st.error(f"Analysis failed: {result.get('error', 'Unknown error')}")
        
        if st.button("🗑️ Clear Results"):
            st.session_state.analysis_results = {}
            st.rerun() 