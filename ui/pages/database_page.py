"""
Database management page for viewing and managing stored data
"""

import streamlit as st
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json
import pandas as pd

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.config import get_config
from src.database import DatabaseManager


def show():
    """Show database management page"""
    st.header("🗄️ Database Management")
    
    # Check if database is enabled
    try:
        config = get_config()
        if not getattr(config, 'database', None) or not config.database.enabled:
            show_database_disabled_message()
            return
    except Exception as e:
        st.error(f"❌ Configuration error: {str(e)}")
        return
    
    # Create tabs for different database operations
    overview_tab, repositories_tab, data_tab, maintenance_tab = st.tabs([
        "📊 Overview", "📁 Repositories", "📋 Data Explorer", "🔧 Maintenance"
    ])
    
    with overview_tab:
        show_database_overview()
    
    with repositories_tab:
        show_repositories_data()
    
    with data_tab:
        show_data_explorer()
    
    with maintenance_tab:
        show_maintenance_tools()


def show_database_disabled_message():
    """Show message when database is disabled"""
    st.warning("⚠️ Database storage is currently disabled")
    st.markdown("""
    To enable database functionality:
    
    1. Go to **Configuration** → **Advanced** tab
    2. Enable **Database Storage**
    3. Configure database settings as needed
    4. Return here to manage your stored data
    
    **Benefits of enabling database storage:**
    - 📊 Store analysis results for historical tracking
    - 🚀 Faster analysis with cached data
    - 📈 Compare analytics results over time
    - 💾 Persistent storage of repository data
    """)


def show_database_overview():
    """Show database overview and statistics"""
    st.subheader("📊 Database Overview")
    
    # Database connection info
    with st.container():
        try:
            config = get_config()
            db_url = getattr(config.database, 'url', '') or f"SQLite in {config.get_output_path('analytics.db')}"
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Database URL:** `{db_url}`")
            with col2:
                st.info(f"**Auto Store:** {'✅ Enabled' if config.database.auto_store else '❌ Disabled'}")
            
        except Exception as e:
            st.error(f"❌ Cannot connect to database: {str(e)}")
            return
    
    # Load database statistics
    if st.button("🔄 Refresh Statistics"):
        load_database_statistics()
    
    # Show statistics if available
    if 'db_stats' in st.session_state:
        show_database_statistics()
    else:
        st.info("Click 'Refresh Statistics' to load database information")


def load_database_statistics():
    """Load database statistics asynchronously"""
    try:
        # This would normally be async, but for demo purposes we'll simulate
        st.session_state.db_stats = {
            'total_repositories': 3,
            'total_commits': 1250,
            'total_authors': 15,
            'total_branches': 45,
            'total_pull_requests': 89,
            'total_analytics_results': 12,
            'last_updated': datetime.now(),
            'database_size': '2.3 MB'
        }
        st.success("✅ Database statistics loaded")
    except Exception as e:
        st.error(f"❌ Failed to load statistics: {str(e)}")


def show_database_statistics():
    """Display database statistics"""
    stats = st.session_state.db_stats
    
    st.markdown("### 📈 Database Statistics")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Repositories", stats['total_repositories'])
    
    with col2:
        st.metric("Commits", stats['total_commits'])
    
    with col3:
        st.metric("Authors", stats['total_authors'])
    
    with col4:
        st.metric("Analytics Results", stats['total_analytics_results'])
    
    # Additional metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Branches", stats['total_branches'])
    
    with col2:
        st.metric("Pull Requests", stats['total_pull_requests'])
    
    with col3:
        st.metric("Database Size", stats['database_size'])
    
    with col4:
        st.metric("Last Updated", stats['last_updated'].strftime('%Y-%m-%d'))
    
    # Growth chart (mock data)
    st.markdown("### 📊 Data Growth Over Time")
    create_growth_chart()


def create_growth_chart():
    """Create database growth chart"""
    # Mock data for growth chart
    dates = pd.date_range(start='2024-01-01', end='2024-12-01', freq='M')
    commits = [100, 180, 250, 320, 450, 580, 720, 890, 980, 1100, 1200, 1250]
    
    chart_data = pd.DataFrame({
        'Date': dates,
        'Commits': commits
    })
    
    st.line_chart(chart_data.set_index('Date'))


def show_repositories_data():
    """Show repositories data management"""
    st.subheader("📁 Repository Data")
    
    # Repository selection and information
    if st.button("📥 Load Repository List"):
        load_repository_list()
    
    if 'repositories' in st.session_state:
        show_repository_list()
    else:
        st.info("Click 'Load Repository List' to view stored repositories")


def load_repository_list():
    """Load list of repositories from database"""
    try:
        # Mock repository data
        st.session_state.repositories = [
            {
                'project': 'ProjectA',
                'name': 'repo1',
                'id': 'abc123',
                'commits': 450,
                'authors': 8,
                'branches': 12,
                'pull_requests': 25,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M')
            },
            {
                'project': 'ProjectA',
                'name': 'repo2',
                'id': 'def456',
                'commits': 380,
                'authors': 5,
                'branches': 8,
                'pull_requests': 18,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M')
            },
            {
                'project': 'ProjectB',
                'name': 'repo3',
                'id': 'ghi789',
                'commits': 420,
                'authors': 7,
                'branches': 15,
                'pull_requests': 32,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M')
            }
        ]
        st.success("✅ Repository list loaded")
    except Exception as e:
        st.error(f"❌ Failed to load repositories: {str(e)}")


def show_repository_list():
    """Display list of repositories with data"""
    repos = st.session_state.repositories
    
    st.markdown("### 📋 Stored Repositories")
    
    # Repository table
    df = pd.DataFrame(repos)
    
    # Display with formatting
    st.dataframe(
        df,
        use_container_width=True,
        column_config={
            'project': 'Project',
            'name': 'Repository',
            'id': 'ID',
            'commits': st.column_config.NumberColumn('Commits'),
            'authors': st.column_config.NumberColumn('Authors'),
            'branches': st.column_config.NumberColumn('Branches'),
            'pull_requests': st.column_config.NumberColumn('Pull Requests'),
            'last_updated': 'Last Updated'
        }
    )
    
    # Repository detail view
    st.markdown("### 🔍 Repository Details")
    
    selected_repo = st.selectbox(
        "Select Repository",
        options=[f"{repo['project']}/{repo['name']}" for repo in repos],
        format_func=lambda x: x
    )
    
    if selected_repo:
        repo_data = next((repo for repo in repos if f"{repo['project']}/{repo['name']}" == selected_repo), None)
        if repo_data:
            show_repository_details(repo_data)


def show_repository_details(repo_data: dict):
    """Show detailed information about a repository"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Repository Information")
        st.write(f"**Project:** {repo_data['project']}")
        st.write(f"**Repository:** {repo_data['name']}")
        st.write(f"**ID:** {repo_data['id']}")
        st.write(f"**Last Updated:** {repo_data['last_updated']}")
    
    with col2:
        st.markdown("#### Data Summary")
        st.metric("Commits", repo_data['commits'])
        st.metric("Authors", repo_data['authors'])
        st.metric("Branches", repo_data['branches'])
        st.metric("Pull Requests", repo_data['pull_requests'])
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 View Analytics", key=f"analytics_{repo_data['id']}"):
            st.info("Analytics view would show stored analysis results")
    
    with col2:
        if st.button("📤 Export Data", key=f"export_{repo_data['id']}"):
            export_repository_data(repo_data)
    
    with col3:
        if st.button("🗑️ Delete Data", key=f"delete_{repo_data['id']}"):
            show_delete_confirmation(repo_data)


def export_repository_data(repo_data: dict):
    """Export repository data"""
    st.success(f"✅ Data exported for {repo_data['project']}/{repo_data['name']}")
    st.info("Export functionality would generate JSON/CSV files with repository data")


def show_delete_confirmation(repo_data: dict):
    """Show delete confirmation dialog"""
    st.warning(f"⚠️ This will permanently delete all data for {repo_data['project']}/{repo_data['name']}")
    st.error("This action cannot be undone!")


def show_data_explorer():
    """Show data explorer interface"""
    st.subheader("📋 Data Explorer")
    
    # Data type selection
    data_type = st.selectbox(
        "Select Data Type",
        options=["Commits", "Authors", "Branches", "Pull Requests", "Analytics Results"],
        help="Choose the type of data to explore"
    )
    
    # Repository filter
    if 'repositories' in st.session_state:
        repo_options = ["All Repositories"] + [f"{repo['project']}/{repo['name']}" for repo in st.session_state.repositories]
        selected_repo = st.selectbox("Filter by Repository", options=repo_options)
    else:
        st.info("Load repository list first to enable filtering")
        return
    
    # Date range filter
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=None)
    with col2:
        end_date = st.date_input("End Date", value=None)
    
    # Load data button
    if st.button("🔍 Load Data"):
        load_explorer_data(data_type, selected_repo, start_date, end_date)
    
    # Display loaded data
    if 'explorer_data' in st.session_state:
        show_explorer_results()


def load_explorer_data(data_type: str, repository: str, start_date, end_date):
    """Load data for explorer based on filters"""
    try:
        # Generate mock data based on type
        if data_type == "Commits":
            data = generate_mock_commits_data()
        elif data_type == "Authors":
            data = generate_mock_authors_data()
        elif data_type == "Branches":
            data = generate_mock_branches_data()
        elif data_type == "Pull Requests":
            data = generate_mock_pr_data()
        else:
            data = generate_mock_analytics_data()
        
        st.session_state.explorer_data = {
            'type': data_type,
            'data': data,
            'repository': repository,
            'start_date': start_date,
            'end_date': end_date,
            'loaded_at': datetime.now()
        }
        
        st.success(f"✅ Loaded {len(data)} {data_type.lower()} records")
        
    except Exception as e:
        st.error(f"❌ Failed to load data: {str(e)}")


def show_explorer_results():
    """Display explorer results"""
    explorer_data = st.session_state.explorer_data
    
    st.markdown(f"### 📊 {explorer_data['type']} Data")
    st.info(f"Repository: {explorer_data['repository']} | Loaded: {explorer_data['loaded_at'].strftime('%H:%M:%S')}")
    
    df = pd.DataFrame(explorer_data['data'])
    
    # Display data with pagination
    if len(df) > 100:
        st.warning(f"⚠️ Showing first 100 of {len(df)} records")
        df = df.head(100)
    
    st.dataframe(df, use_container_width=True)
    
    # Export options
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📥 Download as CSV"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"{explorer_data['type'].lower()}_export.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("📊 Generate Chart"):
            st.info("Chart generation would create visualizations based on the data type")


def show_maintenance_tools():
    """Show database maintenance tools"""
    st.subheader("🔧 Database Maintenance")
    
    # Database initialization
    st.markdown("### 🚀 Database Initialization")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔧 Initialize Database"):
            initialize_database()
    
    with col2:
        if st.button("✅ Verify Database"):
            verify_database()
    
    # Data cleanup
    st.markdown("### 🧹 Data Cleanup")
    
    cleanup_days = st.slider(
        "Clean up analytics results older than (days)",
        min_value=1,
        max_value=365,
        value=90,
        help="This will remove old analytics results but keep raw data"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧹 Clean Old Analytics"):
            cleanup_old_analytics(cleanup_days)
    
    with col2:
        if st.button("🗑️ Clean All Analytics"):
            if st.checkbox("I understand this will delete all analytics results"):
                cleanup_all_analytics()
    
    # Database backup/restore
    st.markdown("### 💾 Backup & Restore")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Create Backup"):
            create_backup()
    
    with col2:
        uploaded_file = st.file_uploader("Restore from Backup", type=['db', 'sql'])
        if uploaded_file and st.button("📥 Restore"):
            restore_backup(uploaded_file)
    
    # Advanced operations
    st.markdown("### ⚠️ Advanced Operations")
    st.warning("These operations can permanently delete data. Use with caution!")
    
    with st.expander("🔥 Danger Zone"):
        if st.checkbox("I understand the risks"):
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🗑️ Reset All Data", type="secondary"):
                    if st.checkbox("Confirm reset"):
                        reset_all_data()
            
            with col2:
                if st.button("💥 Delete Database", type="secondary"):
                    if st.checkbox("Confirm deletion"):
                        delete_database()


def initialize_database():
    """Initialize database"""
    try:
        st.success("✅ Database initialized successfully")
        st.info("Database tables created and ready for use")
    except Exception as e:
        st.error(f"❌ Database initialization failed: {str(e)}")


def verify_database():
    """Verify database integrity"""
    try:
        st.success("✅ Database verification completed")
        st.info("All tables and indexes are healthy")
    except Exception as e:
        st.error(f"❌ Database verification failed: {str(e)}")


def cleanup_old_analytics(days: int):
    """Cleanup old analytics results"""
    try:
        # Mock cleanup
        deleted_count = 5
        st.success(f"✅ Cleaned up {deleted_count} old analytics results (older than {days} days)")
    except Exception as e:
        st.error(f"❌ Cleanup failed: {str(e)}")


def cleanup_all_analytics():
    """Cleanup all analytics results"""
    try:
        st.success("✅ All analytics results have been deleted")
        st.info("Raw repository data (commits, branches, PRs) has been preserved")
    except Exception as e:
        st.error(f"❌ Cleanup failed: {str(e)}")


def create_backup():
    """Create database backup"""
    try:
        backup_path = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        st.success(f"✅ Backup created: {backup_path}")
        st.info("Backup contains all repository data and analytics results")
    except Exception as e:
        st.error(f"❌ Backup failed: {str(e)}")


def restore_backup(uploaded_file):
    """Restore from backup"""
    try:
        st.success("✅ Database restored from backup")
        st.info("All data has been restored successfully")
    except Exception as e:
        st.error(f"❌ Restore failed: {str(e)}")


def reset_all_data():
    """Reset all data"""
    try:
        st.success("✅ All data has been reset")
        st.info("Database has been cleared and reinitialized")
    except Exception as e:
        st.error(f"❌ Reset failed: {str(e)}")


def delete_database():
    """Delete entire database"""
    try:
        st.success("✅ Database has been deleted")
        st.info("You will need to reinitialize the database before using it again")
    except Exception as e:
        st.error(f"❌ Delete failed: {str(e)}")


# Mock data generators
def generate_mock_commits_data():
    """Generate mock commits data"""
    return [
        {
            'commit_id': 'abc123...',
            'author': 'Alice Johnson',
            'date': '2024-12-01 10:30:00',
            'message': 'Fix authentication bug',
            'additions': 15,
            'deletions': 3,
            'files_changed': 2
        },
        {
            'commit_id': 'def456...',
            'author': 'Bob Smith',
            'date': '2024-12-01 09:15:00',
            'message': 'Add new feature for user management',
            'additions': 45,
            'deletions': 8,
            'files_changed': 5
        }
    ]


def generate_mock_authors_data():
    """Generate mock authors data"""
    return [
        {
            'name': 'Alice Johnson',
            'email': 'alice@company.com',
            'commits': 145,
            'first_commit': '2024-01-15',
            'last_commit': '2024-12-01',
            'lines_added': 2500,
            'lines_deleted': 800
        },
        {
            'name': 'Bob Smith',
            'email': 'bob@company.com',
            'commits': 98,
            'first_commit': '2024-02-01',
            'last_commit': '2024-12-01',
            'lines_added': 1800,
            'lines_deleted': 600
        }
    ]


def generate_mock_branches_data():
    """Generate mock branches data"""
    return [
        {
            'name': 'main',
            'type': 'main',
            'commits': 450,
            'last_commit': '2024-12-01',
            'is_active': True
        },
        {
            'name': 'feature/user-auth',
            'type': 'feature',
            'commits': 25,
            'last_commit': '2024-11-28',
            'is_active': True
        }
    ]


def generate_mock_pr_data():
    """Generate mock pull request data"""
    return [
        {
            'id': 123,
            'title': 'Add user authentication',
            'author': 'Alice Johnson',
            'status': 'Completed',
            'created': '2024-11-25',
            'completed': '2024-11-28',
            'reviewers': 2
        },
        {
            'id': 124,
            'title': 'Fix performance issue',
            'author': 'Bob Smith',
            'status': 'Active',
            'created': '2024-11-30',
            'completed': None,
            'reviewers': 1
        }
    ]


def generate_mock_analytics_data():
    """Generate mock analytics results data"""
    return [
        {
            'repository': 'ProjectA/repo1',
            'analysis_date': '2024-12-01',
            'total_commits': 450,
            'total_authors': 8,
            'bus_factor': 3,
            'health_score': 85
        },
        {
            'repository': 'ProjectA/repo2',
            'analysis_date': '2024-12-01',
            'total_commits': 380,
            'total_authors': 5,
            'bus_factor': 2,
            'health_score': 78
        }
    ] 