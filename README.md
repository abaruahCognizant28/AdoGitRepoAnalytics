# Azure DevOps Git Repository Analytics Tool

A comprehensive Python tool for extracting and analyzing Git repository data from Azure DevOps. Generate detailed analytics, Excel reports, and visualizations to gain insights into your development processes.

## Features

### 📊 Comprehensive Analytics
- **Commit Analytics**: Frequency, volume, timing, and trends
- **Author Analytics**: Productivity, collaboration patterns, bus factor analysis
- **Branch Analytics**: Lifecycle, naming conventions, merge patterns
- **Code Quality**: Churn analysis, complexity tracking, refactoring patterns
- **Time Analytics**: Development velocity, work patterns, cycle times
- **Pull Request Analytics**: Review cycles, conflict resolution
- **Security Analytics**: Security-related patterns and commits
- **Team Analytics**: Collaboration patterns, knowledge distribution

### 📈 Multiple Output Formats
- **Excel Reports**: Multi-sheet workbooks with formatted data and metrics
- **JSON Data**: Structured data for programmatic access
- **CSV Files**: Individual datasets for further analysis
- **Visualizations**: Charts and graphs (PNG, SVG, PDF)

### 🔧 Key Capabilities
- **Async Processing**: High-performance data collection
- **Configurable Analytics**: Enable/disable specific analysis types
- **Privacy Controls**: Author anonymization options
- **Rate Limiting**: Respects Azure DevOps API limits
- **Batch Processing**: Handle multiple repositories efficiently

## Installation

### Prerequisites
- Python 3.9 or higher
- Azure DevOps Personal Access Token
- Access to Azure DevOps repositories

### Quick Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ado-git-repo-analytics.git
   cd ado-git-repo-analytics
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp env.template .env
   # Edit .env file with your Azure DevOps credentials
   ```

4. **Configure repositories**
   ```bash
   # Edit config/repositories.yaml with your project and repository details
   ```

### Alternative Installation

```bash
pip install -e .
```

## Configuration

### 1. Environment Variables (.env)

Create a `.env` file from the template:

```bash
# Azure DevOps Personal Access Token
AZURE_DEVOPS_PAT=your_personal_access_token_here

# Azure DevOps Organization URL
AZURE_DEVOPS_ORG_URL=https://dev.azure.com/your-organization

# Optional settings
LOG_LEVEL=INFO
MAX_CONCURRENT_REQUESTS=5
```

#### Getting Azure DevOps Personal Access Token

1. Go to Azure DevOps: `https://dev.azure.com/[your-organization]`
2. Click on User Settings → Personal Access Tokens
3. Create new token with these scopes:
   - **Code (read)**: Access to repository data
   - **Project and team (read)**: Access to project information

### 2. Repository Configuration (config/repositories.yaml)

```yaml
azure_devops:
  organization: "your-organization-name"
  
  projects:
    - name: "Project1"
      repositories:
        - "repo1"
        - "repo2"
    
    - name: "Project2"
      repositories:
        - "repo3"

# Analysis Configuration
analysis:
  date_range:
    start_date: "2023-01-01"  # Optional: limit analysis date range
    end_date: "2024-01-01"    # Optional: limit analysis date range
  
  include:
    commit_analytics: true
    author_analytics: true
    branch_analytics: true
    # ... enable/disable specific analytics

# Output Configuration
output:
  directory: "output"
  filename_prefix: "git_analytics"
  include_timestamp: true
  
  formats:
    excel: true
    csv: true
    json: true
  
  charts:
    generate_charts: true
    chart_format: "png"
    chart_dpi: 300
```

## Usage

### Basic Usage

```bash
python -m src.main
```

### Programmatic Usage

```python
import asyncio
from src.main import GitAnalyticsTool

async def run_analytics():
    tool = GitAnalyticsTool()
    results = await tool.run()
    print(f"Analysis completed: {results['status']}")

asyncio.run(run_analytics())
```

### Custom Configuration

```python
from src.config import reload_config
from src.main import GitAnalyticsTool

# Load custom config
reload_config("path/to/custom/config.yaml")

tool = GitAnalyticsTool()
results = await tool.run()
```

## Output Structure

```
output/
├── git_analytics_20241201_143022.xlsx      # Excel report
├── git_analytics_20241201_143022.json      # JSON data
├── summary_20241201_143022.csv             # Summary CSV
├── Project1_repo1_authors_20241201_143022.csv  # Author details
└── charts/                                 # Visualizations
    ├── Project1_repo1_commits_by_day.png
    ├── Project1_repo1_top_contributors.png
    ├── comparison_commits.png
    └── ...
```

## Analytics Categories

### 1. Commit Analytics
- Total commits, additions, deletions, edits
- Commit frequency by time periods
- Merge vs regular commit ratios
- Commit message analysis
- Time-based patterns (hourly, daily, monthly)

### 2. Author Analytics
- Top contributors by various metrics
- Contribution distribution and ownership
- Bus factor analysis (risk assessment)
- Author activity patterns
- Collaboration indicators

### 3. Branch Analytics
- Branch lifecycle and naming patterns
- Feature vs hotfix branch classification
- Long-lived branch identification
- Merge pattern analysis

### 4. Code Quality Analytics
- Code churn and hotspot identification
- Large commit detection
- Refactoring pattern analysis
- Technical debt indicators

### 5. Time Analytics
- Development velocity trends
- Work pattern analysis (weekends, after-hours)
- Pull request cycle times
- Release cadence analysis

### 6. Team Analytics
- Team velocity and productivity
- Knowledge distribution
- Cross-team collaboration patterns
- Onboarding effectiveness

## Advanced Configuration

### Privacy Settings

```yaml
advanced:
  privacy:
    anonymize_authors: true  # Replace author names with hashes
    exclude_patterns:
      - "*.log"
      - "node_modules/*"
      - ".git/*"
```

### API Rate Limiting

```yaml
advanced:
  api:
    timeout: 30
    retry_attempts: 3
    rate_limit_delay: 1  # seconds between requests
```

### Processing Options

```yaml
advanced:
  processing:
    batch_size: 100  # commits to process at once
    max_file_size_mb: 10  # skip large files
```

## Troubleshooting

### Common Issues

1. **Authentication Error**
   ```
   Error: AZURE_DEVOPS_PAT environment variable is required
   ```
   - Ensure `.env` file exists with valid Personal Access Token
   - Check token permissions (Code read, Project read)

2. **Repository Not Found**
   ```
   Error: Repository 'repo-name' not found in project 'project-name'
   ```
   - Verify repository and project names in config
   - Check access permissions for the repositories

3. **Rate Limiting**
   ```
   Warning: Request attempt 1 failed: 429
   ```
   - Increase `rate_limit_delay` in configuration
   - Reduce `MAX_CONCURRENT_REQUESTS` in environment

### Logging

Logs are saved to `logs/git_analytics_YYYYMMDD.log`

Set log level in `.env`:
```bash
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

## Development

### Running Tests

```bash
pip install -e ".[dev]"
pytest
```

### Code Formatting

```bash
black src/
flake8 src/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Run tests and formatting
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and questions:

1. Check the [troubleshooting section](#troubleshooting)
2. Search existing issues on GitHub
3. Create a new issue with:
   - Error message and logs
   - Configuration (anonymized)
   - Steps to reproduce

## Roadmap

- [ ] Support for GitHub repositories
- [ ] Real-time dashboard
- [ ] Integration with CI/CD pipelines
- [ ] Advanced file-level analytics
- [ ] Machine learning insights
- [ ] API endpoints for external tools

---

**Note**: This tool is designed for Azure DevOps Git repositories. Ensure you have appropriate permissions before analyzing repositories. 