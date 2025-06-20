# SEO Agent with Google Ads API Integration

A comprehensive SEO analysis and optimization toolkit with Google Ads API integration. This tool helps you research keywords, analyze search volumes, and generate actionable SEO recommendations.

## Features

- **Keyword Research**: Get keyword ideas and search volume data from Google Ads API
- **Web Interface**: User-friendly interface for keyword research
- **API Endpoints**: Easy integration with other tools and workflows
- **Langflow Integration**: Built-in support for Langflow workflows
- **Multi-region Support**: Research keywords for different locations and languages

## Google Ads API Integration

This tool uses the Google Ads API to fetch keyword ideas and search volume data. You'll need:

1. A Google Ads API developer token
2. OAuth 2.0 client credentials
3. A Google Ads manager account with API access

## Web Interface

Access the web interface to:
- Enter seed keywords
- Select target location and language
- View keyword ideas with search volumes and competition levels
- Export results

## API Endpoints

- `POST /api/keyword-research` - Main keyword research endpoint
- `POST /api/langflow/keyword-research` - Langflow integration endpoint

## Langflow Integration

Use this JSON configuration in your Langflow flow:

```json
{
  "inputs": {
    "keywords": ["example keyword", "another keyword"],
    "location_id": 1022378,
    "language_id": 1000
  },
  "endpoint": "https://your-render-app.onrender.com/api/langflow/keyword-research"
}
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/seo-agent.git
   cd seo-agent
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the package in development mode:
   ```bash
   pip install -e .
   ```

   Or install directly from GitHub:
   ```bash
   pip install git+https://github.com/yourusername/seo-agent.git
   ```

## Configuration

1. Copy the example environment file and update with your API keys:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your credentials:
   ```
   # Google Ads API
   GOOGLE_ADS_CLIENT_ID=your_client_id
   GOOGLE_ADS_CLIENT_SECRET=your_client_secret
   GOOGLE_ADS_DEVELOPER_TOKEN=your_developer_token
   GOOGLE_ADS_REFRESH_TOKEN=your_refresh_token
   GOOGLE_ADS_LOGIN_CUSTOMER_ID=your_login_customer_id

   # OpenAI (for advanced features)
   OPENAI_API_KEY=your_openai_api_key
   
   # Debugging
   DEBUG=True
   LOG_LEVEL=INFO
   ```

## Usage

### Command Line Interface

```bash
# Basic usage
seo-agent https://example.com "keyword1" "keyword2" "keyword3"

# With options
seo-agent https://example.com "seo tools" "keyword research" \
  --geography US \
  --max-keywords 100 \
  --max-competitors 5 \
  --output-format markdown \
  --output-file report.md
```

### Python API

```python
import asyncio
from seo_agent import SEOOrchestrator, SEOAnalysisInput

async def main():
    # Initialize the orchestrator
    orchestrator = SEOOrchestrator()
    
    # Prepare input
    analysis_input = SEOAnalysisInput(
        url="https://example.com",
        geography="US",
        seed_keywords=["seo tools", "keyword research"],
        max_keywords=50,
        analyze_competitors=True,
        max_competitors=5,
        language="en"
    )
    
    # Run the analysis
    result = await orchestrator.execute(analysis_input)
    
    # Generate and print the report
    if result.success:
        report = await orchestrator.generate_report(
            result, 
            output_format="markdown",
            output_file="seo_report.md"
        )
        print(f"Report generated: seo_report.md")
    else:
        print(f"Analysis failed: {result.error}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Components

### 1. Keyword Research Agent
- Expands seed keywords using semantic analysis
- Fetches search volume and competition data from Google Ads API
- Identifies high-opportunity keywords

### 2. URL Analysis Agent
- Analyzes on-page SEO factors (titles, meta descriptions, headings, etc.)
- Checks for technical SEO issues
- Analyzes content quality and structure
- Provides optimization recommendations

### 3. Competitor Analysis Agent
- Identifies top competitors in search results
- Analyzes competitors' backlink profiles
- Compares content strategies
- Identifies gaps and opportunities

### 4. Report Generation
- Generates comprehensive reports in multiple formats (Markdown, HTML, JSON)
- Provides actionable recommendations
- Includes visualizations of key metrics

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_ADS_CLIENT_ID` | Google Ads API client ID | Yes |
| `GOOGLE_ADS_CLIENT_SECRET` | Google Ads API client secret | Yes |
| `GOOGLE_ADS_DEVELOPER_TOKEN` | Google Ads developer token | Yes |
| `GOOGLE_ADS_REFRESH_TOKEN` | OAuth 2.0 refresh token | Yes |
| `GOOGLE_ADS_LOGIN_CUSTOMER_ID` | Google Ads login customer ID | Yes |
| `OPENAI_API_KEY` | OpenAI API key (for advanced features) | No |
| `DEBUG` | Enable debug mode (True/False) | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) | No |

## Example Reports

### Executive Summary

```markdown
# SEO Analysis Report

**URL:** https://example.com  
**Date:** 2023-04-15T14:30:00Z

## Executive Summary

### Key Findings
- **Top Keywords:** seo tools, keyword research, seo analysis, backlink checker, on page seo
- **SEO Score:** 78/100
- **Competitors Analyzed:** 5

## Top Recommendations

| Priority | Recommendation | Impact | Effort |
|----------|----------------|---------|---------|
| High | Add meta description to improve click-through rate | High | Low |
| High | Fix broken internal links (3 found) | High | Medium |
| Medium | Add alt text to 5 images | Medium | Low |
| Medium | Increase content length (current: 450 words, recommended: 1000+) | Medium | High |
| Low | Add more internal links (current: 8) | Low | Low |
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with ❤️ using Python
- Uses the Google Ads API for keyword research
- Inspired by various SEO tools and best practices

## Support

For support, please open an issue on GitHub or contact us at support@example.com
