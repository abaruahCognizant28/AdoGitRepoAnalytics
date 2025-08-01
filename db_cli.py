#!/usr/bin/env python3
"""
Database CLI tool for Azure DevOps Git Repository Analytics
"""

import sys
import asyncio
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import json

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.database import DatabaseManager
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
    print("Initializing database...")
    
    db_manager = DatabaseManager()
    async with db_manager:
        print("✓ Database initialized successfully")
        print(f"Database location: {db_manager.database_url}")


async def show_database_info():
    """Show database information and statistics"""
    db_manager = DatabaseManager()
    async with db_manager:
        repositories = await db_manager.get_repositories()
        
        print("="*50)
        print("DATABASE INFORMATION")
        print("="*50)
        print(f"Database URL: {db_manager.database_url}")
        print(f"Total Repositories: {len(repositories)}")
        
        if repositories:
            print("\nRepositories:")
            for repo in repositories:
                commit_count = await db_manager.get_commit_count(repo.id)
                print(f"  • {repo.project}/{repo.name}")
                print(f"    ID: {repo.id}")
                print(f"    Commits: {commit_count}")
                print(f"    Created: {repo.created_at}")
                print(f"    Updated: {repo.updated_at}")
                print()


async def list_repositories():
    """List all repositories in database"""
    db_manager = DatabaseManager()
    async with db_manager:
        repositories = await db_manager.get_repositories()
        
        if not repositories:
            print("No repositories found in database")
            return
        
        print(f"Found {len(repositories)} repositories:")
        print()
        
        for repo in repositories:
            commit_count = await db_manager.get_commit_count(repo.id)
            print(f"Repository: {repo.project}/{repo.name}")
            print(f"  ID: {repo.id}")
            print(f"  URL: {repo.url}")
            print(f"  Default Branch: {repo.default_branch}")
            print(f"  Size: {repo.size} bytes")
            print(f"  Is Fork: {repo.is_fork}")
            print(f"  Commits Stored: {commit_count}")
            print(f"  Last Updated: {repo.updated_at}")
            print()


async def show_repository_details(project: str, repository: str):
    """Show detailed information about a specific repository"""
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
        
        print(f"Repository Details: {project}/{repository}")
        print("="*50)
        print(f"ID: {repo.id}")
        print(f"URL: {repo.url}")
        print(f"Default Branch: {repo.default_branch}")
        print(f"Size: {repo.size} bytes")
        print(f"Is Fork: {repo.is_fork}")
        print(f"Created: {repo.created_at}")
        print(f"Updated: {repo.updated_at}")
        
        # Get commit statistics
        commit_count = await db_manager.get_commit_count(repo.id)
        print(f"\nCommits: {commit_count}")
        
        if commit_count > 0:
            commits = await db_manager.get_commits(repo.id, limit=10)
            print("\nRecent Commits (last 10):")
            for commit in commits:
                print(f"  • {commit.commit_id[:8]} - {commit.author_name}")
                print(f"    {commit.message[:80]}...")
                print(f"    Date: {commit.author_date}")
                print()
        
        # Get author statistics
        author_stats = await db_manager.get_author_statistics(repo.id)
        if author_stats:
            print(f"\nAuthors ({len(author_stats)}):")
            for author, stats in list(author_stats.items())[:10]:
                print(f"  • {author}: {stats['commit_count']} commits")
        
        # Get latest analytics result
        analytics_result = await db_manager.get_latest_analytics_result(repo.id)
        if analytics_result:
            print(f"\nLatest Analytics: {analytics_result.analysis_date}")
            if analytics_result.commit_analytics:
                total_commits = analytics_result.commit_analytics.get('total_commits', 0)
                total_authors = analytics_result.author_analytics.get('total_authors', 0)
                print(f"  Total Commits Analyzed: {total_commits}")
                print(f"  Total Authors: {total_authors}")


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
    print(f"Cleaning up analytics results older than {days} days...")
    
    db_manager = DatabaseManager()
    async with db_manager:
        deleted_count = await db_manager.cleanup_old_data(days)
        print(f"✓ Cleaned up {deleted_count} old analytics results")


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
  %(prog)s init                                    # Initialize database
  %(prog)s info                                    # Show database info
  %(prog)s list                                    # List all repositories
  %(prog)s show MyProject MyRepo                   # Show repository details
  %(prog)s export MyProject MyRepo data.json      # Export repository data
  %(prog)s cleanup 30                              # Clean up data older than 30 days
  %(prog)s reanalyze MyProject MyRepo              # Re-analyze from stored data
        """
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Init command
    subparsers.add_parser("init", help="Initialize database and create tables")
    
    # Info command
    subparsers.add_parser("info", help="Show database information and statistics")
    
    # List command
    subparsers.add_parser("list", help="List all repositories in database")
    
    # Show command
    show_parser = subparsers.add_parser("show", help="Show detailed repository information")
    show_parser.add_argument("project", help="Project name")
    show_parser.add_argument("repository", help="Repository name")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export repository data to JSON")
    export_parser.add_argument("project", help="Project name")
    export_parser.add_argument("repository", help="Repository name")
    export_parser.add_argument("output", help="Output JSON file path")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old analytics results")
    cleanup_parser.add_argument("days", type=int, help="Number of days to keep (default: 90)")
    
    # Reanalyze command
    reanalyze_parser = subparsers.add_parser("reanalyze", help="Re-analyze repository from stored data")
    reanalyze_parser.add_argument("project", help="Project name")
    reanalyze_parser.add_argument("repository", help="Repository name")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == "init":
            asyncio.run(init_database())
        elif args.command == "info":
            asyncio.run(show_database_info())
        elif args.command == "list":
            asyncio.run(list_repositories())
        elif args.command == "show":
            asyncio.run(show_repository_details(args.project, args.repository))
        elif args.command == "export":
            asyncio.run(export_repository_data(args.project, args.repository, args.output))
        elif args.command == "cleanup":
            asyncio.run(cleanup_old_data(args.days))
        elif args.command == "reanalyze":
            asyncio.run(reanalyze_repository(args.project, args.repository))
        
        return 0
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        logging.exception("Unexpected error occurred")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 