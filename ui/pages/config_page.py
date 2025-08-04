"""
Configuration page for Azure DevOps settings
"""

import streamlit as st
import yaml
import os
from pathlib import Path
import sys
import asyncio

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.config import get_config, reload_config
from src.azure_client import AzureDevOpsClient


async def fetch_azure_projects(org_url: str, pat: str):
    """Fetch projects from Azure DevOps"""
    try:
        # Temporarily set environment variables for the client
        old_pat = os.environ.get('AZURE_DEVOPS_PAT')
        old_org_url = os.environ.get('AZURE_DEVOPS_ORG_URL')
        
        os.environ['AZURE_DEVOPS_PAT'] = pat
        os.environ['AZURE_DEVOPS_ORG_URL'] = org_url
        
        # Create a minimal config file temporarily if it doesn't exist
        config_path = Path("config/repositories.yaml")
        config_exists = config_path.exists()
        
        if not config_exists:
            config_path.parent.mkdir(exist_ok=True)
            minimal_config = {
                'azure_devops': {
                    'organization': org_url.split('/')[-1],
                    'projects': []
                }
            }
            with open(config_path, 'w') as f:
                yaml.dump(minimal_config, f)
        
        try:
            async with AzureDevOpsClient() as client:
                projects = await client.get_projects()
                return [{'id': p.id, 'name': p.name, 'description': p.description} for p in projects]
        finally:
            # Restore original environment variables
            if old_pat is not None:
                os.environ['AZURE_DEVOPS_PAT'] = old_pat
            elif 'AZURE_DEVOPS_PAT' in os.environ:
                del os.environ['AZURE_DEVOPS_PAT']
                
            if old_org_url is not None:
                os.environ['AZURE_DEVOPS_ORG_URL'] = old_org_url
            elif 'AZURE_DEVOPS_ORG_URL' in os.environ:
                del os.environ['AZURE_DEVOPS_ORG_URL']
            
            # Clean up temporary config if we created it
            if not config_exists and config_path.exists():
                try:
                    config_path.unlink()
                except:
                    pass
                    
    except Exception as e:
        st.error(f"Failed to fetch projects from Azure DevOps: {str(e)}")
        return []


def show():
    """Show configuration page"""
    st.header("⚙️ Configuration")
    
    # Create tabs for different configuration sections
    env_tab, projects_tab, analytics_tab, advanced_tab = st.tabs([
        "🔐 Environment", "📁 Projects", "📊 Analytics", "⚙️ Advanced"
    ])
    
    with env_tab:
        show_environment_config()
    
    with projects_tab:
        show_projects_config()
    
    with analytics_tab:
        show_analytics_config()
    
    with advanced_tab:
        show_advanced_config()


def show_environment_config():
    """Show environment configuration (PAT, Org URL)"""
    st.subheader("Azure DevOps Connection")
    st.markdown("Configure your Azure DevOps Personal Access Token and organization URL.")
    
    # Load current environment variables
    current_pat = os.getenv("AZURE_DEVOPS_PAT", "")
    current_org_url = os.getenv("AZURE_DEVOPS_ORG_URL", "")
    
    # Input fields
    with st.form("environment_form"):
        pat = st.text_input(
            "Personal Access Token",
            value=current_pat,
            type="password",
            help="Your Azure DevOps Personal Access Token with Code (read) and Project (read) permissions"
        )
        
        org_url = st.text_input(
            "Organization URL",
            value=current_org_url,
            placeholder="https://dev.azure.com/your-organization",
            help="Your Azure DevOps organization URL"
        )
        
        col1, col2 = st.columns([1, 3])
        with col1:
            save_env = st.form_submit_button("💾 Save Environment", type="primary")
        
        if save_env:
            if pat and org_url:
                save_environment_config(pat, org_url)
                # Reload configuration to reflect changes
                reload_config()
                st.success("✅ Environment configuration saved and applied!")
                st.rerun()
            else:
                st.error("❌ Please fill in all required fields")
    
    # Instructions for getting PAT
    with st.expander("🔗 How to get a Personal Access Token"):
        st.markdown("""
        1. Go to your Azure DevOps organization: `https://dev.azure.com/[your-organization]`
        2. Click on **User Settings** → **Personal Access Tokens**
        3. Click **+ New Token**
        4. Give it a name and set expiration
        5. Select these scopes:
           - **Code (read)**: Access to repository data
           - **Project and team (read)**: Access to project information
        6. Click **Create** and copy the token
        
        ⚠️ **Important**: Save the token securely - you won't be able to see it again!
        """)


def show_projects_config():
    """Show projects and repositories configuration"""
    st.subheader("Projects & Repositories")
    st.markdown("Configure which projects and repositories to analyze.")
    
    try:
        config = get_config()
        organization = getattr(config, 'organization', '')
        projects = getattr(config, 'projects', [])
    except Exception:
        organization = ''
        projects = []
    
    # Convert ProjectConfig objects to dictionaries for easier handling
    current_projects = []
    if projects:
        current_projects = [
            {'name': p.name, 'repositories': p.repositories} 
            for p in projects
        ]
    
    # Check if we need to show Azure DevOps project discovery
    show_azure_discovery = len(current_projects) == 0
    
    # Environment variables for Azure DevOps access
    current_pat = os.getenv("AZURE_DEVOPS_PAT", "")
    current_org_url = os.getenv("AZURE_DEVOPS_ORG_URL", "")
    
    # Azure DevOps Project Discovery Section
    if show_azure_discovery and current_pat and current_org_url:
        st.markdown("### 🔍 Discover Projects from Azure DevOps")
        st.info("No projects are currently configured. You can discover projects from your Azure DevOps organization.")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("🔍 Fetch Projects", type="primary"):
                with st.spinner("Fetching projects from Azure DevOps..."):
                    # Run async function
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        azure_projects = loop.run_until_complete(
                            fetch_azure_projects(current_org_url, current_pat)
                        )
                        loop.close()
                        
                        if azure_projects:
                            st.session_state['discovered_projects'] = azure_projects
                            st.success(f"✅ Found {len(azure_projects)} projects!")
                            st.rerun()
                        else:
                            st.warning("No projects found or unable to connect.")
                    except Exception as e:
                        st.error(f"Error fetching projects: {str(e)}")
        
        # Show discovered projects for selection
        if 'discovered_projects' in st.session_state and st.session_state['discovered_projects']:
            st.markdown("### 📋 Select Projects to Add")
            discovered_projects = st.session_state['discovered_projects']
            
            with st.form("select_projects_form"):
                selected_projects = []
                
                for project in discovered_projects:
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        selected = st.checkbox(
                            f"Select", 
                            key=f"select_{project['id']}"
                        )
                    with col2:
                        st.markdown(f"**{project['name']}**")
                        if project['description']:
                            st.markdown(f"*{project['description']}*")
                    
                    if selected:
                        selected_projects.append(project['name'])
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    add_selected = st.form_submit_button("➕ Add Selected Projects", type="primary")
                
                if add_selected and selected_projects:
                    # Add selected projects with empty repositories list
                    new_projects = [{'name': name, 'repositories': ['']} for name in selected_projects]
                    org_from_url = current_org_url.split('/')[-1] if current_org_url else organization
                    save_projects_config(org_from_url, new_projects)
                    reload_config()
                    
                    # Clear the discovered projects from session state
                    if 'discovered_projects' in st.session_state:
                        del st.session_state['discovered_projects']
                    
                    st.success(f"✅ Added {len(selected_projects)} projects!")
                    st.rerun()
        
        st.markdown("---")
    
    # Manual Project Configuration Section
    st.markdown("### ✏️ Manual Project Configuration")
    
    # Ensure we have at least one project template for manual entry
    if not current_projects:
        current_projects = [{'name': '', 'repositories': ['']}]
    
    with st.form("projects_form"):
        # Organization name
        org_name = st.text_input(
            "Organization Name",
            value=organization or (current_org_url.split('/')[-1] if current_org_url else ''),
            help="The name of your Azure DevOps organization (not the full URL)"
        )
        
        st.markdown("#### Projects and Repositories")
        
        # Use container to manage dynamic content
        project_configs = []
        
        # Display existing projects
        for i, project in enumerate(current_projects):
            st.markdown(f"**Project {i + 1}**")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                project_name = st.text_input(
                    "Project Name",
                    value=project.get('name', ''),
                    key=f"project_name_{i}",
                    placeholder="Enter project name"
                )
            
            # Repositories for this project
            repositories = project.get('repositories', [''])
            repo_configs = []
            
            st.markdown("**Repositories:**")
            for j, repo in enumerate(repositories):
                repo_name = st.text_input(
                    "Repository",
                    value=repo,
                    key=f"repo_{i}_{j}",
                    placeholder="Enter repository name or leave empty to fetch all"
                )
                if repo_name.strip():  # Only add non-empty repos
                    repo_configs.append(repo_name.strip())
            
            if project_name.strip():  # Only add non-empty projects
                project_configs.append({
                    'name': project_name.strip(),
                    'repositories': repo_configs if repo_configs else ['']  # Ensure at least one repo slot
                })
            
            st.markdown("---")
        
        # Save button
        col1, col2 = st.columns([1, 3])
        with col1:
            save_projects = st.form_submit_button("💾 Save & Apply", type="primary")
        
        if save_projects:
            if org_name and any(p['name'] for p in project_configs):
                # Save directly to config file
                save_projects_config(org_name, project_configs)
                # Reload configuration to reflect changes
                reload_config()
                st.success("✅ Projects configuration saved and applied!")
                st.rerun()
            else:
                st.error("❌ Please provide organization name and at least one project")
    
    # Management buttons outside the form
    st.markdown("### 🔧 Manage Projects")
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        if st.button("➕ Add Project"):
            # Add a new project by modifying the config directly
            current_projects.append({'name': '', 'repositories': ['']})
            save_projects_config(organization, current_projects)
            reload_config()
            st.rerun()
    
    with col2:
        if st.button("🗑️ Remove Last") and len(current_projects) > 1:
            # Remove last project
            current_projects.pop()
            save_projects_config(organization, current_projects)
            reload_config()
            st.rerun()
    
    with col3:
        if st.button("🔄 Refresh Discovery"):
            # Clear discovered projects to allow re-fetching
            if 'discovered_projects' in st.session_state:
                del st.session_state['discovered_projects']
            st.rerun()
    
    with col4:
        if st.button("🧹 Clear All"):
            # Clear all projects
            save_projects_config(organization, [])
            reload_config()
            st.rerun()


def show_analytics_config():
    """Show analytics configuration"""
    st.subheader("Analytics Settings")
    st.markdown("Configure which analytics to include and date ranges.")
    
    try:
        config = get_config()
        analytics = getattr(config, 'analytics', None)
        date_range = getattr(config, 'date_range', None)
    except Exception:
        analytics = None
        date_range = None
    
    with st.form("analytics_form"):
        # Date range
        st.markdown("### Date Range")
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
                help="Leave empty to analyze all history"
            )
        
        # Analytics toggles
        st.markdown("### Analytics Types")
        st.markdown("Select which analytics to include in the analysis:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            commit_analytics = st.checkbox(
                "📝 Commit Analytics",
                value=getattr(analytics, 'commit_analytics', True) if analytics else True,
                help="Frequency, volume, timing, and trends"
            )
            
            author_analytics = st.checkbox(
                "👥 Author Analytics",
                value=getattr(analytics, 'author_analytics', True) if analytics else True,
                help="Productivity, collaboration patterns, bus factor"
            )
            
            branch_analytics = st.checkbox(
                "🌿 Branch Analytics",
                value=getattr(analytics, 'branch_analytics', True) if analytics else True,
                help="Lifecycle, naming conventions, merge patterns"
            )
            
            code_quality = st.checkbox(
                "🔍 Code Quality",
                value=getattr(analytics, 'code_quality', True) if analytics else True,
                help="Churn analysis, complexity tracking"
            )
            
            file_analytics = st.checkbox(
                "📄 File Analytics",
                value=getattr(analytics, 'file_analytics', True) if analytics else True,
                help="File change patterns and hotspots"
            )
            
            time_analytics = st.checkbox(
                "⏰ Time Analytics",
                value=getattr(analytics, 'time_analytics', True) if analytics else True,
                help="Development velocity, work patterns"
            )
        
        with col2:
            pr_analytics = st.checkbox(
                "🔄 Pull Request Analytics",
                value=getattr(analytics, 'pull_request_analytics', True) if analytics else True,
                help="Review cycles, conflict resolution"
            )
            
            repo_health = st.checkbox(
                "💚 Repository Health",
                value=getattr(analytics, 'repository_health', True) if analytics else True,
                help="Overall repository health indicators"
            )
            
            team_analytics = st.checkbox(
                "👥 Team Analytics",
                value=getattr(analytics, 'team_analytics', True) if analytics else True,
                help="Collaboration patterns, knowledge distribution"
            )
            
            security_analytics = st.checkbox(
                "🔒 Security Analytics",
                value=getattr(analytics, 'security_analytics', True) if analytics else True,
                help="Security-related patterns and commits"
            )
            
            performance_analytics = st.checkbox(
                "⚡ Performance Analytics",
                value=getattr(analytics, 'performance_analytics', True) if analytics else True,
                help="Performance-related patterns"
            )
            
            tech_analytics = st.checkbox(
                "🔧 Technology Analytics",
                value=getattr(analytics, 'technology_analytics', True) if analytics else True,
                help="Technology and language patterns"
            )
        
        save_analytics = st.form_submit_button("💾 Save Analytics", type="primary")
        
        if save_analytics:
            analytics_config = {
                'commit_analytics': commit_analytics,
                'author_analytics': author_analytics,
                'branch_analytics': branch_analytics,
                'code_quality': code_quality,
                'file_analytics': file_analytics,
                'time_analytics': time_analytics,
                'pull_request_analytics': pr_analytics,
                'repository_health': repo_health,
                'team_analytics': team_analytics,
                'security_analytics': security_analytics,
                'performance_analytics': performance_analytics,
                'technology_analytics': tech_analytics
            }
            
            date_config = {
                'start_date': start_date.strftime('%Y-%m-%d') if start_date else '',
                'end_date': end_date.strftime('%Y-%m-%d') if end_date else ''
            }
            
            save_analytics_config(analytics_config, date_config)
            # Reload configuration to reflect changes
            reload_config()
            st.success("✅ Analytics configuration saved and applied!")


def show_advanced_config():
    """Show advanced configuration options"""
    st.subheader("Advanced Settings")
    
    try:
        config = get_config()
    except Exception:
        config = None
    
    with st.form("advanced_form"):
        # API Settings
        st.markdown("### API Settings")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            api_timeout = st.number_input(
                "Timeout (seconds)",
                min_value=10,
                max_value=300,
                value=getattr(config.api, 'timeout', 30) if config and hasattr(config, 'api') else 30
            )
        
        with col2:
            retry_attempts = st.number_input(
                "Retry Attempts",
                min_value=1,
                max_value=10,
                value=getattr(config.api, 'retry_attempts', 3) if config and hasattr(config, 'api') else 3
            )
        
        with col3:
            rate_limit_delay = st.number_input(
                "Rate Limit Delay (seconds)",
                min_value=0.1,
                max_value=10.0,
                value=float(getattr(config.api, 'rate_limit_delay', 1.0)) if config and hasattr(config, 'api') else 1.0,
                step=0.1
            )
        
        # Processing Settings
        st.markdown("### Processing Settings")
        col1, col2 = st.columns(2)
        
        with col1:
            batch_size = st.number_input(
                "Batch Size",
                min_value=10,
                max_value=1000,
                value=getattr(config.processing, 'batch_size', 100) if config and hasattr(config, 'processing') else 100
            )
        
        with col2:
            max_file_size = st.number_input(
                "Max File Size (MB)",
                min_value=1,
                max_value=100,
                value=getattr(config.processing, 'max_file_size_mb', 10) if config and hasattr(config, 'processing') else 10
            )
        
        # Database Settings
        st.markdown("### Database Settings")
        
        db_enabled = st.checkbox(
            "Enable Database Storage",
            value=getattr(config.database, 'enabled', True) if config and hasattr(config, 'database') else True,
            help="Store data in database for faster subsequent analysis"
        )
        
        auto_store = st.checkbox(
            "Auto Store Data",
            value=getattr(config.database, 'auto_store', True) if config and hasattr(config, 'database') else True,
            help="Automatically store data during analysis"
        )
        
        cleanup_days = st.number_input(
            "Cleanup Days",
            min_value=1,
            max_value=365,
            value=getattr(config.database, 'cleanup_days', 90) if config and hasattr(config, 'database') else 90,
            help="Clean up analytics results older than this many days"
        )
        
        # Privacy Settings
        st.markdown("### Privacy Settings")
        
        anonymize_authors = st.checkbox(
            "Anonymize Authors",
            value=getattr(config.privacy, 'anonymize_authors', False) if config and hasattr(config, 'privacy') else False,
            help="Replace author names with hashes for privacy"
        )
        
        save_advanced = st.form_submit_button("💾 Save Advanced", type="primary")
        
        if save_advanced:
            advanced_config = {
                'api': {
                    'timeout': api_timeout,
                    'retry_attempts': retry_attempts,
                    'rate_limit_delay': rate_limit_delay
                },
                'processing': {
                    'batch_size': batch_size,
                    'max_file_size_mb': max_file_size
                },
                'database': {
                    'enabled': db_enabled,
                    'auto_store': auto_store,
                    'cleanup_days': cleanup_days
                },
                'privacy': {
                    'anonymize_authors': anonymize_authors
                }
            }
            
            save_advanced_config(advanced_config)
            # Reload configuration to reflect changes
            reload_config()
            st.success("✅ Advanced configuration saved and applied!")


def save_environment_config(pat: str, org_url: str):
    """Save environment configuration to .env file"""
    env_path = Path(".env")
    
    # Read existing .env file
    env_vars = {}
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
    
    # Update with new values
    env_vars['AZURE_DEVOPS_PAT'] = pat
    env_vars['AZURE_DEVOPS_ORG_URL'] = org_url
    
    # Write back to .env file
    with open(env_path, 'w') as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    # Update environment
    os.environ['AZURE_DEVOPS_PAT'] = pat
    os.environ['AZURE_DEVOPS_ORG_URL'] = org_url


def save_projects_config(organization: str, projects: list):
    """Save projects configuration to YAML file"""
    config_path = Path("config/repositories.yaml")
    
    # Load existing config
    if config_path.exists():
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
    else:
        config_data = {}
    
    # Update projects section
    if 'azure_devops' not in config_data:
        config_data['azure_devops'] = {}
    
    config_data['azure_devops']['organization'] = organization
    
    # Filter out empty projects and repositories
    valid_projects = []
    for project in projects:
        if project['name'].strip():
            valid_repos = [repo.strip() for repo in project['repositories'] if repo.strip()]
            if valid_repos:
                valid_projects.append({
                    'name': project['name'].strip(),
                    'repositories': valid_repos
                })
    
    config_data['azure_devops']['projects'] = valid_projects
    
    # Save config
    config_path.parent.mkdir(exist_ok=True)
    with open(config_path, 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
    
    # Reload configuration
    try:
        reload_config()
    except Exception:
        pass  # Config might not be complete yet


def save_analytics_config(analytics: dict, date_range: dict):
    """Save analytics configuration to YAML file"""
    config_path = Path("config/repositories.yaml")
    
    # Load existing config
    if config_path.exists():
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
    else:
        config_data = {}
    
    # Update analysis section
    if 'analysis' not in config_data:
        config_data['analysis'] = {}
    
    config_data['analysis']['date_range'] = date_range
    config_data['analysis']['include'] = analytics
    
    # Save config
    with open(config_path, 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)


def save_advanced_config(advanced: dict):
    """Save advanced configuration to YAML file"""
    config_path = Path("config/repositories.yaml")
    
    # Load existing config
    if config_path.exists():
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
    else:
        config_data = {}
    
    # Update advanced section
    config_data['advanced'] = advanced
    
    # Save config
    with open(config_path, 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False) 