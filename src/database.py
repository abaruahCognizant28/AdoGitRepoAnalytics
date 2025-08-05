"""
Database models and manager for Azure DevOps Git Repository Analytics
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime, timedelta
from pathlib import Path
import json

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Float
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, selectinload
from sqlalchemy.sql import select, delete, update, func
from sqlalchemy import and_, or_, desc

from .azure_client import Commit, Branch, PullRequest, Repository
from .config import get_config

logger = logging.getLogger(__name__)

Base = declarative_base()


class OrganizationModel(Base):
    """Database model for Azure DevOps Organization"""
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    url = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    projects = relationship("ProjectModel", back_populates="organization", cascade="all, delete-orphan")


class ProjectModel(Base):
    """Database model for Azure DevOps Project"""
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True)  # Azure DevOps project ID
    name = Column(String, nullable=False)
    description = Column(Text)
    state = Column(String, default="wellFormed")  # wellFormed, createPending, deleting, etc.
    visibility = Column(String, default="private")  # private, public
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("OrganizationModel", back_populates="projects")
    repositories = relationship("RepositoryModel", back_populates="project", cascade="all, delete-orphan")


class RepositoryModel(Base):
    """Database model for Repository"""
    __tablename__ = "repositories"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    url = Column(String, nullable=False)
    default_branch = Column(String, nullable=False)
    size = Column(Integer, default=0)
    is_fork = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("ProjectModel", back_populates="repositories")
    commits = relationship("CommitModel", back_populates="repository", cascade="all, delete-orphan")
    branches = relationship("BranchModel", back_populates="repository", cascade="all, delete-orphan")
    pull_requests = relationship("PullRequestModel", back_populates="repository", cascade="all, delete-orphan")
    
    @classmethod
    def from_dataclass(cls, repo: Repository, project_id: str) -> "RepositoryModel":
        """Create model instance from dataclass"""
        return cls(
            id=repo.id,
            name=repo.name,
            project_id=project_id,
            url=repo.url,
            default_branch=repo.default_branch,
            size=repo.size,
            is_fork=repo.is_fork
        )


class BranchModel(Base):
    """Database model for Branch"""
    __tablename__ = "branches"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    object_id = Column(String, nullable=False)
    creator = Column(String)
    url = Column(String, nullable=False)
    is_default = Column(Boolean, default=False)
    repository_id = Column(String, ForeignKey("repositories.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    repository = relationship("RepositoryModel", back_populates="branches")
    
    @classmethod
    def from_dataclass(cls, branch: Branch, repository_id: str) -> "BranchModel":
        """Create model instance from dataclass"""
        return cls(
            name=branch.name,
            object_id=branch.object_id,
            creator=branch.creator,
            url=branch.url,
            is_default=branch.is_default,
            repository_id=repository_id
        )


class CommitModel(Base):
    """Database model for Commit"""
    __tablename__ = "commits"
    
    commit_id = Column(String, primary_key=True)
    author_name = Column(String, nullable=False)
    author_email = Column(String, nullable=False)
    author_date = Column(DateTime, nullable=False)
    committer_name = Column(String, nullable=False)
    committer_email = Column(String, nullable=False)
    committer_date = Column(DateTime, nullable=False)
    message = Column(Text, nullable=False)
    change_counts = Column(JSON)  # Store as JSON: {"Add": 0, "Edit": 0, "Delete": 0}
    parents = Column(JSON)  # Store parent commit IDs as JSON list
    url = Column(String, nullable=False)
    changes = Column(JSON)  # Store detailed changes as JSON
    repository_id = Column(String, ForeignKey("repositories.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    repository = relationship("RepositoryModel", back_populates="commits")
    
    @classmethod
    def from_dataclass(cls, commit: Commit, repository_id: str) -> "CommitModel":
        """Create model instance from dataclass"""
        return cls(
            commit_id=commit.commit_id,
            author_name=commit.author_name,
            author_email=commit.author_email,
            author_date=commit.author_date,
            committer_name=commit.committer_name,
            committer_email=commit.committer_email,
            committer_date=commit.committer_date,
            message=commit.message,
            change_counts=commit.change_counts,
            parents=commit.parents,
            url=commit.url,
            changes=commit.changes,
            repository_id=repository_id
        )


class PullRequestModel(Base):
    """Database model for Pull Request"""
    __tablename__ = "pull_requests"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pull_request_id = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    source_branch = Column(String, nullable=False)
    target_branch = Column(String, nullable=False)
    author = Column(String, nullable=False)
    created_date = Column(DateTime, nullable=False)
    closed_date = Column(DateTime)
    completed_date = Column(DateTime)
    status = Column(String, nullable=False)
    merge_status = Column(String)
    reviewers = Column(JSON)  # Store reviewers as JSON list
    url = Column(String, nullable=False)
    repository_id = Column(String, ForeignKey("repositories.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    repository = relationship("RepositoryModel", back_populates="pull_requests")
    
    @classmethod
    def from_dataclass(cls, pr: PullRequest, repository_id: str) -> "PullRequestModel":
        """Create model instance from dataclass"""
        return cls(
            pull_request_id=pr.pull_request_id,
            title=pr.title,
            description=pr.description,
            source_branch=pr.source_branch,
            target_branch=pr.target_branch,
            author=pr.author,
            created_date=pr.created_date,
            closed_date=pr.closed_date,
            completed_date=pr.completed_date,
            status=pr.status,
            merge_status=pr.merge_status,
            reviewers=pr.reviewers,
            url=pr.url,
            repository_id=repository_id
        )


class AnalyticsRequestModel(Base):
    """Database model for tracking analytics requests"""
    __tablename__ = "analytics_requests"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_name = Column(String, nullable=False)
    repository_ids = Column(JSON, nullable=False)  # List of repository IDs
    status = Column(String, nullable=False, default="Requested")  # Requested, Running, Completed, Failed
    requested_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    started_date = Column(DateTime)
    completed_date = Column(DateTime)
    error_message = Column(Text)
    progress_info = Column(JSON)  # Store progress information
    result_files = Column(JSON)  # Store paths to generated files
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AnalyticsResultModel(Base):
    """Database model for storing analytics results"""
    __tablename__ = "analytics_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    repository_id = Column(String, ForeignKey("repositories.id"), nullable=False)
    analysis_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    commit_analytics = Column(JSON)
    author_analytics = Column(JSON)
    branch_analytics = Column(JSON)
    code_quality = Column(JSON)
    file_analytics = Column(JSON)
    time_analytics = Column(JSON)
    pull_request_analytics = Column(JSON)
    repository_health = Column(JSON)
    team_analytics = Column(JSON)
    security_analytics = Column(JSON)
    performance_analytics = Column(JSON)
    technology_analytics = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    repository = relationship("RepositoryModel")


class DatabaseManager:
    """Database manager for handling all database operations"""
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize database manager"""
        self.config = get_config()
        self.database_url = database_url or self._get_database_url()
        self.engine = None
        self.async_session_maker = None
        self.logger = logging.getLogger(__name__)
    
    def _get_database_url(self) -> str:
        """Get database URL from configuration"""
        db_config = getattr(self.config, 'database', None)
        if db_config and hasattr(db_config, 'url') and db_config.url:
            return db_config.url
        
        # Default to SQLite in output directory
        db_path = self.config.get_output_path("analytics.db")
        return f"sqlite+aiosqlite:///{db_path}"
    
    async def initialize(self):
        """Initialize database connection and create tables"""
        self.logger.info(f"Initializing database: {self.database_url}")
        
        self.engine = create_async_engine(
            self.database_url,
            echo=False,  # Set to True for SQL debugging
            pool_pre_ping=True
        )
        
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        self.logger.info("Database initialized successfully")
    
    async def close(self):
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()
            self.logger.info("Database connection closed")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    # Organization CRUD operations
    async def store_organization(self, name: str, url: str, description: str = None) -> OrganizationModel:
        """Store or update organization data"""
        async with self.async_session_maker() as session:
            # Check if organization already exists
            result = await session.execute(
                select(OrganizationModel).where(OrganizationModel.name == name)
            )
            existing_org = result.scalar_one_or_none()
            
            if existing_org:
                # Update existing organization
                existing_org.url = url
                existing_org.description = description
                existing_org.updated_at = datetime.utcnow()
                org_model = existing_org
            else:
                # Create new organization
                org_model = OrganizationModel(
                    name=name,
                    url=url,
                    description=description
                )
                session.add(org_model)
            
            await session.commit()
            await session.refresh(org_model)
            return org_model
    
    async def get_organization(self, name: str) -> Optional[OrganizationModel]:
        """Get organization by name"""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(OrganizationModel).where(OrganizationModel.name == name)
            )
            return result.scalar_one_or_none()
    
    async def get_organizations(self) -> List[OrganizationModel]:
        """Get all organizations"""
        async with self.async_session_maker() as session:
            result = await session.execute(select(OrganizationModel))
            return result.scalars().all()
    
    # Project CRUD operations
    async def store_project(self, project_id: str, name: str, organization_id: int, 
                           description: str = None, state: str = "wellFormed", 
                           visibility: str = "private") -> ProjectModel:
        """Store or update project data"""
        async with self.async_session_maker() as session:
            # Check if project already exists
            result = await session.execute(
                select(ProjectModel).where(ProjectModel.id == project_id)
            )
            existing_project = result.scalar_one_or_none()
            
            if existing_project:
                # Update existing project
                existing_project.name = name
                existing_project.description = description
                existing_project.state = state
                existing_project.visibility = visibility
                existing_project.organization_id = organization_id
                existing_project.updated_at = datetime.utcnow()
                project_model = existing_project
            else:
                # Create new project
                project_model = ProjectModel(
                    id=project_id,
                    name=name,
                    description=description,
                    state=state,
                    visibility=visibility,
                    organization_id=organization_id
                )
                session.add(project_model)
            
            await session.commit()
            await session.refresh(project_model)
            return project_model
    
    async def get_project(self, project_id: str) -> Optional[ProjectModel]:
        """Get project by ID"""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(ProjectModel).where(ProjectModel.id == project_id)
            )
            return result.scalar_one_or_none()
    
    async def get_project_by_name(self, name: str, organization_id: int) -> Optional[ProjectModel]:
        """Get project by name within an organization"""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(ProjectModel).where(
                    and_(ProjectModel.name == name, ProjectModel.organization_id == organization_id)
                )
            )
            return result.scalar_one_or_none()
    
    async def get_projects(self, organization_id: Optional[int] = None) -> List[ProjectModel]:
        """Get projects, optionally filtered by organization"""
        async with self.async_session_maker() as session:
            query = select(ProjectModel)
            if organization_id:
                query = query.where(ProjectModel.organization_id == organization_id)
            
            result = await session.execute(query)
            return result.scalars().all()
    
    async def store_repository(self, repository: Repository, project_id: str) -> RepositoryModel:
        """Store or update repository data"""
        async with self.async_session_maker() as session:
            # Check if repository already exists
            result = await session.execute(
                select(RepositoryModel).where(RepositoryModel.id == repository.id)
            )
            existing_repo = result.scalar_one_or_none()
            
            if existing_repo:
                # Update existing repository
                existing_repo.name = repository.name
                existing_repo.project_id = project_id
                existing_repo.url = repository.url
                existing_repo.default_branch = repository.default_branch
                existing_repo.size = repository.size
                existing_repo.is_fork = repository.is_fork
                existing_repo.updated_at = datetime.utcnow()
                repo_model = existing_repo
            else:
                # Create new repository
                repo_model = RepositoryModel.from_dataclass(repository, project_id)
                session.add(repo_model)
            
            await session.commit()
            await session.refresh(repo_model)
            return repo_model
    
    async def store_commits(self, commits: List[Commit], repository_id: str) -> List[CommitModel]:
        """Store commit data, avoiding duplicates"""
        if not commits:
            return []
        
        async with self.async_session_maker() as session:
            commit_models = []
            
            # Get existing commit IDs to avoid duplicates
            existing_commits_result = await session.execute(
                select(CommitModel.commit_id).where(CommitModel.repository_id == repository_id)
            )
            existing_commit_ids = set(row[0] for row in existing_commits_result.fetchall())
            
            # Add only new commits
            for commit in commits:
                if commit.commit_id not in existing_commit_ids:
                    commit_model = CommitModel.from_dataclass(commit, repository_id)
                    session.add(commit_model)
                    commit_models.append(commit_model)
            
            if commit_models:
                await session.commit()
                self.logger.info(f"Stored {len(commit_models)} new commits for repository {repository_id}")
            
            return commit_models
    
    async def store_branches(self, branches: List[Branch], repository_id: str) -> List[BranchModel]:
        """Store branch data, updating existing ones"""
        if not branches:
            return []
        
        async with self.async_session_maker() as session:
            # Delete existing branches for this repository
            await session.execute(
                delete(BranchModel).where(BranchModel.repository_id == repository_id)
            )
            
            # Add current branches
            branch_models = []
            for branch in branches:
                branch_model = BranchModel.from_dataclass(branch, repository_id)
                session.add(branch_model)
                branch_models.append(branch_model)
            
            await session.commit()
            self.logger.info(f"Stored {len(branch_models)} branches for repository {repository_id}")
            return branch_models
    
    async def store_pull_requests(self, pull_requests: List[PullRequest], repository_id: str) -> List[PullRequestModel]:
        """Store pull request data, avoiding duplicates"""
        if not pull_requests:
            return []
        
        async with self.async_session_maker() as session:
            pr_models = []
            
            # Get existing PR IDs to avoid duplicates
            existing_prs_result = await session.execute(
                select(PullRequestModel.pull_request_id).where(
                    PullRequestModel.repository_id == repository_id
                )
            )
            existing_pr_ids = set(row[0] for row in existing_prs_result.fetchall())
            
            # Add only new PRs
            for pr in pull_requests:
                if pr.pull_request_id not in existing_pr_ids:
                    pr_model = PullRequestModel.from_dataclass(pr, repository_id)
                    session.add(pr_model)
                    pr_models.append(pr_model)
            
            if pr_models:
                await session.commit()
                self.logger.info(f"Stored {len(pr_models)} new pull requests for repository {repository_id}")
            
            return pr_models
    
    async def store_analytics_result(self, repository_id: str, analytics_result) -> AnalyticsResultModel:
        """Store analytics result"""
        async with self.async_session_maker() as session:
            result_model = AnalyticsResultModel(
                repository_id=repository_id,
                analysis_date=datetime.utcnow(),
                commit_analytics=analytics_result.commit_analytics,
                author_analytics=analytics_result.author_analytics,
                branch_analytics=analytics_result.branch_analytics,
                code_quality=analytics_result.code_quality,
                file_analytics=analytics_result.file_analytics,
                time_analytics=analytics_result.time_analytics,
                pull_request_analytics=analytics_result.pull_request_analytics,
                repository_health=analytics_result.repository_health,
                team_analytics=analytics_result.team_analytics,
                security_analytics=analytics_result.security_analytics,
                performance_analytics=analytics_result.performance_analytics,
                technology_analytics=analytics_result.technology_analytics
            )
            
            session.add(result_model)
            await session.commit()
            await session.refresh(result_model)
            
            self.logger.info(f"Stored analytics result for repository {repository_id}")
            return result_model
    
    async def get_repository(self, repository_id: str) -> Optional[RepositoryModel]:
        """Get repository by ID"""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(RepositoryModel).where(RepositoryModel.id == repository_id)
            )
            return result.scalar_one_or_none()
    
    async def get_repositories(self, project_id: Optional[str] = None) -> List[RepositoryModel]:
        """Get repositories, optionally filtered by project"""
        async with self.async_session_maker() as session:
            query = select(RepositoryModel)
            if project_id:
                query = query.where(RepositoryModel.project_id == project_id)
            
            result = await session.execute(query)
            return result.scalars().all()
    
    async def get_repository_with_project(self, repository_id: str) -> Optional[RepositoryModel]:
        """Get repository by ID with project information loaded"""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(RepositoryModel)
                .options(selectinload(RepositoryModel.project))
                .where(RepositoryModel.id == repository_id)
            )
            return result.scalar_one_or_none()
    
    async def get_repository_list(self, organization_name: Optional[str] = None) -> List[tuple]:
        """Get list of (project_name, repository_name) tuples"""
        async with self.async_session_maker() as session:
            query = select(ProjectModel.name, RepositoryModel.name).join(
                RepositoryModel, ProjectModel.id == RepositoryModel.project_id
            )
            
            if organization_name:
                query = query.join(
                    OrganizationModel, ProjectModel.organization_id == OrganizationModel.id
                ).where(OrganizationModel.name == organization_name)
            
            result = await session.execute(query)
            return [(row[0], row[1]) for row in result.fetchall()]
    
    async def seed_from_config(self):
        """Seed database with data from configuration file"""
        self.logger.info("Seeding database from configuration...")
        
        try:
            config = get_config()
            
            # Create organization
            org_model = await self.store_organization(
                name=config.organization,
                url=config.get_azure_devops_url(),
                description=f"Organization {config.organization}"
            )
            
            # Create projects and their repositories
            for project_config in config.projects:
                # Use project name as ID for now (could be enhanced to use actual Azure DevOps project ID)
                project_model = await self.store_project(
                    project_id=project_config.name,
                    name=project_config.name,
                    organization_id=org_model.id,
                    description=f"Project {project_config.name}"
                )
                
                self.logger.info(f"Seeded project: {project_config.name}")
            
            self.logger.info("Database seeding completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to seed database from config: {e}")
            raise

    async def get_latest_analytics_result(self, repository_id: str) -> Optional[AnalyticsResultModel]:
        """Get latest analytics result for a repository"""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(AnalyticsResultModel)
                .where(AnalyticsResultModel.repository_id == repository_id)
                .order_by(desc(AnalyticsResultModel.analysis_date))
                .limit(1)
            )
            return result.scalar_one_or_none()
    
    async def get_commit_count(self, repository_id: str) -> int:
        """Get total commit count for a repository"""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(func.count(CommitModel.commit_id)).where(CommitModel.repository_id == repository_id)
            )
            return result.scalar() or 0
    
    async def get_author_statistics(self, repository_id: str) -> Dict[str, Any]:
        """Get author statistics for a repository"""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(
                    CommitModel.author_name,
                    func.count(CommitModel.commit_id).label('commit_count'),
                    func.min(CommitModel.author_date).label('first_commit'),
                    func.max(CommitModel.author_date).label('last_commit')
                )
                .where(CommitModel.repository_id == repository_id)
                .group_by(CommitModel.author_name)
                .order_by(desc('commit_count'))
            )
            
            authors = {}
            for row in result.fetchall():
                authors[row.author_name] = {
                    'commit_count': row.commit_count,
                    'first_commit': row.first_commit.isoformat() if row.first_commit else None,
                    'last_commit': row.last_commit.isoformat() if row.last_commit else None
                }
            
            return authors
    
    async def get_commits(self, repository_id: str, limit: Optional[int] = None) -> List[CommitModel]:
        """Get commits for a repository"""
        async with self.async_session_maker() as session:
            query = select(CommitModel).where(CommitModel.repository_id == repository_id).order_by(desc(CommitModel.author_date))
            
            if limit:
                query = query.limit(limit)
            
            result = await session.execute(query)
            return result.scalars().all()
    
    async def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old analytics results"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        async with self.async_session_maker() as session:
            result = await session.execute(
                delete(AnalyticsResultModel).where(AnalyticsResultModel.analysis_date < cutoff_date)
            )
            await session.commit()
            
            deleted_count = result.rowcount
            if deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} old analytics results")
            
            return deleted_count
    
    # Analytics Request CRUD operations
    async def store_analytics_request(self, project_name: str, repository_ids: List[str]) -> AnalyticsRequestModel:
        """Store a new analytics request"""
        async with self.async_session_maker() as session:
            request_model = AnalyticsRequestModel(
                project_name=project_name,
                repository_ids=repository_ids,
                status="Requested"
            )
            
            session.add(request_model)
            await session.commit()
            await session.refresh(request_model)
            
            self.logger.info(f"Created analytics request {request_model.id} for project {project_name}")
            return request_model
    
    async def update_request_status(self, request_id: int, status: str, 
                                  error_message: str = None, progress_info: dict = None,
                                  result_files: List[str] = None) -> Optional[AnalyticsRequestModel]:
        """Update analytics request status"""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(AnalyticsRequestModel).where(AnalyticsRequestModel.id == request_id)
            )
            request_model = result.scalar_one_or_none()
            
            if not request_model:
                return None
            
            request_model.status = status
            request_model.updated_at = datetime.utcnow()
            
            if status == "Running" and not request_model.started_date:
                request_model.started_date = datetime.utcnow()
            elif status in ["Completed", "Failed"]:
                request_model.completed_date = datetime.utcnow()
            
            if error_message:
                request_model.error_message = error_message
            
            if progress_info:
                request_model.progress_info = progress_info
            
            if result_files:
                request_model.result_files = result_files
            
            await session.commit()
            await session.refresh(request_model)
            
            self.logger.info(f"Updated request {request_id} status to {status}")
            return request_model
    
    async def get_analytics_request(self, request_id: int) -> Optional[AnalyticsRequestModel]:
        """Get analytics request by ID"""
        async with self.async_session_maker() as session:
            result = await session.execute(
                select(AnalyticsRequestModel).where(AnalyticsRequestModel.id == request_id)
            )
            return result.scalar_one_or_none()
    
    async def get_analytics_requests(self, status: Optional[str] = None) -> List[AnalyticsRequestModel]:
        """Get analytics requests, optionally filtered by status"""
        async with self.async_session_maker() as session:
            query = select(AnalyticsRequestModel).order_by(desc(AnalyticsRequestModel.requested_date))
            
            if status:
                query = query.where(AnalyticsRequestModel.status == status)
            
            result = await session.execute(query)
            return result.scalars().all() 