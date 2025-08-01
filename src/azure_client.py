"""
Azure DevOps API Client for Git Repository Analytics
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime, timezone
import base64
import json
from urllib.parse import quote

from .config import get_config


logger = logging.getLogger(__name__)


@dataclass
class Commit:
    """Commit information"""
    commit_id: str
    author_name: str
    author_email: str
    author_date: datetime
    committer_name: str
    committer_email: str
    committer_date: datetime
    message: str
    change_counts: Dict[str, int]  # {"add": 0, "edit": 0, "delete": 0}
    parents: List[str]
    url: str
    changes: List[Dict[str, Any]] = None


@dataclass
class Branch:
    """Branch information"""
    name: str
    object_id: str
    creator: Optional[str]
    url: str
    is_default: bool = False


@dataclass
class PullRequest:
    """Pull request information"""
    pull_request_id: int
    title: str
    description: str
    source_branch: str
    target_branch: str
    author: str
    created_date: datetime
    closed_date: Optional[datetime]
    completed_date: Optional[datetime]
    status: str
    merge_status: str
    reviewers: List[Dict[str, Any]]
    url: str


@dataclass
class Repository:
    """Repository information"""
    id: str
    name: str
    project: str
    url: str
    default_branch: str
    size: int
    is_fork: bool = False


class AzureDevOpsClient:
    """Azure DevOps REST API Client"""
    
    def __init__(self):
        """Initialize the Azure DevOps client"""
        self.config = get_config()
        self.base_url = self.config.get_azure_devops_url()
        self.organization = self.config.organization
        
        # Setup authentication
        self.auth_header = self._create_auth_header()
        
        # Setup session configuration
        self.timeout = aiohttp.ClientTimeout(total=self.config.api.timeout)
        self.connector = aiohttp.TCPConnector(limit=self.config.max_concurrent_requests)
        
        self._session: Optional[aiohttp.ClientSession] = None
    
    def _create_auth_header(self) -> str:
        """Create authentication header for Azure DevOps API"""
        token = self.config.azure_pat
        auth_string = base64.b64encode(f":{token}".encode()).decode()
        return f"Basic {auth_string}"
    
    async def __aenter__(self):
        """Async context manager entry"""
        self._session = aiohttp.ClientSession(
            timeout=self.timeout,
            connector=self.connector,
            headers={
                "Authorization": self.auth_header,
                "Content-Type": "application/json",
                "User-Agent": self.config.user_agent
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._session:
            await self._session.close()
    
    async def _make_request(self, url: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make authenticated request to Azure DevOps API"""
        if not self._session:
            raise RuntimeError("Client session not initialized. Use async context manager.")
        
        for attempt in range(self.config.api.retry_attempts):
            try:
                logger.debug(f"Making request to: {url}")
                
                async with self._session.get(url, params=params) as response:
                    if response.status == 429:  # Rate limit
                        await asyncio.sleep(self.config.api.rate_limit_delay * (attempt + 1))
                        continue
                    
                    response.raise_for_status()
                    data = await response.json()
                    
                    # Rate limiting
                    await asyncio.sleep(self.config.api.rate_limit_delay)
                    
                    return data
                    
            except aiohttp.ClientError as e:
                logger.warning(f"Request attempt {attempt + 1} failed: {e}")
                if attempt == self.config.api.retry_attempts - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        raise RuntimeError(f"Failed to make request after {self.config.api.retry_attempts} attempts")
    
    async def get_repositories(self, project: str) -> List[Repository]:
        """Get all repositories in a project"""
        url = f"{self.base_url}/{quote(project)}/_apis/git/repositories"
        params = {"api-version": "6.0"}
        
        data = await self._make_request(url, params)
        
        repositories = []
        for repo_data in data.get("value", []):
            repositories.append(Repository(
                id=repo_data["id"],
                name=repo_data["name"],
                project=project,
                url=repo_data["webUrl"],
                default_branch=repo_data.get("defaultBranch", "refs/heads/main"),
                size=repo_data.get("size", 0),
                is_fork=repo_data.get("isFork", False)
            ))
        
        return repositories
    
    async def get_commits(self, project: str, repository: str, 
                         branch: str = None, top: int = 100, 
                         skip: int = 0) -> List[Commit]:
        """Get commits from a repository"""
        url = f"{self.base_url}/{quote(project)}/_apis/git/repositories/{quote(repository)}/commits"
        
        params = {
            "api-version": "6.0",
            "$top": top,
            "$skip": skip,
            "includeStatuses": "true"
        }
        
        if branch:
            params["searchCriteria.itemVersion.version"] = branch
        
        # Add date range if configured
        if self.config.date_range.start_date:
            params["searchCriteria.fromDate"] = self.config.date_range.start_date
        if self.config.date_range.end_date:
            params["searchCriteria.toDate"] = self.config.date_range.end_date
        
        data = await self._make_request(url, params)
        
        commits = []
        for commit_data in data.get("value", []):
            commit = Commit(
                commit_id=commit_data["commitId"],
                author_name=commit_data["author"]["name"],
                author_email=commit_data["author"]["email"],
                author_date=datetime.fromisoformat(commit_data["author"]["date"].replace("Z", "+00:00")),
                committer_name=commit_data["committer"]["name"],
                committer_email=commit_data["committer"]["email"],
                committer_date=datetime.fromisoformat(commit_data["committer"]["date"].replace("Z", "+00:00")),
                message=commit_data["comment"],
                change_counts=commit_data.get("changeCounts", {"Add": 0, "Edit": 0, "Delete": 0}),
                parents=[parent["commitId"] for parent in commit_data.get("parents", [])],
                url=commit_data["url"]
            )
            commits.append(commit)
        
        return commits
    
    async def get_commit_changes(self, project: str, repository: str, commit_id: str) -> List[Dict[str, Any]]:
        """Get detailed changes for a specific commit"""
        url = f"{self.base_url}/{quote(project)}/_apis/git/repositories/{quote(repository)}/commits/{commit_id}/changes"
        params = {"api-version": "6.0"}
        
        data = await self._make_request(url, params)
        return data.get("changes", [])
    
    async def get_branches(self, project: str, repository: str) -> List[Branch]:
        """Get all branches in a repository"""
        url = f"{self.base_url}/{quote(project)}/_apis/git/repositories/{quote(repository)}/refs"
        params = {
            "api-version": "6.0",
            "filter": "heads/"
        }
        
        data = await self._make_request(url, params)
        
        branches = []
        for ref_data in data.get("value", []):
            branch_name = ref_data["name"].replace("refs/heads/", "")
            branches.append(Branch(
                name=branch_name,
                object_id=ref_data["objectId"],
                creator=ref_data.get("creator", {}).get("displayName"),
                url=ref_data["url"]
            ))
        
        return branches
    
    async def get_pull_requests(self, project: str, repository: str, 
                               status: str = "all", top: int = 100, 
                               skip: int = 0) -> List[PullRequest]:
        """Get pull requests from a repository"""
        url = f"{self.base_url}/{quote(project)}/_apis/git/repositories/{quote(repository)}/pullrequests"
        
        params = {
            "api-version": "6.0",
            "searchCriteria.status": status,
            "$top": top,
            "$skip": skip
        }
        
        data = await self._make_request(url, params)
        
        pull_requests = []
        for pr_data in data.get("value", []):
            created_date = datetime.fromisoformat(pr_data["creationDate"].replace("Z", "+00:00"))
            closed_date = None
            completed_date = None
            
            if pr_data.get("closedDate"):
                closed_date = datetime.fromisoformat(pr_data["closedDate"].replace("Z", "+00:00"))
            
            if pr_data.get("completionQueueTime"):
                completed_date = datetime.fromisoformat(pr_data["completionQueueTime"].replace("Z", "+00:00"))
            
            pull_request = PullRequest(
                pull_request_id=pr_data["pullRequestId"],
                title=pr_data["title"],
                description=pr_data.get("description", ""),
                source_branch=pr_data["sourceRefName"],
                target_branch=pr_data["targetRefName"],
                author=pr_data["createdBy"]["displayName"],
                created_date=created_date,
                closed_date=closed_date,
                completed_date=completed_date,
                status=pr_data["status"],
                merge_status=pr_data.get("mergeStatus", ""),
                reviewers=[{
                    "name": reviewer["displayName"],
                    "vote": reviewer.get("vote", 0),
                    "isRequired": reviewer.get("isRequired", False)
                } for reviewer in pr_data.get("reviewers", [])],
                url=pr_data["url"]
            )
            pull_requests.append(pull_request)
        
        return pull_requests
    
    async def get_all_commits(self, project: str, repository: str, 
                             branch: str = None) -> AsyncGenerator[Commit, None]:
        """Get all commits from a repository with pagination"""
        skip = 0
        batch_size = self.config.processing.batch_size
        
        while True:
            commits = await self.get_commits(project, repository, branch, batch_size, skip)
            
            if not commits:
                break
            
            for commit in commits:
                yield commit
            
            if len(commits) < batch_size:
                break
            
            skip += batch_size
    
    async def get_all_pull_requests(self, project: str, repository: str) -> AsyncGenerator[PullRequest, None]:
        """Get all pull requests from a repository with pagination"""
        skip = 0
        batch_size = self.config.processing.batch_size
        
        while True:
            prs = await self.get_pull_requests(project, repository, "all", batch_size, skip)
            
            if not prs:
                break
            
            for pr in prs:
                yield pr
            
            if len(prs) < batch_size:
                break
            
            skip += batch_size 