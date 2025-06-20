#!/usr/bin/env python3
"""Command-line interface for SEO Agent."""

import asyncio
import argparse
import json
from pathlib import Path
from typing import Optional

from seo_agent import SEOOrchestrator, SEOAnalysisInput
from config.settings import settings

async def run_analysis(
    url: str,
    keywords: list[str],
    geography: str = "US",
    max_keywords: int = 50,
    max_competitors: int = 5,
    output_format: str = "markdown",
    output_file: Optional[str] = None,
    language: str = "en"
) -> None:
    """Run SEO analysis and generate report."""
    print(f"🚀 Starting SEO analysis for: {url}")
    print(f"🔍 Keywords: {', '.join(keywords[:5])}{'...' if len(keywords) > 5 else ''}")
    
    # Initialize the orchestrator
    orchestrator = SEOOrchestrator()
    
    # Prepare input
    analysis_input = SEOAnalysisInput(
        url=url,
        geography=geography,
        seed_keywords=keywords,
        max_keywords=max_keywords,
        analyze_competitors=max_competitors > 0,
        max_competitors=max_competitors,
        language=language
    )
    
    try:
        # Run the analysis
        print("🔎 Analyzing keywords...")
        result = await orchestrator.execute(analysis_input)
        
        if not result.success:
            print(f"❌ Analysis failed: {result.error}")
            return
        
        # Generate and display the report
        print("📊 Generating report...")
        report = await orchestrator.generate_report(
            result,
            output_format=output_format,
            output_file=output_file
        )
        
        if output_file:
            print(f"✅ Report saved to: {output_file}")
        else:
            print("\n" + "="*80 + "\n")
            print(report)
        
    except Exception as e:
        print(f"❌ An error occurred: {str(e)}")
        if settings.DEBUG:
            import traceback
            traceback.print_exc()

def main():
    """Parse command-line arguments and run the analysis."""
    parser = argparse.ArgumentParser(description="SEO Analysis Tool")
    
    # Required arguments
    parser.add_argument("url", help="URL to analyze")
    parser.add_argument(
        "keywords", 
        nargs="+",
        help="Seed keywords for analysis (space-separated)"
    )
    
    # Optional arguments
    parser.add_argument(
        "--geography", 
        "-g", 
        default="US",
        help="Target geography (e.g., US, GB, CA)"
    )
    parser.add_argument(
        "--max-keywords",
        "-k",
        type=int,
        default=50,
        help="Maximum number of keywords to analyze (default: 50)"
    )
    parser.add_argument(
        "--max-competitors",
        "-c",
        type=int,
        default=5,
        help="Maximum number of competitors to analyze (default: 5, 0 to disable)"
    )
    parser.add_argument(
        "--output-format",
        "-f",
        choices=["markdown", "html", "json"],
        default="markdown",
        help="Output format (default: markdown)"
    )
    parser.add_argument(
        "--output-file",
        "-o",
        help="Save report to file (default: print to console)"
    )
    parser.add_argument(
        "--language",
        "-l",
        default="en",
        help="Language code (e.g., en, es, fr) (default: en)"
    )
    
    args = parser.parse_args()
    
    # Run the analysis
    asyncio.run(
        run_analysis(
            url=args.url,
            keywords=args.keywords,
            geography=args.geography,
            max_keywords=args.max_keywords,
            max_competitors=args.max_competitors,
            output_format=args.output_format,
            output_file=args.output_file,
            language=args.language
        )
    )

if __name__ == "__main__":
    main()
