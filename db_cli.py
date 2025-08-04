#!/usr/bin/env python3
"""
Database CLI for Azure DevOps Git Repository Analytics Tool
"""

import asyncio
import argparse
import sys
import json
from pathlib import Path
from typing import Optional
import logging
from datetime import datetime

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.database import DatabaseManager, OrganizationModel, ProjectModel, RepositoryModel
from src.config import get_config
from src.analytics_engine import AnalyticsEngine


def setup_logging(level: str = "INFO"):
    """Setup logging for CLI"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


async def init_database():
    """Initialize database and create tables"""
    print("🔧 Initializing database...")
    
    async with DatabaseManager() as db:
        print("✅ Database initialized successfully")
        print(f"📍 Database location: {db.database_url}")


async def seed_database():
    """Seed database from configuration file"""
    print("🌱 Seeding database from configuration...")
    
    try:
        async with DatabaseManager() as db:
            await db.seed_from_config()
            print("✅ Database seeded successfully")
    except Exception as e:
        print(f"❌ Failed to seed database: {e}")
        return False
    return True


async def list_organizations():
    """List all organizations"""
    print("🏢 Organizations:")
    print("-" * 50)
    
    async with DatabaseManager() as db:
        organizations = await db.get_organizations()
        
        if not organizations:
            print("No organizations found")
            return
        
        for org in organizations:
            print(f"ID: {org.id}")
            print(f"Name: {org.name}")
            print(f"URL: {org.url}")
            print(f"Description: {org.description or 'N/A'}")
            print(f"Created: {org.created_at}")
            print("-" * 30)


async def list_projects(organization_name: Optional[str] = None):
    """List projects, optionally filtered by organization"""
    print("📁 Projects:")
    print("-" * 50)
    
    async with DatabaseManager() as db:
        if organization_name:
            org = await db.get_organization(organization_name)
            if not org:
                print(f"Organization '{organization_name}' not found")
                return
            projects = await db.get_projects(org.id)
        else:
            projects = await db.get_projects()
        
        if not projects:
            print("No projects found")
            return
        
        for project in projects:
            print(f"ID: {project.id}")
            print(f"Name: {project.name}")
            print(f"State: {project.state}")
            print(f"Visibility: {project.visibility}")
            print(f"Description: {project.description or 'N/A'}")
            print(f"Created: {project.created_at}")
            
            # Get repositories count
            repositories = await db.get_repositories(project.id)
            print(f"Repositories: {len(repositories)}")
            print("-" * 30)


async def list_repositories(project_name: Optional[str] = None, organization_name: Optional[str] = None):
    """List repositories, optionally filtered by project"""
    print("📂 Repositories:")
    print("-" * 50)
    
    async with DatabaseManager() as db:
        if project_name and organization_name:
            org = await db.get_organization(organization_name)
            if not org:
                print(f"Organization '{organization_name}' not found")
                return
            
            project = await db.get_project_by_name(project_name, org.id)
            if not project:
                print(f"Project '{project_name}' not found")
                return
            
            repositories = await db.get_repositories(project.id)
        else:
            repositories = await db.get_repositories()
        
        if not repositories:
            print("No repositories found")
            return
        
        for repo in repositories:
            print(f"ID: {repo.id}")
            print(f"Name: {repo.name}")
            print(f"Project ID: {repo.project_id}")
            print(f"Default Branch: {repo.default_branch}")
            print(f"Size: {repo.size} bytes")
            print(f"Is Fork: {repo.is_fork}")
            print(f"URL: {repo.url}")
            print(f"Created: {repo.created_at}")
            print("-" * 30)


async def add_organization(name: str, url: str, description: str = None):
    """Add a new organization"""
    print(f"➕ Adding organization: {name}")
    
    async with DatabaseManager() as db:
        try:
            org = await db.store_organization(name, url, description)
            print(f"✅ Organization added with ID: {org.id}")
        except Exception as e:
            print(f"❌ Failed to add organization: {e}")


async def add_project(project_id: str, name: str, organization_name: str, description: str = None):
    """Add a new project"""
    print(f"➕ Adding project: {name}")
    
    async with DatabaseManager() as db:
        try:
            # Get organization
            org = await db.get_organization(organization_name)
            if not org:
                print(f"❌ Organization '{organization_name}' not found")
                return
            
            project = await db.store_project(project_id, name, org.id, description)
            print(f"✅ Project added with ID: {project.id}")
        except Exception as e:
            print(f"❌ Failed to add project: {e}")


async def show_database_info():
    """Show database information and statistics"""
    print("="*50)
    print("📊 DATABASE INFORMATION")
    print("="*50)
    
    async with DatabaseManager() as db:
        print(f"📍 Database URL: {db.database_url}")
        
        # Get statistics
        organizations = await db.get_organizations()
        projects = await db.get_projects()
        repositories = await db.get_repositories()
        
        print(f"🏢 Organizations: {len(organizations)}")
        print(f"📁 Projects: {len(projects)}")
        print(f"📂 Repositories: {len(repositories)}")
        
        if repositories:
            total_commits = 0
            for repo in repositories:
                commit_count = await db.get_commit_count(repo.id)
                total_commits += commit_count
            print(f"📝 Total Commits: {total_commits}")
        
        print("\n📈 Recent Activity:")
        if repositories:
            # Show most recently updated repositories
            recent_repos = sorted(repositories, key=lambda r: r.updated_at, reverse=True)[:5]
            for repo in recent_repos:
                print(f"  • {repo.project_id}/{repo.name} - {repo.updated_at.strftime('%Y-%m-%d %H:%M')}")


async def show_repository_details(project_id: str, repository: str):
    """Show detailed information about a specific repository"""
    async with DatabaseManager() as db:
        repositories = await db.get_repositories()
        repo = None
        
        for r in repositories:
            if r.project_id == project_id and r.name == repository:
                repo = r
                break
        
        if not repo:
            print(f"❌ Repository '{project_id}/{repository}' not found")
            return
        
        print("="*50)
        print(f"📂 REPOSITORY DETAILS: {repo.name}")
        print("="*50)
        print(f"ID: {repo.id}")
        print(f"Name: {repo.name}")
        print(f"Project ID: {repo.project_id}")
        print(f"URL: {repo.url}")
        print(f"Default Branch: {repo.default_branch}")
        print(f"Size: {repo.size} bytes")
        print(f"Is Fork: {repo.is_fork}")
        print(f"Created: {repo.created_at}")
        print(f"Updated: {repo.updated_at}")
        
        # Get commit statistics
        commit_count = await db.get_commit_count(repo.id)
        print(f"\n📝 Commits: {commit_count}")
        
        if commit_count > 0:
            commits = await db.get_commits(repo.id, limit=5)
            print(f"\n📅 Recent Commits:")
            for commit in commits:
                print(f"  • {commit.commit_id[:8]} - {commit.author_name} - {commit.author_date.strftime('%Y-%m-%d')}")
                print(f"    {commit.message[:80]}...")
        
        # Get author statistics
        authors = await db.get_author_statistics(repo.id)
        if authors:
            print(f"\n👥 Top Authors:")
            sorted_authors = sorted(authors.items(), key=lambda x: x[1]['commit_count'], reverse=True)[:5]
            for author, stats in sorted_authors:
                print(f"  • {author}: {stats['commit_count']} commits")


async def export_repository_data(project: str, repository: str, output_file: str):
    """Export repository data to JSON"""
    db_manager = DatabaseManager()
    async with db_manager:
        repositories = await db_manager.get_repositories()
        repo = None
        
        for r in repositories:
            if r.project == project and r.name == repository:
                repo = r
                break
        
        if not repo:
            print(f"Repository {project}/{repository} not found in database")
            return
        
        print(f"Exporting data for {project}/{repository}...")
        
        # Get all data
        commits = await db_manager.get_commits(repo.id)
        analytics_result = await db_manager.get_latest_analytics_result(repo.id)
        
        export_data = {
            "repository": {
                "id": repo.id,
                "name": repo.name,
                "project": repo.project,
                "url": repo.url,
                "default_branch": repo.default_branch,
                "size": repo.size,
                "is_fork": repo.is_fork,
                "created_at": repo.created_at.isoformat(),
                "updated_at": repo.updated_at.isoformat()
            },
            "commits": [
                {
                    "commit_id": commit.commit_id,
                    "author_name": commit.author_name,
                    "author_email": commit.author_email,
                    "author_date": commit.author_date.isoformat(),
                    "committer_name": commit.committer_name,
                    "committer_email": commit.committer_email,
                    "committer_date": commit.committer_date.isoformat(),
                    "message": commit.message,
                    "change_counts": commit.change_counts,
                    "parents": commit.parents,
                    "url": commit.url
                }
                for commit in commits
            ],
            "analytics": analytics_result.to_dict() if analytics_result else None,
            "export_date": datetime.utcnow().isoformat()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Data exported to {output_file}")
        print(f"  Repository: {repo.project}/{repo.name}")
        print(f"  Commits: {len(commits)}")
        print(f"  Analytics: {'Yes' if analytics_result else 'No'}")


async def cleanup_old_data(days: int):
    """Clean up old analytics results"""
    print(f"🧹 Cleaning up data older than {days} days...")
    
    async with DatabaseManager() as db:
        try:
            deleted_count = await db.cleanup_old_data(days)
            if deleted_count > 0:
                print(f"✅ Cleaned up {deleted_count} old analytics results")
            else:
                print("ℹ️ No old data found to clean up")
        except Exception as e:
            print(f"❌ Failed to clean up data: {e}")


async def reanalyze_repository(project: str, repository: str):
    """Re-analyze a repository using stored data"""
    print(f"Re-analyzing repository {project}/{repository} from database...")
    
    analytics_engine = AnalyticsEngine()
    
    # Check if repository exists in database
    repo_data = await analytics_engine.get_repository_from_database(project, repository)
    if not repo_data:
        print(f"Repository {project}/{repository} not found in database")
        print("Run the main analytics tool first to collect data")
        return
    
    # Get stored commits count
    stored_commits = await analytics_engine.get_stored_commits_count(repo_data['id'])
    print(f"Found {stored_commits} commits in database")
    
    if stored_commits == 0:
        print("No commits found in database. Run data collection first.")
        return
    
    print("Re-analysis from database is not yet implemented.")
    print("This feature would analyze stored data without fetching from API.")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Database CLI for Azure DevOps Git Repository Analytics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s init                           # Initialize database
  %(prog)s seed                           # Seed database from config
  %(prog)s info                           # Show database information
  %(prog)s list orgs                      # List organizations
  %(prog)s list projects                  # List projects
  %(prog)s list repos                     # List repositories
  %(prog)s add org "MyOrg" "https://dev.azure.com/myorg"
  %(prog)s add project "MyProject" "MyProjectID" "MyOrg"
  %(prog)s show repo "MyProject" "MyRepo" # Show repository details
  %(prog)s cleanup                        # Clean up old data
        """
    )
    
    parser.add_argument("--log-level", default="INFO", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Set logging level")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Init command
    subparsers.add_parser("init", help="Initialize database")
    
    # Seed command
    subparsers.add_parser("seed", help="Seed database from configuration")
    
    # Info command
    subparsers.add_parser("info", help="Show database information")
    
    # List commands
    list_parser = subparsers.add_parser("list", help="List database entities")
    list_subparsers = list_parser.add_subparsers(dest="list_type", help="What to list")
    
    list_subparsers.add_parser("orgs", help="List organizations")
    
    projects_parser = list_subparsers.add_parser("projects", help="List projects")
    projects_parser.add_argument("--org", help="Filter by organization name")
    
    repos_parser = list_subparsers.add_parser("repos", help="List repositories")
    repos_parser.add_argument("--project", help="Filter by project name")
    repos_parser.add_argument("--org", help="Organization name (required with --project)")
    
    # Add commands
    add_parser = subparsers.add_parser("add", help="Add database entities")
    add_subparsers = add_parser.add_subparsers(dest="add_type", help="What to add")
    
    org_parser = add_subparsers.add_parser("org", help="Add organization")
    org_parser.add_argument("name", help="Organization name")
    org_parser.add_argument("url", help="Organization URL")
    org_parser.add_argument("--description", help="Organization description")
    
    project_parser = add_subparsers.add_parser("project", help="Add project")
    project_parser.add_argument("name", help="Project name")
    project_parser.add_argument("project_id", help="Project ID")
    project_parser.add_argument("organization", help="Organization name")
    project_parser.add_argument("--description", help="Project description")
    
    # Show command
    show_parser = subparsers.add_parser("show", help="Show detailed information")
    show_subparsers = show_parser.add_subparsers(dest="show_type", help="What to show")
    
    repo_parser = show_subparsers.add_parser("repo", help="Show repository details")
    repo_parser.add_argument("project", help="Project name or ID")
    repo_parser.add_argument("repository", help="Repository name")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old data")
    cleanup_parser.add_argument("--days", type=int, default=90,
                               help="Keep data newer than this many days")
    
    args = parser.parse_args()
    
    setup_logging(args.log_level)
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == "init":
            return asyncio.run(init_database()) or 0
        elif args.command == "seed":
            success = asyncio.run(seed_database())
            return 0 if success else 1
        elif args.command == "info":
            return asyncio.run(show_database_info()) or 0
        elif args.command == "list":
            if args.list_type == "orgs":
                return asyncio.run(list_organizations()) or 0
            elif args.list_type == "projects":
                return asyncio.run(list_projects(args.org)) or 0
            elif args.list_type == "repos":
                return asyncio.run(list_repositories(args.project, args.org)) or 0
            else:
                print("❌ Please specify what to list: orgs, projects, or repos")
                return 1
        elif args.command == "add":
            if args.add_type == "org":
                return asyncio.run(add_organization(args.name, args.url, args.description)) or 0
            elif args.add_type == "project":
                return asyncio.run(add_project(args.project_id, args.name, args.organization, args.description)) or 0
            else:
                print("❌ Please specify what to add: org or project")
                return 1
        elif args.command == "show":
            if args.show_type == "repo":
                return asyncio.run(show_repository_details(args.project, args.repository)) or 0
            else:
                print("❌ Please specify what to show: repo")
                return 1
        elif args.command == "cleanup":
            return asyncio.run(cleanup_old_data(args.days)) or 0
        else:
            print(f"❌ Unknown command: {args.command}")
            return 1
            
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 