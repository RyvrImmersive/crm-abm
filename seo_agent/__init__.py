"""SEO Agent - A comprehensive SEO analysis and optimization toolkit.

This package provides tools for keyword research, URL analysis, competitor analysis,
and generating actionable SEO recommendations.
"""

from .agents import (
    SEOOrchestrator,
    SEOAnalysisInput,
    SEOAnalysisOutput,
    KeywordResearchAgent,
    URLAnalysisAgent,
    CompetitorAnalysisAgent
)

__version__ = '0.1.0'
__all__ = [
    'SEOOrchestrator',
    'SEOAnalysisInput',
    'SEOAnalysisOutput',
    'KeywordResearchAgent',
    'URLAnalysisAgent',
    'CompetitorAnalysisAgent'
]
