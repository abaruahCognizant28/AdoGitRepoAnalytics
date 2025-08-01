"""
Visualization module for Git Analytics data
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
from datetime import datetime
import numpy as np

from .analytics_engine import AnalyticsResult
from .config import get_config


logger = logging.getLogger(__name__)

# Set style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")


class VisualizationGenerator:
    """Generate visualizations for Git analytics data"""
    
    def __init__(self):
        """Initialize visualization generator"""
        self.config = get_config()
        self.output_dir = self.config.get_output_path() / "charts"
        self.output_dir.mkdir(exist_ok=True)
        
        # Chart configuration
        self.chart_format = self.config.output.charts.get('chart_format', 'png')
        self.chart_dpi = self.config.output.charts.get('chart_dpi', 300)
        
        # Figure size
        self.fig_size = (12, 8)
        self.small_fig_size = (10, 6)
    
    async def generate_all_charts(self, analytics_results: Dict[str, AnalyticsResult]) -> List[Path]:
        """Generate all charts for analytics results"""
        chart_files = []
        
        logger.info("Generating visualization charts...")
        
        # Single repository charts
        for repo_key, result in analytics_results.items():
            repo_charts = await self._generate_repository_charts(repo_key, result)
            chart_files.extend(repo_charts)
        
        # Comparative charts across repositories
        if len(analytics_results) > 1:
            comparative_charts = await self._generate_comparative_charts(analytics_results)
            chart_files.extend(comparative_charts)
        
        logger.info(f"Generated {len(chart_files)} charts")
        return chart_files
    
    async def _generate_repository_charts(self, repo_key: str, result: AnalyticsResult) -> List[Path]:
        """Generate charts for a single repository"""
        charts = []
        safe_repo_name = repo_key.replace('/', '_').replace(' ', '_')
        
        # Commit analytics charts
        if result.commit_analytics:
            commit_charts = await self._generate_commit_charts(safe_repo_name, result.commit_analytics)
            charts.extend(commit_charts)
        
        # Author analytics charts
        if result.author_analytics:
            author_charts = await self._generate_author_charts(safe_repo_name, result.author_analytics)
            charts.extend(author_charts)
        
        # Time analytics charts
        if result.time_analytics:
            time_charts = await self._generate_time_charts(safe_repo_name, result.time_analytics)
            charts.extend(time_charts)
        
        # Code quality charts
        if result.code_quality:
            quality_charts = await self._generate_code_quality_charts(safe_repo_name, result.code_quality)
            charts.extend(quality_charts)
        
        return charts
    
    async def _generate_commit_charts(self, repo_name: str, commit_analytics: Dict[str, Any]) -> List[Path]:
        """Generate commit-related charts"""
        charts = []
        
        # Commits by day of week
        commits_by_day = commit_analytics.get('commits_by_day_of_week', {})
        if commits_by_day:
            chart_path = await self._create_bar_chart(
                data=commits_by_day,
                title=f"Commits by Day of Week - {repo_name}",
                xlabel="Day of Week",
                ylabel="Number of Commits",
                filename=f"{repo_name}_commits_by_day.{self.chart_format}"
            )
            charts.append(chart_path)
        
        # Commits by hour
        commits_by_hour = commit_analytics.get('commits_by_hour', {})
        if commits_by_hour:
            chart_path = await self._create_line_chart(
                data=commits_by_hour,
                title=f"Commits by Hour of Day - {repo_name}",
                xlabel="Hour of Day",
                ylabel="Number of Commits",
                filename=f"{repo_name}_commits_by_hour.{self.chart_format}"
            )
            charts.append(chart_path)
        
        # Monthly commit trends
        commits_by_month = commit_analytics.get('commits_by_month', {})
        if commits_by_month:
            chart_path = await self._create_trend_chart(
                data=commits_by_month,
                title=f"Monthly Commit Trends - {repo_name}",
                xlabel="Month",
                ylabel="Number of Commits",
                filename=f"{repo_name}_monthly_trends.{self.chart_format}"
            )
            charts.append(chart_path)
        
        # Commit type distribution
        merge_commits = commit_analytics.get('merge_commits', 0)
        regular_commits = commit_analytics.get('regular_commits', 0)
        if merge_commits > 0 or regular_commits > 0:
            chart_path = await self._create_pie_chart(
                data={"Regular Commits": regular_commits, "Merge Commits": merge_commits},
                title=f"Commit Type Distribution - {repo_name}",
                filename=f"{repo_name}_commit_types.{self.chart_format}"
            )
            charts.append(chart_path)
        
        return charts
    
    async def _generate_author_charts(self, repo_name: str, author_analytics: Dict[str, Any]) -> List[Path]:
        """Generate author-related charts"""
        charts = []
        
        # Top contributors by commits
        top_contributors = author_analytics.get('top_contributors_by_commits', {})
        if top_contributors:
            # Take top 10 contributors
            top_10 = dict(list(top_contributors.items())[:10])
            commit_data = {author: stats['commits'] for author, stats in top_10.items()}
            
            chart_path = await self._create_horizontal_bar_chart(
                data=commit_data,
                title=f"Top Contributors by Commits - {repo_name}",
                xlabel="Number of Commits",
                ylabel="Contributors",
                filename=f"{repo_name}_top_contributors.{self.chart_format}"
            )
            charts.append(chart_path)
        
        # Commit distribution
        commit_distribution = author_analytics.get('commit_distribution', [])
        if commit_distribution:
            chart_path = await self._create_distribution_chart(
                data=commit_distribution,
                title=f"Commit Distribution Across Authors - {repo_name}",
                xlabel="Commits per Author",
                ylabel="Frequency",
                filename=f"{repo_name}_commit_distribution.{self.chart_format}"
            )
            charts.append(chart_path)
        
        return charts
    
    async def _generate_time_charts(self, repo_name: str, time_analytics: Dict[str, Any]) -> List[Path]:
        """Generate time-based charts"""
        charts = []
        
        # Work patterns (weekend vs weekday)
        weekend_commits = time_analytics.get('weekend_commits', 0)
        weekday_commits = time_analytics.get('weekday_commits', 0)
        
        if weekend_commits > 0 or weekday_commits > 0:
            chart_path = await self._create_pie_chart(
                data={"Weekday": weekday_commits, "Weekend": weekend_commits},
                title=f"Work Pattern Distribution - {repo_name}",
                filename=f"{repo_name}_work_patterns.{self.chart_format}"
            )
            charts.append(chart_path)
        
        # Weekly commit trends
        commits_by_week = time_analytics.get('commits_by_week', {})
        if commits_by_week and len(commits_by_week) > 4:  # Only if we have significant data
            chart_path = await self._create_trend_chart(
                data=commits_by_week,
                title=f"Weekly Commit Activity - {repo_name}",
                xlabel="Week",
                ylabel="Number of Commits",
                filename=f"{repo_name}_weekly_activity.{self.chart_format}"
            )
            charts.append(chart_path)
        
        return charts
    
    async def _generate_code_quality_charts(self, repo_name: str, code_quality: Dict[str, Any]) -> List[Path]:
        """Generate code quality charts"""
        charts = []
        
        # Code change types
        additions = code_quality.get('total_additions', 0)
        deletions = code_quality.get('total_deletions', 0)
        edits = code_quality.get('total_edits', 0)
        
        if additions > 0 or deletions > 0 or edits > 0:
            chart_path = await self._create_pie_chart(
                data={"Additions": additions, "Deletions": deletions, "Edits": edits},
                title=f"Code Change Distribution - {repo_name}",
                filename=f"{repo_name}_code_changes.{self.chart_format}"
            )
            charts.append(chart_path)
        
        return charts
    
    async def _generate_comparative_charts(self, analytics_results: Dict[str, AnalyticsResult]) -> List[Path]:
        """Generate comparative charts across repositories"""
        charts = []
        
        # Repository comparison by commits
        repo_commits = {}
        repo_authors = {}
        repo_branches = {}
        
        for repo_key, result in analytics_results.items():
            repo_commits[repo_key] = result.commit_analytics.get('total_commits', 0)
            repo_authors[repo_key] = result.author_analytics.get('total_authors', 0)
            repo_branches[repo_key] = result.branch_analytics.get('total_branches', 0)
        
        # Commits comparison
        if any(commits > 0 for commits in repo_commits.values()):
            chart_path = await self._create_horizontal_bar_chart(
                data=repo_commits,
                title="Repository Comparison - Total Commits",
                xlabel="Number of Commits",
                ylabel="Repository",
                filename=f"comparison_commits.{self.chart_format}"
            )
            charts.append(chart_path)
        
        # Authors comparison
        if any(authors > 0 for authors in repo_authors.values()):
            chart_path = await self._create_horizontal_bar_chart(
                data=repo_authors,
                title="Repository Comparison - Total Authors",
                xlabel="Number of Authors",
                ylabel="Repository",
                filename=f"comparison_authors.{self.chart_format}"
            )
            charts.append(chart_path)
        
        # Multi-metric comparison
        comparison_data = {
            'Repository': list(repo_commits.keys()),
            'Commits': list(repo_commits.values()),
            'Authors': list(repo_authors.values()),
            'Branches': list(repo_branches.values())
        }
        
        chart_path = await self._create_multi_metric_chart(
            data=comparison_data,
            title="Repository Multi-Metric Comparison",
            filename=f"comparison_multi_metric.{self.chart_format}"
        )
        charts.append(chart_path)
        
        return charts
    
    async def _create_bar_chart(self, data: Dict[str, Any], title: str, xlabel: str, ylabel: str, filename: str) -> Path:
        """Create a bar chart"""
        fig, ax = plt.subplots(figsize=self.small_fig_size)
        
        keys = list(data.keys())
        values = list(data.values())
        
        bars = ax.bar(keys, values)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height)}', ha='center', va='bottom')
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=self.chart_dpi, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    async def _create_horizontal_bar_chart(self, data: Dict[str, Any], title: str, xlabel: str, ylabel: str, filename: str) -> Path:
        """Create a horizontal bar chart"""
        fig, ax = plt.subplots(figsize=self.fig_size)
        
        # Sort data by values
        sorted_data = dict(sorted(data.items(), key=lambda x: x[1]))
        keys = list(sorted_data.keys())
        values = list(sorted_data.values())
        
        bars = ax.barh(keys, values)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        
        # Add value labels
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2.,
                   f'{int(width)}', ha='left', va='center')
        
        plt.tight_layout()
        
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=self.chart_dpi, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    async def _create_line_chart(self, data: Dict[str, Any], title: str, xlabel: str, ylabel: str, filename: str) -> Path:
        """Create a line chart"""
        fig, ax = plt.subplots(figsize=self.fig_size)
        
        # Sort data by keys (assuming they're numeric)
        sorted_data = dict(sorted(data.items(), key=lambda x: int(x[0]) if str(x[0]).isdigit() else x[0]))
        keys = list(sorted_data.keys())
        values = list(sorted_data.values())
        
        ax.plot(keys, values, marker='o', linewidth=2, markersize=6)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)
        
        plt.xticks(rotation=45 if len(keys) > 10 else 0)
        plt.tight_layout()
        
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=self.chart_dpi, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    async def _create_pie_chart(self, data: Dict[str, Any], title: str, filename: str) -> Path:
        """Create a pie chart"""
        fig, ax = plt.subplots(figsize=self.small_fig_size)
        
        keys = list(data.keys())
        values = list(data.values())
        
        # Filter out zero values
        filtered_data = [(k, v) for k, v in zip(keys, values) if v > 0]
        if not filtered_data:
            plt.close()
            return None
        
        keys, values = zip(*filtered_data)
        
        wedges, texts, autotexts = ax.pie(values, labels=keys, autopct='%1.1f%%', startangle=90)
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        # Improve text appearance
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        plt.tight_layout()
        
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=self.chart_dpi, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    async def _create_trend_chart(self, data: Dict[str, Any], title: str, xlabel: str, ylabel: str, filename: str) -> Path:
        """Create a trend chart with dates"""
        fig, ax = plt.subplots(figsize=self.fig_size)
        
        # Sort data by keys (dates)
        sorted_data = dict(sorted(data.items()))
        keys = list(sorted_data.keys())
        values = list(sorted_data.values())
        
        # Convert keys to dates if they look like dates
        if keys and '-' in str(keys[0]):
            try:
                dates = [datetime.strptime(key, '%Y-%m') for key in keys]
                ax.plot(dates, values, marker='o', linewidth=2, markersize=6)
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
                ax.xaxis.set_major_locator(mdates.MonthLocator(interval=max(1, len(dates)//12)))
                plt.xticks(rotation=45)
            except ValueError:
                # Fallback to regular plot
                ax.plot(keys, values, marker='o', linewidth=2, markersize=6)
                plt.xticks(rotation=45)
        else:
            ax.plot(keys, values, marker='o', linewidth=2, markersize=6)
            plt.xticks(rotation=45 if len(keys) > 10 else 0)
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=self.chart_dpi, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    async def _create_distribution_chart(self, data: List[float], title: str, xlabel: str, ylabel: str, filename: str) -> Path:
        """Create a distribution histogram"""
        fig, ax = plt.subplots(figsize=self.fig_size)
        
        ax.hist(data, bins=min(20, len(set(data))), alpha=0.7, edgecolor='black')
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=self.chart_dpi, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    async def _create_multi_metric_chart(self, data: Dict[str, List], title: str, filename: str) -> Path:
        """Create a multi-metric comparison chart"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(title, fontsize=16, fontweight='bold')
        
        repositories = data['Repository']
        
        # Commits
        ax1.bar(repositories, data['Commits'], color='skyblue')
        ax1.set_title('Commits')
        ax1.set_ylabel('Count')
        ax1.tick_params(axis='x', rotation=45)
        
        # Authors
        ax2.bar(repositories, data['Authors'], color='lightgreen')
        ax2.set_title('Authors')
        ax2.set_ylabel('Count')
        ax2.tick_params(axis='x', rotation=45)
        
        # Branches
        ax3.bar(repositories, data['Branches'], color='lightcoral')
        ax3.set_title('Branches')
        ax3.set_ylabel('Count')
        ax3.tick_params(axis='x', rotation=45)
        
        # Combined scatter plot
        ax4.scatter(data['Commits'], data['Authors'], s=100, alpha=0.7)
        for i, repo in enumerate(repositories):
            ax4.annotate(repo, (data['Commits'][i], data['Authors'][i]), 
                        xytext=(5, 5), textcoords='offset points', fontsize=8)
        ax4.set_xlabel('Commits')
        ax4.set_ylabel('Authors')
        ax4.set_title('Commits vs Authors')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=self.chart_dpi, bbox_inches='tight')
        plt.close()
        
        return output_path 