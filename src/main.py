"""
Main entry point for Azure DevOps Git Repository Analytics Tool
"""

import asyncio
import logging
import sys
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from .config import get_config, reload_config
from .analytics_engine import AnalyticsEngine, AnalyticsResult
from .excel_exporter import ExcelExporter
from .visualizations import VisualizationGenerator


def setup_logging():
    """Setup logging configuration"""
    config = get_config()
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler
    file_handler = logging.FileHandler(
        log_dir / f"git_analytics_{datetime.now().strftime('%Y%m%d')}.log"
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Set third-party library log levels
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)


class GitAnalyticsTool:
    """Main application class for Git Analytics Tool"""
    
    def __init__(self):
        """Initialize the analytics tool"""
        self.config = get_config()
        self.analytics_engine = AnalyticsEngine()
        self.excel_exporter = ExcelExporter()
        self.visualization_generator = VisualizationGenerator()
        
        self.logger = logging.getLogger(__name__)
    
    async def run_analysis(self) -> Dict[str, AnalyticsResult]:
        """Run analytics on all configured repositories"""
        self.logger.info("Starting Git Repository Analytics")
        self.logger.info(f"Configuration: {self.config}")
        
        results = {}
        repository_list = self.config.get_repository_list()
        
        self.logger.info(f"Analyzing {len(repository_list)} repositories...")
        
        for i, (project, repository) in enumerate(repository_list, 1):
            self.logger.info(f"Processing repository {i}/{len(repository_list)}: {project}/{repository}")
            
            try:
                # Run analytics for this repository
                result = await self.analytics_engine.analyze_repository(project, repository)
                repo_key = f"{project}/{repository}"
                results[repo_key] = result
                
                self.logger.info(f"Successfully analyzed {repo_key}")
                
            except Exception as e:
                self.logger.error(f"Failed to analyze {project}/{repository}: {e}")
                # Continue with other repositories
                continue
        
        self.logger.info(f"Completed analysis of {len(results)} repositories")
        return results
    
    async def export_results(self, results: Dict[str, AnalyticsResult]) -> Dict[str, Any]:
        """Export results to various formats"""
        export_info = {
            "timestamp": datetime.now().isoformat(),
            "total_repositories": len(results),
            "exports": {}
        }
        
        if not results:
            self.logger.warning("No results to export")
            return export_info
        
        # Export to Excel
        if self.config.output.formats.get('excel', True):
            try:
                self.logger.info("Exporting to Excel...")
                excel_path = await self.excel_exporter.export_analytics(results)
                export_info["exports"]["excel"] = str(excel_path)
                self.logger.info(f"Excel export completed: {excel_path}")
            except Exception as e:
                self.logger.error(f"Excel export failed: {e}")
        
        # Export to JSON
        if self.config.output.formats.get('json', True):
            try:
                self.logger.info("Exporting to JSON...")
                json_path = await self._export_json(results)
                export_info["exports"]["json"] = str(json_path)
                self.logger.info(f"JSON export completed: {json_path}")
            except Exception as e:
                self.logger.error(f"JSON export failed: {e}")
        
        # Export to CSV
        if self.config.output.formats.get('csv', True):
            try:
                self.logger.info("Exporting to CSV...")
                csv_paths = await self._export_csv(results)
                export_info["exports"]["csv"] = [str(p) for p in csv_paths]
                self.logger.info(f"CSV export completed: {len(csv_paths)} files")
            except Exception as e:
                self.logger.error(f"CSV export failed: {e}")
        
        # Generate visualizations
        if self.config.output.charts.get('generate_charts', True):
            try:
                self.logger.info("Generating visualizations...")
                chart_paths = await self.visualization_generator.generate_all_charts(results)
                export_info["exports"]["charts"] = [str(p) for p in chart_paths if p]
                self.logger.info(f"Generated {len(chart_paths)} charts")
            except Exception as e:
                self.logger.error(f"Chart generation failed: {e}")
        
        return export_info
    
    async def _export_json(self, results: Dict[str, AnalyticsResult]) -> Path:
        """Export results to JSON format"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") if self.config.output.include_timestamp else ""
        suffix = f"_{timestamp}" if timestamp else ""
        filename = f"{self.config.output.filename_prefix}{suffix}.json"
        
        output_path = self.config.get_output_path(filename)
        
        # Convert results to serializable format
        json_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "tool_version": "1.0.0",
                "total_repositories": len(results)
            },
            "repositories": {}
        }
        
        for repo_key, result in results.items():
            json_data["repositories"][repo_key] = result.to_dict()
        
        # Write JSON file
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(json_data, file, indent=2, ensure_ascii=False)
        
        return output_path
    
    async def _export_csv(self, results: Dict[str, AnalyticsResult]) -> list[Path]:
        """Export results to CSV format"""
        import pandas as pd
        
        csv_files = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") if self.config.output.include_timestamp else ""
        suffix = f"_{timestamp}" if timestamp else ""
        
        # Summary CSV
        summary_data = []
        for repo_key, result in results.items():
            summary_data.append({
                "Repository": repo_key,
                "Total_Commits": result.commit_analytics.get('total_commits', 0),
                "Total_Authors": result.author_analytics.get('total_authors', 0),
                "Total_Branches": result.branch_analytics.get('total_branches', 0),
                "Total_Pull_Requests": result.pull_request_analytics.get('total_pull_requests', 0),
                "Latest_Commit": result.commit_analytics.get('last_commit_date', ''),
                "Merge_Ratio": result.commit_analytics.get('merge_ratio', 0),
                "Bus_Factor_50": result.author_analytics.get('bus_factor_50_percent', 0),
                "Bus_Factor_80": result.author_analytics.get('bus_factor_80_percent', 0)
            })
        
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            summary_path = self.config.get_output_path(f"summary{suffix}.csv")
            summary_df.to_csv(summary_path, index=False)
            csv_files.append(summary_path)
        
        # Detailed analytics CSVs
        for repo_key, result in results.items():
            safe_repo_name = repo_key.replace('/', '_').replace(' ', '_')
            
            # Author analytics CSV
            if result.author_analytics.get('author_statistics'):
                author_data = []
                for author, stats in result.author_analytics['author_statistics'].items():
                    author_data.append({
                        "Repository": repo_key,
                        "Author": author,
                        "Commits": stats.get('commits', 0),
                        "Additions": stats.get('additions', 0),
                        "Edits": stats.get('edits', 0),
                        "Deletions": stats.get('deletions', 0),
                        "Total_Changes": stats.get('total_changes', 0),
                        "First_Commit": stats.get('first_commit', ''),
                        "Last_Commit": stats.get('last_commit', '')
                    })
                
                if author_data:
                    author_df = pd.DataFrame(author_data)
                    author_path = self.config.get_output_path(f"{safe_repo_name}_authors{suffix}.csv")
                    author_df.to_csv(author_path, index=False)
                    csv_files.append(author_path)
        
        return csv_files
    
    async def run(self) -> Dict[str, Any]:
        """Main execution method"""
        try:
            # Run analytics
            results = await self.run_analysis()
            
            # Export results
            export_info = await self.export_results(results)
            
            # Generate summary
            summary = {
                "status": "success",
                "analysis_completed_at": datetime.now().isoformat(),
                "repositories_analyzed": len(results),
                "exports": export_info
            }
            
            self.logger.info("Git Analytics completed successfully!")
            self.logger.info(f"Results exported to: {self.config.output.directory}")
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Analytics failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


async def main():
    """Main entry point"""
    try:
        # Setup logging
        setup_logging()
        
        # Create and run analytics tool
        tool = GitAnalyticsTool()
        result = await tool.run()
        
        # Print summary
        print("\n" + "="*50)
        print("GIT ANALYTICS SUMMARY")
        print("="*50)
        print(f"Status: {result['status'].upper()}")
        
        if result['status'] == 'success':
            print(f"Repositories Analyzed: {result['repositories_analyzed']}")
            print(f"Analysis Completed: {result['analysis_completed_at']}")
            
            exports = result['exports']['exports']
            if 'excel' in exports:
                print(f"Excel Report: {exports['excel']}")
            if 'json' in exports:
                print(f"JSON Data: {exports['json']}")
            if 'csv' in exports:
                print(f"CSV Files: {len(exports['csv'])} files generated")
            if 'charts' in exports:
                print(f"Charts: {len(exports['charts'])} visualizations generated")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        print("="*50)
        
        return 0 if result['status'] == 'success' else 1
        
    except KeyboardInterrupt:
        print("\nAnalysis interrupted by user")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main())) 