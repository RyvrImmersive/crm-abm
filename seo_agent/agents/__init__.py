"""SEO Agent package for comprehensive SEO analysis and optimization."""

from .base_agent import AgentInput, AgentOutput, BaseAgent
from .keyword_research_agent import KeywordResearchAgent, KeywordResearchInput, KeywordData
from .url_analysis_agent import URLAnalysisAgent, URLAnalysisInput, URLMetrics, ContentAnalysis
from .competitor_analysis_agent import (
    CompetitorAnalysisAgent, 
    CompetitorAnalysisInput, 
    CompetitorData
)
from .seo_orchestrator import SEOOrchestrator, SEOAnalysisInput, SEOAnalysisOutput

__all__ = [
    'AgentInput',
    'AgentOutput',
    'BaseAgent',
    'KeywordResearchAgent',
    'KeywordResearchInput',
    'KeywordData',
    'URLAnalysisAgent',
    'URLAnalysisInput',
    'URLMetrics',
    'ContentAnalysis',
    'CompetitorAnalysisAgent',
    'CompetitorAnalysisInput',
    'CompetitorData',
    'SEOOrchestrator',
    'SEOAnalysisInput',
    'SEOAnalysisOutput'
]
