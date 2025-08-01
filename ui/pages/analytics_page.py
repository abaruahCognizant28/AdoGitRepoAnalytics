"""
Analytics visualization page with tabbed chart display
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.config import get_config
from src.database import DatabaseManager


def show():
    """Show analytics visualization page"""
    st.header("📈 Analytics Visualization")
    
    # Check if we have analysis results to display
    if 'analysis_results' not in st.session_state or not st.session_state.analysis_results:
        show_no_data_message()
        return
    
    # Repository selection for visualization
    repos = list(st.session_state.analysis_results.keys())
    
    with st.sidebar:
        st.subheader("🎯 Visualization Options")
        
        selected_repo = st.selectbox(
            "Select Repository",
            options=repos,
            help="Choose a repository to visualize"
        )
        
        show_comparisons = st.checkbox(
            "Show Comparisons",
            value=len(repos) > 1,
            help="Compare metrics across repositories"
        )
        
        chart_theme = st.selectbox(
            "Chart Theme",
            options=["streamlit", "plotly", "plotly_white", "plotly_dark"],
            index=0
        )
    
    # Create tabs for different analytics views
    create_analytics_tabs(selected_repo, show_comparisons, chart_theme)


def show_no_data_message():
    """Show message when no analysis data is available"""
    st.info("📊 No analysis data available")
    st.markdown("""
    To view analytics visualizations:
    
    1. **Configure** your Azure DevOps settings in the Configuration page
    2. **Run Analysis** in the Data Collection page
    3. **Return here** to view the generated charts and insights
    
    You can also load data from the database if you have previously stored analysis results.
    """)
    
    # Option to load from database
    with st.expander("🗄️ Load Data from Database"):
        if st.button("📥 Load Stored Results"):
            load_data_from_database()


def create_analytics_tabs(selected_repo: str, show_comparisons: bool, chart_theme: str):
    """Create tabs for different analytics visualizations"""
    
    tabs = st.tabs([
        "📊 Overview",
        "📝 Commits",
        "👥 Authors", 
        "🌿 Branches",
        "🔍 Code Quality",
        "⏰ Time Patterns",
        "🔄 Pull Requests",
        "🏥 Repository Health"
    ])
    
    with tabs[0]:
        show_overview_analytics(selected_repo, show_comparisons, chart_theme)
    
    with tabs[1]:
        show_commit_analytics(selected_repo, show_comparisons, chart_theme)
    
    with tabs[2]:
        show_author_analytics(selected_repo, show_comparisons, chart_theme)
    
    with tabs[3]:
        show_branch_analytics(selected_repo, show_comparisons, chart_theme)
    
    with tabs[4]:
        show_code_quality_analytics(selected_repo, show_comparisons, chart_theme)
    
    with tabs[5]:
        show_time_analytics(selected_repo, show_comparisons, chart_theme)
    
    with tabs[6]:
        show_pr_analytics(selected_repo, show_comparisons, chart_theme)
    
    with tabs[7]:
        show_health_analytics(selected_repo, show_comparisons, chart_theme)


def show_overview_analytics(repo: str, show_comparisons: bool, theme: str):
    """Show overview analytics dashboard"""
    st.subheader(f"📊 Overview - {repo}")
    
    # Get data for selected repository
    data = st.session_state.analysis_results.get(repo, {})
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Commits",
            data.get('commit_count', 0),
            delta=None
        )
    
    with col2:
        st.metric(
            "Contributors",
            data.get('author_count', 0),
            delta=None
        )
    
    with col3:
        st.metric(
            "Active Branches",
            data.get('branch_count', 0),
            delta=None
        )
    
    with col4:
        st.metric(
            "Pull Requests",
            data.get('pr_count', 0),
            delta=None
        )
    
    # Repository comparison chart (if multiple repos)
    if show_comparisons and len(st.session_state.analysis_results) > 1:
        st.markdown("### 📈 Repository Comparison")
        create_comparison_chart(theme)
    
    # Activity timeline (mock data)
    st.markdown("### 📅 Activity Timeline")
    create_activity_timeline(repo, theme)


def show_commit_analytics(repo: str, show_comparisons: bool, theme: str):
    """Show commit analytics"""
    st.subheader(f"📝 Commit Analytics - {repo}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Commits by day of week
        st.markdown("#### Commits by Day of Week")
        create_commits_by_day_chart(repo, theme)
    
    with col2:
        # Commits by hour
        st.markdown("#### Commits by Hour")
        create_commits_by_hour_chart(repo, theme)
    
    # Commit frequency over time
    st.markdown("#### 📈 Commit Frequency Over Time")
    create_commit_frequency_chart(repo, theme)
    
    # Commit size distribution
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Commit Size Distribution")
        create_commit_size_chart(repo, theme)
    
    with col2:
        st.markdown("#### Merge vs Regular Commits")
        create_merge_commits_chart(repo, theme)


def show_author_analytics(repo: str, show_comparisons: bool, theme: str):
    """Show author analytics"""
    st.subheader(f"👥 Author Analytics - {repo}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top contributors
        st.markdown("#### Top Contributors by Commits")
        create_top_contributors_chart(repo, theme)
    
    with col2:
        # Contribution distribution
        st.markdown("#### Contribution Distribution")
        create_contribution_distribution_chart(repo, theme)
    
    # Author activity heatmap
    st.markdown("#### 🗓️ Author Activity Heatmap")
    create_author_activity_heatmap(repo, theme)
    
    # Bus factor analysis
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Bus Factor Analysis")
        create_bus_factor_chart(repo, theme)
    
    with col2:
        st.markdown("#### Author Collaboration Network")
        create_collaboration_network(repo, theme)


def show_branch_analytics(repo: str, show_comparisons: bool, theme: str):
    """Show branch analytics"""
    st.subheader(f"🌿 Branch Analytics - {repo}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Branch Types")
        create_branch_types_chart(repo, theme)
    
    with col2:
        st.markdown("#### Branch Activity")
        create_branch_activity_chart(repo, theme)


def show_code_quality_analytics(repo: str, show_comparisons: bool, theme: str):
    """Show code quality analytics"""
    st.subheader(f"🔍 Code Quality Analytics - {repo}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Code Churn")
        create_code_churn_chart(repo, theme)
    
    with col2:
        st.markdown("#### Refactoring Activity")
        create_refactoring_chart(repo, theme)


def show_time_analytics(repo: str, show_comparisons: bool, theme: str):
    """Show time-based analytics"""
    st.subheader(f"⏰ Time Analytics - {repo}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Work Patterns")
        create_work_patterns_chart(repo, theme)
    
    with col2:
        st.markdown("#### Development Velocity")
        create_velocity_chart(repo, theme)


def show_pr_analytics(repo: str, show_comparisons: bool, theme: str):
    """Show pull request analytics"""
    st.subheader(f"🔄 Pull Request Analytics - {repo}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### PR Status Distribution")
        create_pr_status_chart(repo, theme)
    
    with col2:
        st.markdown("#### Review Cycle Time")
        create_pr_cycle_time_chart(repo, theme)


def show_health_analytics(repo: str, show_comparisons: bool, theme: str):
    """Show repository health analytics"""
    st.subheader(f"🏥 Repository Health - {repo}")
    
    # Health score
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Health Score", "85%", delta="5%")
    
    with col2:
        st.metric("Activity Level", "High", delta=None)
    
    with col3:
        st.metric("Bus Factor", "3", delta=None)
    
    # Health indicators
    create_health_indicators_chart(repo, theme)


def create_comparison_chart(theme: str):
    """Create repository comparison chart"""
    # Generate mock comparison data
    repos = list(st.session_state.analysis_results.keys())
    
    df = pd.DataFrame({
        'Repository': repos,
        'Commits': [st.session_state.analysis_results[repo].get('commit_count', 0) for repo in repos],
        'Authors': [st.session_state.analysis_results[repo].get('author_count', 0) for repo in repos],
        'Branches': [st.session_state.analysis_results[repo].get('branch_count', 0) for repo in repos],
        'Pull_Requests': [st.session_state.analysis_results[repo].get('pr_count', 0) for repo in repos]
    })
    
    fig = px.bar(
        df, 
        x='Repository', 
        y=['Commits', 'Authors', 'Branches', 'Pull_Requests'],
        title="Repository Metrics Comparison",
        template=theme
    )
    
    st.plotly_chart(fig, use_container_width=True)


def create_activity_timeline(repo: str, theme: str):
    """Create activity timeline chart"""
    # Generate mock timeline data
    dates = pd.date_range(start='2024-01-01', end='2024-12-01', freq='W')
    
    df = pd.DataFrame({
        'Date': dates,
        'Commits': [abs(int(x)) for x in np.random.normal(10, 3, len(dates))],
        'Pull_Requests': [abs(int(x)) for x in np.random.normal(3, 1, len(dates))]
    })
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['Commits'],
        mode='lines+markers',
        name='Commits',
        line=dict(color='#1f77b4')
    ))
    
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['Pull_Requests'],
        mode='lines+markers',
        name='Pull Requests',
        yaxis='y2',
        line=dict(color='#ff7f0e')
    ))
    
    fig.update_layout(
        title="Activity Timeline",
        xaxis_title="Date",
        yaxis_title="Commits",
        yaxis2=dict(
            title="Pull Requests",
            overlaying='y',
            side='right'
        ),
        template=theme
    )
    
    st.plotly_chart(fig, use_container_width=True)


def create_commits_by_day_chart(repo: str, theme: str):
    """Create commits by day of week chart"""
    # Mock data
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    commits = [45, 52, 48, 51, 42, 15, 8]
    
    fig = px.bar(
        x=days,
        y=commits,
        title="Commits by Day of Week",
        template=theme,
        color=commits,
        color_continuous_scale="Blues"
    )
    
    st.plotly_chart(fig, use_container_width=True)


def create_commits_by_hour_chart(repo: str, theme: str):
    """Create commits by hour chart"""
    # Mock data
    hours = list(range(24))
    commits = [2, 1, 0, 0, 0, 0, 1, 3, 8, 15, 18, 20, 22, 25, 20, 18, 15, 12, 8, 6, 4, 3, 2, 2]
    
    fig = px.line(
        x=hours,
        y=commits,
        title="Commits by Hour of Day",
        template=theme,
        markers=True
    )
    
    fig.update_xaxis(title="Hour of Day")
    fig.update_yaxis(title="Number of Commits")
    
    st.plotly_chart(fig, use_container_width=True)


def create_commit_frequency_chart(repo: str, theme: str):
    """Create commit frequency over time chart"""
    # Generate mock data
    dates = pd.date_range(start='2024-01-01', end='2024-12-01', freq='D')
    commits = np.random.poisson(3, len(dates))
    
    df = pd.DataFrame({
        'Date': dates,
        'Commits': commits
    })
    
    # Group by week for better visualization
    df_weekly = df.groupby(pd.Grouper(key='Date', freq='W')).sum().reset_index()
    
    fig = px.line(
        df_weekly,
        x='Date',
        y='Commits',
        title="Weekly Commit Frequency",
        template=theme
    )
    
    st.plotly_chart(fig, use_container_width=True)


def create_commit_size_chart(repo: str, theme: str):
    """Create commit size distribution chart"""
    # Mock data
    sizes = ['Small (1-10)', 'Medium (11-50)', 'Large (51-100)', 'XLarge (100+)']
    counts = [65, 25, 8, 2]
    
    fig = px.pie(
        values=counts,
        names=sizes,
        title="Commit Size Distribution",
        template=theme
    )
    
    st.plotly_chart(fig, use_container_width=True)


def create_merge_commits_chart(repo: str, theme: str):
    """Create merge vs regular commits chart"""
    # Mock data
    types = ['Regular Commits', 'Merge Commits']
    counts = [85, 15]
    
    fig = px.pie(
        values=counts,
        names=types,
        title="Merge vs Regular Commits",
        template=theme,
        color_discrete_sequence=['#3498db', '#e74c3c']
    )
    
    st.plotly_chart(fig, use_container_width=True)


def create_top_contributors_chart(repo: str, theme: str):
    """Create top contributors chart"""
    # Mock data
    authors = ['Alice Johnson', 'Bob Smith', 'Charlie Brown', 'Diana Prince', 'Eve Wilson']
    commits = [45, 38, 32, 28, 22]
    
    fig = px.bar(
        x=commits,
        y=authors,
        orientation='h',
        title="Top Contributors",
        template=theme,
        color=commits,
        color_continuous_scale="Viridis"
    )
    
    st.plotly_chart(fig, use_container_width=True)


def create_contribution_distribution_chart(repo: str, theme: str):
    """Create contribution distribution chart"""
    # Mock data showing Pareto distribution
    x = list(range(1, 21))
    y = [50, 25, 15, 8, 5, 3, 2, 2, 1, 1, 1, 1, 0.5, 0.5, 0.5, 0.3, 0.3, 0.2, 0.2, 0.1]
    
    fig = px.line(
        x=x,
        y=y,
        title="Contribution Distribution (Pareto)",
        template=theme,
        markers=True
    )
    
    fig.update_xaxis(title="Contributor Rank")
    fig.update_yaxis(title="Percentage of Total Commits")
    
    st.plotly_chart(fig, use_container_width=True)


def create_author_activity_heatmap(repo: str, theme: str):
    """Create author activity heatmap"""
    st.info("📊 Author activity heatmap would show commit patterns by author over time")


def create_bus_factor_chart(repo: str, theme: str):
    """Create bus factor chart"""
    # Mock data
    percentages = ['50%', '80%', '90%']
    authors = [2, 4, 6]
    
    fig = px.bar(
        x=percentages,
        y=authors,
        title="Bus Factor Analysis",
        template=theme,
        color=authors,
        color_continuous_scale="Reds"
    )
    
    fig.update_xaxis(title="Percentage of Work")
    fig.update_yaxis(title="Number of Authors")
    
    st.plotly_chart(fig, use_container_width=True)


def create_collaboration_network(repo: str, theme: str):
    """Create collaboration network visualization"""
    st.info("🕸️ Collaboration network would show how authors work together on files/features")


def create_branch_types_chart(repo: str, theme: str):
    """Create branch types chart"""
    # Mock data
    types = ['Feature', 'Hotfix', 'Release', 'Main', 'Other']
    counts = [12, 3, 2, 1, 4]
    
    fig = px.pie(
        values=counts,
        names=types,
        title="Branch Types",
        template=theme
    )
    
    st.plotly_chart(fig, use_container_width=True)


def create_branch_activity_chart(repo: str, theme: str):
    """Create branch activity chart"""
    st.info("🌿 Branch activity chart would show commits per branch over time")


def create_code_churn_chart(repo: str, theme: str):
    """Create code churn chart"""
    st.info("🔄 Code churn analysis would show files with high change frequency")


def create_refactoring_chart(repo: str, theme: str):
    """Create refactoring activity chart"""
    st.info("🔧 Refactoring analysis would show patterns in code restructuring")


def create_work_patterns_chart(repo: str, theme: str):
    """Create work patterns chart"""
    # Mock data
    patterns = ['Weekday Work', 'Weekend Work', 'After Hours']
    percentages = [75, 15, 10]
    
    fig = px.pie(
        values=percentages,
        names=patterns,
        title="Work Patterns",
        template=theme
    )
    
    st.plotly_chart(fig, use_container_width=True)


def create_velocity_chart(repo: str, theme: str):
    """Create development velocity chart"""
    st.info("⚡ Velocity chart would show development speed trends over time")


def create_pr_status_chart(repo: str, theme: str):
    """Create PR status distribution chart"""
    # Mock data
    statuses = ['Completed', 'Active', 'Abandoned']
    counts = [85, 12, 3]
    
    fig = px.pie(
        values=counts,
        names=statuses,
        title="Pull Request Status",
        template=theme
    )
    
    st.plotly_chart(fig, use_container_width=True)


def create_pr_cycle_time_chart(repo: str, theme: str):
    """Create PR cycle time chart"""
    st.info("⏱️ PR cycle time analysis would show review and merge times")


def create_health_indicators_chart(repo: str, theme: str):
    """Create repository health indicators chart"""
    # Mock data
    indicators = ['Activity', 'Documentation', 'Test Coverage', 'Code Quality', 'Security']
    scores = [85, 70, 60, 75, 80]
    
    fig = go.Figure(data=go.Scatterpolar(
        r=scores,
        theta=indicators,
        fill='toself',
        name='Health Score'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        title="Repository Health Indicators",
        template=theme
    )
    
    st.plotly_chart(fig, use_container_width=True)


def load_data_from_database():
    """Load analysis data from database"""
    st.info("🗄️ Database loading functionality would retrieve stored analysis results")
    # This would integrate with the DatabaseManager to load stored results


# Import numpy for mock data generation
try:
    import numpy as np
except ImportError:
    # Fallback if numpy is not available
    class MockNumpy:
        @staticmethod
        def random_normal(mean, std, size):
            import random
            return [random.gauss(mean, std) for _ in range(size)]
        
        @staticmethod
        def random_poisson(lam, size):
            import random
            return [random.randint(0, lam*2) for _ in range(size)]
    
    np = MockNumpy() 