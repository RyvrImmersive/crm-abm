from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, HttpUrl
import logging
import asyncio
from datetime import datetime
from pathlib import Path
import json

from .base_agent import BaseAgent, AgentInput, AgentOutput
from .keyword_research_agent import KeywordResearchAgent, KeywordResearchInput, KeywordData
from .url_analysis_agent import URLAnalysisAgent, URLAnalysisInput, URLMetrics, ContentAnalysis
from .competitor_analysis_agent import CompetitorAnalysisAgent, CompetitorAnalysisInput, CompetitorData
from config.settings import settings

logger = logging.getLogger(__name__)

class SEOAnalysisInput(AgentInput):
    """Input model for SEO analysis"""
    url: HttpUrl = Field(..., description="The URL to analyze")
    geography: str = Field("US", description="Target geography (e.g., 'US', 'GB')")
    seed_keywords: List[str] = Field(..., description="List of seed keywords")
    max_keywords: int = Field(50, description="Maximum number of keywords to analyze")
    analyze_competitors: bool = Field(True, description="Whether to analyze competitors")
    max_competitors: int = Field(5, description="Maximum number of competitors to analyze")
    language: str = Field("en", description="Language code (e.g., 'en', 'es')")

class SEOAnalysisOutput(AgentOutput):
    """Output model for SEO analysis"""
    url: str
    timestamp: str
    keyword_research: Dict[str, Any] = Field(default_factory=dict)
    url_analysis: Dict[str, Any] = Field(default_factory=dict)
    competitor_analysis: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True

class SEOOrchestrator(BaseAgent):
    """Orchestrator agent for comprehensive SEO analysis"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.keyword_agent = KeywordResearchAgent()
        self.url_agent = URLAnalysisAgent()
        self.competitor_agent = CompetitorAnalysisAgent()
    
    async def _execute_impl(self, input_data: SEOAnalysisInput) -> SEOAnalysisOutput:
        """Execute end-to-end SEO analysis"""
        timestamp = datetime.utcnow().isoformat()
        
        try:
            # Step 1: Perform keyword research
            keyword_results = await self._run_keyword_research(input_data)
            
            # Extract top keywords for further analysis
            top_keywords = self._extract_top_keywords(
                keyword_results.get('keywords', []), 
                input_data.max_keywords
            )
            
            # Step 2: Analyze the target URL
            url_analysis = await self._analyze_url(input_data.url, top_keywords)
            
            # Step 3: Analyze competitors (if enabled)
            competitor_analysis = {}
            if input_data.analyze_competitors:
                competitor_analysis = await self._analyze_competitors(
                    input_data.url, 
                    top_keywords,
                    input_data.max_competitors,
                    input_data.geography,
                    input_data.language
                )
            
            # Step 4: Generate recommendations
            recommendations = self._generate_recommendations(
                keyword_results, 
                url_analysis, 
                competitor_analysis
            )
            
            # Step 5: Generate final report
            return SEOAnalysisOutput(
                success=True,
                url=str(input_data.url),
                timestamp=timestamp,
                keyword_research=keyword_results,
                url_analysis=url_analysis.dict() if hasattr(url_analysis, 'dict') else {},
                competitor_analysis=competitor_analysis,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error in SEO analysis: {str(e)}", exc_info=True)
            return SEOAnalysisOutput(
                success=False,
                url=str(input_data.url),
                timestamp=timestamp,
                error=str(e)
            )
    
    async def _run_keyword_research(self, input_data: SEOAnalysisInput) -> Dict[str, Any]:
        """Run keyword research"""
        keyword_input = KeywordResearchInput(
            geography=input_data.geography,
            seed_keywords=input_data.seed_keywords,
            max_keywords=input_data.max_keywords * 2,  # Get more initially to filter later
            language_code=input_data.language
        )
        
        result = await self.keyword_agent.execute(keyword_input)
        if not result.success:
            raise Exception(f"Keyword research failed: {result.error}")
        
        return {
            'keywords': [kw.dict() for kw in result.keywords],
            'metadata': result.metadata
        }
    
    def _extract_top_keywords(self, keywords: List[Dict], max_keywords: int) -> List[str]:
        """Extract top keywords based on search volume and relevance"""
        if not keywords:
            return []
        
        # Sort by search volume (descending) and filter out low-volume keywords
        sorted_keywords = sorted(
            [k for k in keywords if k.get('avg_monthly_searches', 0) > 100],
            key=lambda x: x.get('avg_monthly_searches', 0),
            reverse=True
        )
        
        # Return the top N keywords
        return [k['keyword'] for k in sorted_keywords[:max_keywords]]
    
    async def _analyze_url(self, url: str, keywords: List[str]) -> Any:
        """Analyze the target URL"""
        url_input = URLAnalysisInput(
            url=url,
            target_keywords=keywords,
            analyze_competitors=False
        )
        
        result = await self.url_agent.execute(url_input)
        if not result.success:
            raise Exception(f"URL analysis failed: {result.error}")
        
        return result
    
    async def _analyze_competitors(
        self, 
        url: str, 
        keywords: List[str], 
        max_competitors: int,
        geography: str,
        language: str
    ) -> Dict[str, Any]:
        """Analyze competitors"""
        if not keywords:
            return {}
            
        comp_input = CompetitorAnalysisInput(
            target_url=url,
            keywords=keywords,
            max_competitors=max_competitors,
            geography=geography,
            language=language
        )
        
        result = await self.competitor_agent.execute(comp_input)
        if not result.success:
            logger.warning(f"Competitor analysis failed: {result.error}")
            return {"error": str(result.error)}
        
        # Convert Pydantic models to dict for JSON serialization
        return {
            'competitors': [
                {
                    **c.dict(exclude_none=True),
                    'metrics': c.metrics.dict() if c.metrics else None,
                    'content_analysis': c.content_analysis.dict() if c.content_analysis else None
                }
                for c in result.competitors
            ],
            'summary': result.summary
        }
    
    def _generate_recommendations(
        self, 
        keyword_results: Dict[str, Any],
        url_analysis: Any,
        competitor_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Add keyword-related recommendations
        if keyword_results.get('keywords'):
            low_volume_kws = [
                k['keyword'] for k in keyword_results['keywords'] 
                if k.get('avg_monthly_searches', 0) < 100
            ]
            if low_volume_kws:
                recommendations.append({
                    'category': 'Keywords',
                    'priority': 'Medium',
                    'title': 'Low Search Volume Keywords',
                    'description': f"Consider focusing on higher volume alternatives to: {', '.join(low_volume_kws[:5])}",
                    'impact': 'Medium',
                    'effort': 'Low'
                })
        
        # Add URL analysis recommendations
        if hasattr(url_analysis, 'metrics') and url_analysis.metrics.seo_issues:
            for issue in url_analysis.metrics.seo_issues[:3]:  # Limit to top 3 issues
                recommendations.append({
                    'category': 'On-Page SEO',
                    'priority': 'High' if 'missing' in issue.lower() else 'Medium',
                    'title': 'SEO Issue Detected',
                    'description': issue,
                    'impact': 'High' if 'missing' in issue.lower() else 'Medium',
                    'effort': 'Low'
                })
        
        # Add competitor-based recommendations
        if competitor_analysis.get('summary'):
            comp_summary = competitor_analysis['summary']
            
            # Backlink recommendation
            if 'average_backlinks' in comp_summary:
                rec = {
                    'category': 'Backlinks',
                    'priority': 'High',
                    'title': 'Backlink Building Opportunity',
                    'description': f"Top competitors average {int(comp_summary['average_backlinks'])} backlinks. "
                                 "Consider implementing a backlink building strategy.",
                    'impact': 'High',
                    'effort': 'High'
                }
                recommendations.append(rec)
            
            # Content length recommendation
            if 'content_length_ranking' in comp_summary and comp_summary['content_length_ranking']:
                avg_length = sum(
                    item['word_count'] 
                    for item in comp_summary['content_length_ranking']
                ) / len(comp_summary['content_length_ranking'])
                
                rec = {
                    'category': 'Content',
                    'priority': 'Medium',
                    'title': 'Content Length Optimization',
                    'description': f"Top-ranking pages average {int(avg_length)} words. "
                                 "Consider expanding your content to match this depth.",
                    'impact': 'Medium',
                    'effort': 'Medium'
                }
                recommendations.append(rec)
        
        # Sort by priority (High, Medium, Low)
        priority_order = {'High': 0, 'Medium': 1, 'Low': 2}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 99))
        
        return recommendations
    
    async def generate_report(
        self, 
        analysis_output: SEOAnalysisOutput,
        output_format: str = 'markdown',
        output_file: Optional[str] = None
    ) -> str:
        """Generate a formatted report from the analysis"""
        if not analysis_output.success:
            return f"Error generating report: {analysis_output.error}"
        
        try:
            if output_format.lower() == 'markdown':
                report = self._generate_markdown_report(analysis_output)
            elif output_format.lower() == 'html':
                report = self._generate_html_report(analysis_output)
            else:
                report = json.dumps(analysis_output.dict(), indent=2)
            
            # Save to file if path is provided
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(report)
                
            return report
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}", exc_info=True)
            return f"Error generating report: {str(e)}"
    
    def _generate_markdown_report(self, analysis: SEOAnalysisOutput) -> str:
        """Generate markdown report"""
        report = [
            f"# SEO Analysis Report",
            f"**URL:** {analysis.url}",
            f"**Date:** {analysis.timestamp}\n",
            "---\n"
        ]
        
        # Executive Summary
        report.extend([
            "## Executive Summary\n",
            "### Key Findings\n"
        ])
        
        # Add key findings from each section
        if analysis.keyword_research.get('keywords'):
            top_kws = ', '.join([k['keyword'] for k in analysis.keyword_research['keywords'][:5]])
            report.append(f"- **Top Keywords:** {top_kws}")
        
        if hasattr(analysis.url_analysis, 'metrics') and analysis.url_analysis.metrics.seo_score is not None:
            report.append(f"- **SEO Score:** {analysis.url_analysis.metrics.seo_score:.1f}/100")
        
        if analysis.competitor_analysis.get('summary', {}).get('total_competitors_analyzed', 0) > 0:
            comp_count = analysis.competitor_analysis['summary']['total_competitors_analyzed']
            report.append(f"- **Competitors Analyzed:** {comp_count}")
        
        # Add recommendations
        if analysis.recommendations:
            report.extend([
                "\n## Top Recommendations\n",
                "| Priority | Recommendation | Impact | Effort |",
                "|----------|----------------|---------|---------|"
            ])
            
            for rec in analysis.recommendations[:5]:  # Top 5 recommendations
                report.append(
                    f"| {rec['priority']} | {rec['description']} | {rec['impact']} | {rec['effort']} |"
                )
        
        # Add detailed sections
        report.extend([
            "\n## Detailed Analysis\n",
            "### 1. Keyword Research\n"
        ])
        
        if analysis.keyword_research.get('keywords'):
            report.extend([
                "| Keyword | Monthly Searches | Competition | CPC |",
                "|---------|------------------|-------------|-----|"
            ])
            
            for kw in analysis.keyword_research['keywords'][:10]:  # Top 10 keywords
                report.append(
                    f"| {kw['keyword']} | {kw.get('avg_monthly_searches', 'N/A')} | "
                    f"{kw.get('competition', 'N/A')} | ${kw.get('cpc_bid_micros', 0) / 1000000:.2f} |"
                )
        
        # URL Analysis
        report.extend(["\n### 2. URL Analysis\n"])
        if hasattr(analysis.url_analysis, 'metrics'):
            metrics = analysis.url_analysis.metrics
            report.extend([
                f"- **Title:** {metrics.title or 'Not found'}",
                f"- **Meta Description:** {metrics.meta_description or 'Not found'}",
                f"- **Word Count:** {metrics.content_analysis.word_count}",
                f"- **Images:** {len(metrics.content_analysis.images)} (with alt text: "
                f"{sum(1 for img in metrics.content_analysis.images if img.get('alt'))})",
                f"- **Internal Links:** {len(metrics.content_analysis.internal_links)}",
                f"- **External Links:** {len(metrics.content_analysis.external_links)}\n"
            ])
            
            if metrics.seo_issues:
                report.append("**Issues Found:**")
                for issue in metrics.seo_issues[:5]:  # Top 5 issues
                    report.append(f"- ❌ {issue}")
        
        # Competitor Analysis
        if analysis.competitor_analysis.get('competitors'):
            report.extend(["\n### 3. Competitor Analysis\n"])
            
            summary = analysis.competitor_analysis.get('summary', {})
            if summary:
                report.extend([
                    f"- **Average Domain Authority:** {summary.get('average_domain_authority', 'N/A')}",
                    f"- **Average Page Authority:** {summary.get('average_page_authority', 'N/A')}",
                    f"- **Average Backlinks:** {int(summary.get('average_backlinks', 0))}\n"
                ])
            
            report.extend(["\n**Top Competitors:**\n"])
            for comp in analysis.competitor_analysis.get('competitors', [])[:3]:
                report.extend([
                    f"#### {comp.get('domain', 'Unknown')}",
                    f"- **URL:** {comp.get('url', 'N/A')}",
                    f"- **Title:** {comp.get('title', 'N/A')}",
                    f"- **Domain Authority:** {comp.get('domain_authority', 'N/A')}",
                    f"- **Backlinks:** {comp.get('backlinks', 'N/A')}\n"
                ])
        
        # Conclusion
        report.extend([
            "\n## Conclusion\n",
            "This report provides a comprehensive analysis of the target URL's SEO performance "
            "including keyword opportunities, on-page optimizations, and competitive insights. "
            "The recommendations section highlights the most impactful actions to improve search visibility."
        ])
        
        return '\n'.join(report)
    
    def _generate_html_report(self, analysis: SEOAnalysisOutput) -> str:
        """Generate HTML report (simplified version)"""
        # Convert markdown to HTML (in a real implementation, use a proper markdown-to-html converter)
        markdown = self._generate_markdown_report(analysis)
        
        # Simple markdown to HTML conversion (basic)
        html = ["""
        <!DOCTYPE html>
        <html>
        <head>
            <title>SEO Analysis Report</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 900px; margin: 0 auto; padding: 20px; }
                h1 { color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px; }
                h2 { color: #3498db; margin-top: 30px; }
                h3 { color: #2980b9; }
                table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                tr:nth-child(even) { background-color: #f9f9f9; }
                .priority-High { background-color: #ffdddd; }
                .priority-Medium { background-color: #ffffcc; }
                .priority-Low { background-color: #ddffdd; }
            </style>
        </head>
        <body>
        """]
        
        # Convert markdown sections to HTML (simplified)
        lines = markdown.split('\n')
        in_table = False
        in_list = False
        
        for line in lines:
            if line.startswith('# '):
                html.append(f'<h1>{line[2:]}</h1>')
            elif line.startswith('## '):
                html.append(f'<h2>{line[3:]}</h2>')
            elif line.startswith('### '):
                html.append(f'<h3>{line[4:]}</h3>')
            elif line.startswith('|'):
                if not in_table:
                    html.append('<table>')
                    in_table = True
                
                # Check if it's a header row
                if '---' in line:
                    continue
                    
                html.append('<tr>')
                cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                for cell in cells:
                    # Check if this is a row in the recommendations table
                    if any(priority in cell for priority in ['High', 'Medium', 'Low']):
                        priority = next((p for p in ['High', 'Medium', 'Low'] if p in cell), '')
                        html.append(f'<td class="priority-{priority}">{cell}</td>')
                    else:
                        html.append(f'<td>{cell}</td>')
                html.append('</tr>')
            else:
                if in_table:
                    html.append('</table>')
                    in_table = False
                
                if line.startswith('- '):
                    if not in_list:
                        html.append('<ul>')
                        in_list = True
                    html.append(f'<li>{line[2:]}</li>')
                else:
                    if in_list:
                        html.append('</ul>')
                        in_list = False
                    if line.strip():
                        html.append(f'<p>{line}</p>')
        
        if in_table:
            html.append('</table>')
        if in_list:
            html.append('</ul>')
        
        html.append("""
        </body>
        </html>
        """)
        
        return '\n'.join(html)
