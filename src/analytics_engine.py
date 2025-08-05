"""
Analytics Engine for Git Repository Data Processing
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics
from dataclasses import dataclass, asdict
from datetime import timezone

from .azure_client import AzureDevOpsClient, Commit, Branch, PullRequest, Repository
from .config import get_config
from .database import DatabaseManager, AnalyticsRequestModel


logger = logging.getLogger(__name__)


@dataclass
class AnalyticsResult:
    """Container for analytics results"""
    repository_info: Dict[str, Any]
    commit_analytics: Dict[str, Any]
    author_analytics: Dict[str, Any]
    branch_analytics: Dict[str, Any]
    code_quality: Dict[str, Any]
    file_analytics: Dict[str, Any]
    time_analytics: Dict[str, Any]
    pull_request_analytics: Dict[str, Any]
    repository_health: Dict[str, Any]
    team_analytics: Dict[str, Any]
    security_analytics: Dict[str, Any]
    performance_analytics: Dict[str, Any]
    technology_analytics: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class AnalyticsEngine:
    """Main analytics processing engine"""
    
    def __init__(self):
        """Initialize analytics engine"""
        self.config = get_config()
        self.client = AzureDevOpsClient()
        self.db_manager = DatabaseManager() if self.config.database.enabled else None
        
    async def analyze_repository(self, project: str, repository: str) -> AnalyticsResult:
        """Analyze a single repository and return comprehensive analytics"""
        logger.info(f"Starting analysis for {project}/{repository}")
        
        async with self.client:
            # Collect all data
            repo_info = await self._get_repository_info(project, repository)
            commits = await self._collect_commits(project, repository)
            branches = await self._collect_branches(project, repository)
            pull_requests = await self._collect_pull_requests(project, repository)
            
            # Store data in database if enabled
            if self.db_manager and self.config.database.auto_store:
                await self._store_repository_data(repo_info, commits, branches, pull_requests)
            
            # Run analytics
            result = AnalyticsResult(
                repository_info=repo_info,
                commit_analytics=await self._analyze_commits(commits) if self.config.is_analytics_enabled('commit_analytics') else {},
                author_analytics=await self._analyze_authors(commits) if self.config.is_analytics_enabled('author_analytics') else {},
                branch_analytics=await self._analyze_branches(branches, commits) if self.config.is_analytics_enabled('branch_analytics') else {},
                code_quality=await self._analyze_code_quality(commits) if self.config.is_analytics_enabled('code_quality') else {},
                file_analytics=await self._analyze_files(commits, project, repository) if self.config.is_analytics_enabled('file_analytics') else {},
                time_analytics=await self._analyze_time_patterns(commits, pull_requests) if self.config.is_analytics_enabled('time_analytics') else {},
                pull_request_analytics=await self._analyze_pull_requests(pull_requests) if self.config.is_analytics_enabled('pull_request_analytics') else {},
                repository_health=await self._analyze_repository_health(commits, branches, pull_requests) if self.config.is_analytics_enabled('repository_health') else {},
                team_analytics=await self._analyze_team_patterns(commits, pull_requests) if self.config.is_analytics_enabled('team_analytics') else {},
                security_analytics=await self._analyze_security_patterns(commits) if self.config.is_analytics_enabled('security_analytics') else {},
                performance_analytics=await self._analyze_performance_patterns(commits, pull_requests) if self.config.is_analytics_enabled('performance_analytics') else {},
                technology_analytics=await self._analyze_technology_patterns(commits) if self.config.is_analytics_enabled('technology_analytics') else {}
            )
            
            # Store analytics result in database if enabled
            if self.db_manager and self.config.database.auto_store:
                await self._store_analytics_result(repo_info['id'], result)
            
            logger.info(f"Completed analysis for {project}/{repository}")
            return result
    
    async def _get_repository_info(self, project: str, repository: str) -> Dict[str, Any]:
        """Get basic repository information"""
        repositories = await self.client.get_repositories(project)
        repo = next((r for r in repositories if r.name == repository), None)
        
        if not repo:
            raise ValueError(f"Repository {repository} not found in project {project}")
        
        return {
            "project": project,
            "repository": repository,
            "id": repo.id,
            "url": repo.url,
            "default_branch": repo.default_branch,
            "size": repo.size,
            "is_fork": repo.is_fork,
            "analysis_date": datetime.now().isoformat()
        }
    
    async def _collect_commits(self, project: str, repository: str) -> List[Commit]:
        """Collect all commits from repository"""
        commits = []
        async for commit in self.client.get_all_commits(project, repository):
            commits.append(commit)
        
        logger.info(f"Collected {len(commits)} commits from {project}/{repository}")
        return commits
    
    async def _collect_branches(self, project: str, repository: str) -> List[Branch]:
        """Collect all branches from repository"""
        branches = await self.client.get_branches(project, repository)
        logger.info(f"Collected {len(branches)} branches from {project}/{repository}")
        return branches
    
    async def _collect_pull_requests(self, project: str, repository: str) -> List[PullRequest]:
        """Collect all pull requests from repository"""
        pull_requests = []
        async for pr in self.client.get_all_pull_requests(project, repository):
            pull_requests.append(pr)
        
        logger.info(f"Collected {len(pull_requests)} pull requests from {project}/{repository}")
        return pull_requests
    
    async def _analyze_commits(self, commits: List[Commit]) -> Dict[str, Any]:
        """Analyze commit patterns and metrics"""
        if not commits:
            return {}
        
        # Basic statistics
        total_commits = len(commits)
        total_additions = sum(c.change_counts.get('Add', 0) for c in commits)
        total_edits = sum(c.change_counts.get('Edit', 0) for c in commits)
        total_deletions = sum(c.change_counts.get('Delete', 0) for c in commits)
        
        # Commit message analysis
        message_lengths = [len(c.message) for c in commits]
        avg_message_length = statistics.mean(message_lengths) if message_lengths else 0
        
        # Time-based patterns
        commits_by_day = defaultdict(int)
        commits_by_hour = defaultdict(int)
        
        for commit in commits:
            day_of_week = commit.author_date.strftime('%A')
            hour_of_day = commit.author_date.hour
            commits_by_day[day_of_week] += 1
            commits_by_hour[hour_of_day] += 1
        
        # Merge vs regular commits
        merge_commits = [c for c in commits if len(c.parents) > 1]
        regular_commits = [c for c in commits if len(c.parents) <= 1]
        
        # Commit frequency trends
        commits_by_month = defaultdict(int)
        for commit in commits:
            month_key = commit.author_date.strftime('%Y-%m')
            commits_by_month[month_key] += 1
        
        return {
            "total_commits": total_commits,
            "total_additions": total_additions,
            "total_edits": total_edits,
            "total_deletions": total_deletions,
            "average_message_length": avg_message_length,
            "merge_commits": len(merge_commits),
            "regular_commits": len(regular_commits),
            "merge_ratio": len(merge_commits) / total_commits if total_commits > 0 else 0,
            "commits_by_day_of_week": dict(commits_by_day),
            "commits_by_hour": dict(commits_by_hour),
            "commits_by_month": dict(sorted(commits_by_month.items())),
            "first_commit_date": min(c.author_date for c in commits).isoformat() if commits else None,
            "last_commit_date": max(c.author_date for c in commits).isoformat() if commits else None
        }
    
    async def _analyze_authors(self, commits: List[Commit]) -> Dict[str, Any]:
        """Analyze author patterns and contributions"""
        if not commits:
            return {}
        
        # Author statistics
        authors = defaultdict(lambda: {
            'commits': 0,
            'additions': 0,
            'edits': 0,
            'deletions': 0,
            'first_commit': None,
            'last_commit': None,
            'emails': set()
        })
        
        for commit in commits:
            author = commit.author_name
            if self.config.privacy.anonymize_authors:
                author = f"Author_{hash(author) % 10000}"
            
            authors[author]['commits'] += 1
            authors[author]['additions'] += commit.change_counts.get('Add', 0)
            authors[author]['edits'] += commit.change_counts.get('Edit', 0)
            authors[author]['deletions'] += commit.change_counts.get('Delete', 0)
            authors[author]['emails'].add(commit.author_email)
            
            if not authors[author]['first_commit'] or commit.author_date < authors[author]['first_commit']:
                authors[author]['first_commit'] = commit.author_date
            
            if not authors[author]['last_commit'] or commit.author_date > authors[author]['last_commit']:
                authors[author]['last_commit'] = commit.author_date
        
        # Convert to serializable format
        author_stats = {}
        for author, stats in authors.items():
            author_stats[author] = {
                'commits': stats['commits'],
                'additions': stats['additions'],
                'edits': stats['edits'],
                'deletions': stats['deletions'],
                'total_changes': stats['additions'] + stats['edits'] + stats['deletions'],
                'first_commit': stats['first_commit'].isoformat() if stats['first_commit'] else None,
                'last_commit': stats['last_commit'].isoformat() if stats['last_commit'] else None,
                'email_count': len(stats['emails'])
            }
        
        # Top contributors
        top_by_commits = sorted(author_stats.items(), key=lambda x: x[1]['commits'], reverse=True)[:10]
        top_by_changes = sorted(author_stats.items(), key=lambda x: x[1]['total_changes'], reverse=True)[:10]
        
        # Bus factor calculation (concentration of contributions)
        total_commits = len(commits)
        commit_distribution = [stats['commits'] for stats in author_stats.values()]
        
        # Calculate how many authors account for 50% and 80% of commits
        sorted_commits = sorted(commit_distribution, reverse=True)
        cumulative = 0
        bus_factor_50 = 0
        bus_factor_80 = 0
        
        for i, commits_count in enumerate(sorted_commits):
            cumulative += commits_count
            if cumulative >= total_commits * 0.5 and bus_factor_50 == 0:
                bus_factor_50 = i + 1
            if cumulative >= total_commits * 0.8 and bus_factor_80 == 0:
                bus_factor_80 = i + 1
                break
        
        return {
            "total_authors": len(author_stats),
            "author_statistics": author_stats,
            "top_contributors_by_commits": dict(top_by_commits),
            "top_contributors_by_changes": dict(top_by_changes),
            "bus_factor_50_percent": bus_factor_50,
            "bus_factor_80_percent": bus_factor_80,
            "commit_distribution": sorted_commits
        }
    
    async def _analyze_branches(self, branches: List[Branch], commits: List[Commit]) -> Dict[str, Any]:
        """Analyze branch patterns and lifecycle"""
        if not branches:
            return {}
        
        # Branch statistics
        total_branches = len(branches)
        
        # Analyze branch names for patterns
        branch_patterns = defaultdict(int)
        for branch in branches:
            if '/' in branch.name:
                prefix = branch.name.split('/')[0]
                branch_patterns[prefix] += 1
            else:
                branch_patterns['no_prefix'] += 1
        
        # Common naming conventions
        feature_branches = [b for b in branches if any(keyword in b.name.lower() for keyword in ['feature', 'feat'])]
        hotfix_branches = [b for b in branches if any(keyword in b.name.lower() for keyword in ['hotfix', 'fix', 'bug'])]
        release_branches = [b for b in branches if any(keyword in b.name.lower() for keyword in ['release', 'rel'])]
        
        return {
            "total_branches": total_branches,
            "branch_name_patterns": dict(branch_patterns),
            "feature_branches": len(feature_branches),
            "hotfix_branches": len(hotfix_branches),
            "release_branches": len(release_branches),
            "branch_names": [b.name for b in branches[:50]]  # Limit to first 50 for space
        }
    
    async def _analyze_code_quality(self, commits: List[Commit]) -> Dict[str, Any]:
        """Analyze code quality indicators"""
        if not commits:
            return {}
        
        # File change frequency (code churn)
        file_changes = defaultdict(int)
        large_commits = []
        
        for commit in commits:
            total_changes = commit.change_counts.get('Add', 0) + commit.change_counts.get('Edit', 0) + commit.change_counts.get('Delete', 0)
            
            if total_changes > 500:  # Large commit threshold
                large_commits.append({
                    'commit_id': commit.commit_id[:8],
                    'author': commit.author_name,
                    'date': commit.author_date.isoformat(),
                    'changes': total_changes,
                    'message': commit.message[:100]
                })
        
        # Code change ratios
        total_additions = sum(c.change_counts.get('Add', 0) for c in commits)
        total_deletions = sum(c.change_counts.get('Delete', 0) for c in commits)
        total_edits = sum(c.change_counts.get('Edit', 0) for c in commits)
        
        # Refactoring indicators (high delete/add ratio)
        refactoring_commits = []
        for commit in commits:
            adds = commit.change_counts.get('Add', 0)
            deletes = commit.change_counts.get('Delete', 0)
            if adds > 0 and deletes > 0 and deletes / adds > 0.5:
                refactoring_commits.append({
                    'commit_id': commit.commit_id[:8],
                    'ratio': deletes / adds,
                    'message': commit.message[:100]
                })
        
        return {
            "total_additions": total_additions,
            "total_deletions": total_deletions,
            "total_edits": total_edits,
            "delete_add_ratio": total_deletions / total_additions if total_additions > 0 else 0,
            "large_commits_count": len(large_commits),
            "large_commits": large_commits[:10],  # Top 10 largest
            "refactoring_commits_count": len(refactoring_commits),
            "refactoring_indicators": refactoring_commits[:10]
        }
    
    async def _analyze_files(self, commits: List[Commit], project: str, repository: str) -> Dict[str, Any]:
        """Analyze file patterns and changes"""
        # Note: File-level analysis would require fetching detailed commit changes
        # This is a placeholder for file analytics that could be expanded
        
        return {
            "analysis_note": "File-level analysis requires detailed commit change data",
            "total_commits_analyzed": len(commits),
            "implementation_status": "placeholder"
        }
    
    async def _analyze_time_patterns(self, commits: List[Commit], pull_requests: List[PullRequest]) -> Dict[str, Any]:
        """Analyze time-based patterns and velocity"""
        if not commits and not pull_requests:
            return {}
        
        result = {}
        
        if commits:
            # Development velocity
            commits_by_week = defaultdict(int)
            for commit in commits:
                week_key = commit.author_date.strftime('%Y-W%U')
                commits_by_week[week_key] += 1
            
            # Work patterns
            weekend_commits = sum(1 for c in commits if c.author_date.weekday() >= 5)
            weekday_commits = len(commits) - weekend_commits
            
            after_hours_commits = sum(1 for c in commits if c.author_date.hour < 9 or c.author_date.hour > 17)
            
            result.update({
                "commits_by_week": dict(sorted(commits_by_week.items())),
                "weekend_commits": weekend_commits,
                "weekday_commits": weekday_commits,
                "weekend_ratio": weekend_commits / len(commits) if commits else 0,
                "after_hours_commits": after_hours_commits,
                "after_hours_ratio": after_hours_commits / len(commits) if commits else 0
            })
        
        if pull_requests:
            # PR cycle times
            completed_prs = [pr for pr in pull_requests if pr.completed_date and pr.created_date]
            if completed_prs:
                cycle_times = [(pr.completed_date - pr.created_date).total_seconds() / 3600 for pr in completed_prs]  # Hours
                avg_cycle_time = statistics.mean(cycle_times)
                median_cycle_time = statistics.median(cycle_times)
                
                result.update({
                    "average_pr_cycle_time_hours": avg_cycle_time,
                    "median_pr_cycle_time_hours": median_cycle_time,
                    "completed_prs": len(completed_prs)
                })
        
        return result
    
    async def _analyze_pull_requests(self, pull_requests: List[PullRequest]) -> Dict[str, Any]:
        """Analyze pull request patterns"""
        if not pull_requests:
            return {}
        
        # PR status distribution
        status_counts = Counter(pr.status for pr in pull_requests)
        
        # Review patterns
        total_reviewers = sum(len(pr.reviewers) for pr in pull_requests)
        avg_reviewers = total_reviewers / len(pull_requests) if pull_requests else 0
        
        # PR size analysis (would need detailed change data)
        # This is a simplified version
        
        return {
            "total_pull_requests": len(pull_requests),
            "status_distribution": dict(status_counts),
            "average_reviewers_per_pr": avg_reviewers,
            "total_reviewers": total_reviewers
        }
    
    async def _analyze_repository_health(self, commits: List[Commit], branches: List[Branch], pull_requests: List[PullRequest]) -> Dict[str, Any]:
        """Analyze overall repository health indicators"""
        if not commits:
            return {}
        
        # Activity indicators
        now = datetime.now(timezone.utc)
        recent_commits = [c for c in commits if (now - c.author_date.replace(tzinfo=timezone.utc)).days <= 30]
        
        # Documentation indicators (basic)
        doc_commits = [c for c in commits if any(keyword in c.message.lower() for keyword in ['doc', 'readme', 'documentation'])]
        
        return {
            "recent_activity_30_days": len(recent_commits),
            "documentation_commits": len(doc_commits),
            "documentation_ratio": len(doc_commits) / len(commits) if commits else 0,
            "total_branches": len(branches),
            "total_pull_requests": len(pull_requests)
        }
    
    async def _analyze_team_patterns(self, commits: List[Commit], pull_requests: List[PullRequest]) -> Dict[str, Any]:
        """Analyze team collaboration patterns"""
        if not commits:
            return {}
        
        # Author collaboration (simplified)
        unique_authors = set(c.author_email for c in commits)
        
        return {
            "unique_contributors": len(unique_authors),
            "commits_per_contributor": len(commits) / len(unique_authors) if unique_authors else 0
        }
    
    async def _analyze_security_patterns(self, commits: List[Commit]) -> Dict[str, Any]:
        """Analyze security-related patterns"""
        if not commits:
            return {}
        
        # Security-related keywords in commit messages
        security_keywords = ['security', 'vulnerability', 'cve', 'patch', 'fix', 'auth', 'permission', 'token', 'secret']
        security_commits = []
        
        for commit in commits:
            message_lower = commit.message.lower()
            if any(keyword in message_lower for keyword in security_keywords):
                security_commits.append({
                    'commit_id': commit.commit_id[:8],
                    'author': commit.author_name,
                    'date': commit.author_date.isoformat(),
                    'message': commit.message[:100]
                })
        
        return {
            "security_related_commits": len(security_commits),
            "security_ratio": len(security_commits) / len(commits) if commits else 0,
            "recent_security_commits": security_commits[:10]
        }
    
    async def _analyze_performance_patterns(self, commits: List[Commit], pull_requests: List[PullRequest]) -> Dict[str, Any]:
        """Analyze performance-related patterns"""
        if not commits:
            return {}
        
        # Performance-related keywords
        perf_keywords = ['performance', 'optimize', 'speed', 'slow', 'fast', 'cache', 'memory', 'cpu']
        perf_commits = [c for c in commits if any(keyword in c.message.lower() for keyword in perf_keywords)]
        
        return {
            "performance_related_commits": len(perf_commits),
            "performance_ratio": len(perf_commits) / len(commits) if commits else 0
        }
    
    async def _analyze_technology_patterns(self, commits: List[Commit]) -> Dict[str, Any]:
        """Analyze technology and language patterns"""
        # This would require file extension analysis from detailed commit changes
        # Placeholder implementation
        
        return {
            "analysis_note": "Technology pattern analysis requires file change details",
            "implementation_status": "placeholder"
        }
    
    async def _store_repository_data(self, repo_info: Dict[str, Any], commits: List[Commit], 
                                   branches: List[Branch], pull_requests: List[PullRequest]):
        """Store repository data in database"""
        if not self.db_manager:
            return
        
        try:
            async with self.db_manager:
                # Create Repository object from repo_info
                repository = Repository(
                    id=repo_info['id'],
                    name=repo_info['repository'],
                    project=repo_info['project'],
                    url=repo_info['url'],
                    default_branch=repo_info['default_branch'],
                    size=repo_info['size'],
                    is_fork=repo_info['is_fork']
                )
                
                # Store repository
                await self.db_manager.store_repository(repository)
                
                # Store commits, branches, and pull requests
                await self.db_manager.store_commits(commits, repository.id)
                await self.db_manager.store_branches(branches, repository.id)
                await self.db_manager.store_pull_requests(pull_requests, repository.id)
                
                logger.info(f"Stored repository data for {repo_info['project']}/{repo_info['repository']}")
                
        except Exception as e:
            logger.error(f"Failed to store repository data: {e}")
    
    async def _store_analytics_result(self, repository_id: str, result: AnalyticsResult):
        """Store analytics result in database"""
        if not self.db_manager:
            return
        
        try:
            async with self.db_manager:
                await self.db_manager.store_analytics_result(repository_id, result)
                logger.info(f"Stored analytics result for repository {repository_id}")
                
        except Exception as e:
            logger.error(f"Failed to store analytics result: {e}")
    
    async def get_repository_from_database(self, project: str, repository: str) -> Optional[Dict[str, Any]]:
        """Get repository data from database if available"""
        if not self.db_manager:
            return None
        
        try:
            async with self.db_manager:
                repositories = await self.db_manager.get_repositories()
                for repo in repositories:
                    if repo.project == project and repo.name == repository:
                        return {
                            'id': repo.id,
                            'name': repo.name,
                            'project': repo.project,
                            'url': repo.url,
                            'default_branch': repo.default_branch,
                            'size': repo.size,
                            'is_fork': repo.is_fork,
                            'stored_at': repo.created_at.isoformat()
                        }
                return None
                
        except Exception as e:
            logger.error(f"Failed to get repository from database: {e}")
            return None
    
    async def get_stored_commits_count(self, repository_id: str) -> int:
        """Get count of stored commits for a repository"""
        if not self.db_manager:
            return 0
        
        try:
            async with self.db_manager:
                return await self.db_manager.get_commit_count(repository_id)
                
        except Exception as e:
            logger.error(f"Failed to get stored commits count: {e}")
            return 0


# Analytics Request Processing Functions

async def process_analytics_request_async(request_id: int):
    """Process an analytics request asynchronously"""
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    try:
        # Get the request
        request = await db_manager.get_analytics_request(request_id)
        if not request:
            logger.error(f"Request {request_id} not found")
            return
        
        # Update status to Running
        await db_manager.update_request_status(request_id, "Running")
        
        # Get repositories from the request
        repository_ids = request.repository_ids
        project_name = request.project_name
        
        # Initialize analytics engine
        analytics_engine = AnalyticsEngine()
        
        result_files = []
        progress_info = {"total_repos": len(repository_ids), "completed_repos": 0}
        
        # Process each repository
        for i, repo_id in enumerate(repository_ids):
            repo = await db_manager.get_repository(repo_id)
            if not repo:
                continue
            
            # Update progress
            progress_info["completed_repos"] = i
            progress_info["current_repo"] = repo.name
            await db_manager.update_request_status(request_id, "Running", progress_info=progress_info)
            
            # Run analytics for this repository
            try:
                logger.info(f"Processing analytics for {project_name}/{repo.name}")
                result = await analytics_engine.analyze_repository(project_name, repo.name)
                
                # For now, simulate file generation
                # In real implementation, this would call export functions
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                files = [
                    f"output/git_analytics_{project_name}_{repo.name}_{timestamp}.xlsx",
                    f"output/git_analytics_{project_name}_{repo.name}_{timestamp}.json",
                    f"output/summary_{project_name}_{repo.name}_{timestamp}.csv"
                ]
                result_files.extend(files)
                
            except Exception as e:
                logger.error(f"Error processing repository {repo.name}: {e}")
                # Continue with other repositories
        
        # Update final progress
        progress_info["completed_repos"] = len(repository_ids)
        
        # Update status to Completed
        await db_manager.update_request_status(
            request_id, 
            "Completed",
            progress_info=progress_info,
            result_files=result_files
        )
        
        logger.info(f"Analytics request {request_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error processing analytics request {request_id}: {e}")
        await db_manager.update_request_status(
            request_id, 
            "Failed",
            error_message=str(e)
        )
    finally:
        await db_manager.close()


# Note: The start_analytics_request_background function has been replaced
# by the AnalyticsPollingService for more reliable background processing. 