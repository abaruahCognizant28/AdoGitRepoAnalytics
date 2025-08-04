"""
Configuration management for Azure DevOps Git Analytics Tool
"""

import os
import yaml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
import asyncio


@dataclass
class DateRange:
    """Date range configuration for analysis"""
    start_date: Optional[str] = None
    end_date: Optional[str] = None


@dataclass
class ProjectConfig:
    """Project configuration"""
    name: str
    repositories: List[str]


@dataclass
class AnalyticsConfig:
    """Analytics inclusion configuration"""
    commit_analytics: bool = True
    author_analytics: bool = True
    branch_analytics: bool = True
    code_quality: bool = True
    file_analytics: bool = True
    time_analytics: bool = True
    pull_request_analytics: bool = True
    repository_health: bool = True
    team_analytics: bool = True
    security_analytics: bool = True
    performance_analytics: bool = True
    technology_analytics: bool = True


@dataclass
class OutputConfig:
    """Output configuration"""
    directory: str = "output"
    filename_prefix: str = "git_analytics"
    include_timestamp: bool = True
    formats: Dict[str, bool] = None
    charts: Dict[str, Any] = None

    def __post_init__(self):
        if self.formats is None:
            self.formats = {"excel": True, "csv": True, "json": True}
        if self.charts is None:
            self.charts = {
                "generate_charts": True,
                "chart_format": "png",
                "chart_dpi": 300
            }


@dataclass
class APIConfig:
    """API configuration"""
    timeout: int = 30
    retry_attempts: int = 3
    rate_limit_delay: int = 1


@dataclass
class ProcessingConfig:
    """Data processing configuration"""
    batch_size: int = 100
    max_file_size_mb: int = 10


@dataclass
class PrivacyConfig:
    """Privacy and security configuration"""
    anonymize_authors: bool = False
    exclude_patterns: List[str] = None

    def __post_init__(self):
        if self.exclude_patterns is None:
            self.exclude_patterns = [
                "*.log", "*.tmp", "node_modules/*", ".git/*"
            ]


@dataclass
class DatabaseConfig:
    """Database configuration"""
    enabled: bool = True
    url: Optional[str] = None
    auto_store: bool = True
    cleanup_days: int = 90


class Config:
    """Main configuration class"""
    
    def __init__(self, config_file: str = "config/repositories.yaml", use_database: bool = True):
        """Initialize configuration from file and environment"""
        self.config_file = config_file
        self.use_database = use_database
        self._db_manager = None
        self._load_environment()
        self._load_config_file()
        self._validate_config()
    
    def _load_environment(self):
        """Load environment variables"""
        # Try to load .env file
        env_file = Path(".env")
        if env_file.exists():
            load_dotenv(env_file)
        
        # Required environment variables
        self.azure_pat = os.getenv("AZURE_DEVOPS_PAT")
        self.azure_org_url = os.getenv("AZURE_DEVOPS_ORG_URL")
        
        # Optional environment variables
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.max_concurrent_requests = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))
        self.user_agent = os.getenv("USER_AGENT", "GitAnalyticsTool/1.0")
        self.output_dir_override = os.getenv("OUTPUT_DIR")
    
    def _load_config_file(self):
        """Load configuration from YAML file"""
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")
        
        with open(config_path, 'r', encoding='utf-8') as file:
            config_data = yaml.safe_load(file)
        
        # Parse Azure DevOps configuration
        azure_config = config_data.get("azure_devops", {})
        self.organization = azure_config.get("organization")
        
        # Parse projects and repositories
        self.projects = []
        for project_data in azure_config.get("projects", []):
            self.projects.append(ProjectConfig(
                name=project_data["name"],
                repositories=project_data.get("repositories", [])
            ))
        
        # Parse analysis configuration
        analysis_config = config_data.get("analysis", {})
        date_range_data = analysis_config.get("date_range", {})
        self.date_range = DateRange(
            start_date=date_range_data.get("start_date") or None,
            end_date=date_range_data.get("end_date") or None
        )
        
        include_data = analysis_config.get("include", {})
        self.analytics = AnalyticsConfig(**include_data)
        
        # Parse output configuration
        output_data = config_data.get("output", {})
        self.output = OutputConfig(**output_data)
        
        # Override output directory if specified in environment
        if self.output_dir_override:
            self.output.directory = self.output_dir_override
        
        # Parse advanced configuration
        advanced_config = config_data.get("advanced", {})
        
        api_config = advanced_config.get("api", {})
        self.api = APIConfig(**api_config)
        
        processing_config = advanced_config.get("processing", {})
        self.processing = ProcessingConfig(**processing_config)
        
        privacy_config = advanced_config.get("privacy", {})
        self.privacy = PrivacyConfig(**privacy_config)
        
        database_config = advanced_config.get("database", {})
        self.database = DatabaseConfig(**database_config)
    
    def _get_database_manager(self):
        """Get database manager instance"""
        if self._db_manager is None:
            # Import here to avoid circular imports
            from .database import DatabaseManager
            self._db_manager = DatabaseManager()
        return self._db_manager
    
    async def get_repository_list_from_db(self, organization_name: Optional[str] = None) -> List[tuple]:
        """Get repository list from database"""
        if not self.use_database or not self.database.enabled:
            return self.get_repository_list()
        
        try:
            db_manager = self._get_database_manager()
            if not hasattr(db_manager, 'async_session_maker') or db_manager.async_session_maker is None:
                await db_manager.initialize()
            
            org_name = organization_name or self.organization
            return await db_manager.get_repository_list(org_name)
        except Exception:
            # Fallback to config-based repository list
            return self.get_repository_list()
    
    async def get_projects_from_db(self, organization_name: Optional[str] = None) -> List[ProjectConfig]:
        """Get projects from database, falling back to config if needed"""
        if not self.use_database or not self.database.enabled:
            return self.projects
        
        try:
            db_manager = self._get_database_manager()
            if not hasattr(db_manager, 'async_session_maker') or db_manager.async_session_maker is None:
                await db_manager.initialize()
            
            # Get organization
            org_name = organization_name or self.organization
            org = await db_manager.get_organization(org_name)
            if not org:
                return self.projects
            
            # Get projects from database
            projects_db = await db_manager.get_projects(org.id)
            
            # Convert to ProjectConfig objects
            db_projects = []
            for project_db in projects_db:
                repositories_db = await db_manager.get_repositories(project_db.id)
                repo_names = [repo.name for repo in repositories_db]
                
                db_projects.append(ProjectConfig(
                    name=project_db.name,
                    repositories=repo_names
                ))
            
            return db_projects if db_projects else self.projects
            
        except Exception:
            # Fallback to config-based projects
            return self.projects
    
    def _validate_config(self):
        """Validate configuration"""
        errors = []
        
        if not self.azure_pat:
            errors.append("AZURE_DEVOPS_PAT environment variable is required")
        
        if not self.azure_org_url:
            errors.append("AZURE_DEVOPS_ORG_URL environment variable is required")
        
        if not self.organization:
            errors.append("Azure DevOps organization must be specified in config file")
        
        if not self.projects:
            errors.append("At least one project must be configured")
        
        for project in self.projects:
            if not project.repositories:
                errors.append(f"Project '{project.name}' must have at least one repository")
        
        if errors:
            raise ValueError("Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors))
    
    def get_repository_list(self) -> List[tuple]:
        """Get list of (project, repository) tuples from config"""
        repos = []
        for project in self.projects:
            for repo in project.repositories:
                repos.append((project.name, repo))
        return repos
    
    def get_azure_devops_url(self) -> str:
        """Get formatted Azure DevOps URL"""
        return self.azure_org_url.rstrip('/')
    
    def get_output_path(self, filename: str = None) -> Path:
        """Get output file path"""
        output_dir = Path(self.output.directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if filename:
            return output_dir / filename
        return output_dir
    
    def is_analytics_enabled(self, analytics_type: str) -> bool:
        """Check if specific analytics type is enabled"""
        return getattr(self.analytics, analytics_type, False)
    
    def __repr__(self):
        """String representation of configuration"""
        return f"Config(organization='{self.organization}', projects={len(self.projects)}, repos={len(self.get_repository_list())})"


# Global configuration instance
_config_instance = None


def get_config(config_file: str = "config/repositories.yaml") -> Config:
    """Get global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_file)
    return _config_instance


def reload_config(config_file: str = "config/repositories.yaml"):
    """Reload configuration"""
    global _config_instance
    _config_instance = Config(config_file) 