#!/usr/bin/env python3
"""
Sentiment Analysis Service for Company News Sources
Uses GenAI to analyze news sentiment and extract insights
"""

import logging
import requests
from typing import List, Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

class SentimentService:
    """Service for analyzing sentiment of company news and sources"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize sentiment service
        
        Args:
            api_key: Optional API key for external GenAI services
        """
        self.api_key = api_key
        
    def analyze_sources_sentiment(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze sentiment of news sources using GenAI
        
        Args:
            sources: List of source dictionaries with title, url, snippet
            
        Returns:
            Dictionary with sentiment analysis results
        """
        if not sources:
            return {
                "overall_sentiment": "neutral",
                "sentiment_score": 0.0,
                "confidence": 0.0,
                "analysis": "No sources available for analysis",
                "source_sentiments": []
            }
        
        try:
            # Analyze each source
            source_sentiments = []
            sentiment_scores = []
            
            for i, source in enumerate(sources):
                source_analysis = self._analyze_single_source(source, i + 1)
                source_sentiments.append(source_analysis)
                sentiment_scores.append(source_analysis["sentiment_score"])
            
            # Calculate overall sentiment
            if sentiment_scores:
                avg_score = sum(sentiment_scores) / len(sentiment_scores)
                overall_sentiment = self._score_to_sentiment(avg_score)
                confidence = min(0.9, len(sources) * 0.15)  # Higher confidence with more sources
            else:
                avg_score = 0.0
                overall_sentiment = "neutral"
                confidence = 0.0
            
            # Generate summary analysis
            analysis = self._generate_sentiment_summary(source_sentiments, overall_sentiment, avg_score)
            
            return {
                "overall_sentiment": overall_sentiment,
                "sentiment_score": avg_score,
                "confidence": confidence,
                "analysis": analysis,
                "source_sentiments": source_sentiments,
                "total_sources": len(sources)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sources sentiment: {str(e)}")
            return {
                "overall_sentiment": "neutral",
                "sentiment_score": 0.0,
                "confidence": 0.0,
                "analysis": f"Error analyzing sentiment: {str(e)}",
                "source_sentiments": []
            }
    
    def _analyze_single_source(self, source: Dict[str, Any], index: int) -> Dict[str, Any]:
        """
        Analyze sentiment of a single news source
        
        Args:
            source: Source dictionary with title, url, snippet
            index: Source index number
            
        Returns:
            Dictionary with source sentiment analysis
        """
        title = source.get('title', '')
        snippet = source.get('snippet', '')
        url = source.get('url', '')
        
        # Combine title and snippet for analysis
        text_content = f"{title}. {snippet}".strip()
        
        if not text_content:
            return {
                "source_index": index,
                "title": title,
                "sentiment": "neutral",
                "sentiment_score": 0.0,
                "confidence": 0.0,
                "key_phrases": [],
                "reasoning": "No content available for analysis"
            }
        
        # Simple rule-based sentiment analysis (can be enhanced with actual GenAI API)
        sentiment_result = self._rule_based_sentiment(text_content)
        
        return {
            "source_index": index,
            "title": title[:100] + "..." if len(title) > 100 else title,
            "sentiment": sentiment_result["sentiment"],
            "sentiment_score": sentiment_result["score"],
            "confidence": sentiment_result["confidence"],
            "key_phrases": sentiment_result["key_phrases"],
            "reasoning": sentiment_result["reasoning"]
        }
    
    def _rule_based_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Advanced rule-based sentiment analysis with financial context
        Enhanced for mature business and market analysis
        
        Args:
            text: Text content to analyze
            
        Returns:
            Dictionary with sentiment analysis results
        """
        text_lower = text.lower()
        
        # Enhanced sentiment keywords with weights
        strong_positive = {
            'record': 1.0, 'breakthrough': 1.0, 'exceptional': 1.0, 'outstanding': 1.0,
            'surge': 0.9, 'soar': 0.9, 'boom': 0.9, 'stellar': 0.9, 'robust': 0.8,
            'accelerate': 0.8, 'momentum': 0.7, 'optimize': 0.7, 'milestone': 0.8
        }
        
        positive = {
            'growth': 0.7, 'profit': 0.6, 'revenue': 0.5, 'earnings': 0.6, 'success': 0.7,
            'strong': 0.6, 'increase': 0.5, 'gain': 0.6, 'beat': 0.7, 'exceed': 0.7,
            'expansion': 0.6, 'innovation': 0.6, 'achievement': 0.6, 'improve': 0.5,
            'upgrade': 0.6, 'bullish': 0.8, 'outperform': 0.7, 'upside': 0.6
        }
        
        strong_negative = {
            'crisis': -1.0, 'collapse': -1.0, 'plummet': -1.0, 'crash': -1.0,
            'devastating': -0.9, 'alarming': -0.9, 'catastrophic': -0.9, 'severe': -0.8,
            'massive layoffs': -0.9, 'bankruptcy': -1.0, 'scandal': -0.8
        }
        
        negative = {
            'loss': -0.6, 'decline': -0.6, 'fall': -0.5, 'drop': -0.5, 'weak': -0.6,
            'concern': -0.5, 'risk': -0.5, 'threat': -0.6, 'challenge': -0.4,
            'layoff': -0.7, 'cut': -0.5, 'reduce': -0.4, 'struggle': -0.6,
            'warning': -0.6, 'bearish': -0.8, 'underperform': -0.7, 'downside': -0.6,
            'volatility': -0.4, 'uncertainty': -0.5, 'pressure': -0.4
        }
        
        # Market-specific context modifiers
        market_context = {
            'q1': 0.1, 'q2': 0.1, 'q3': 0.1, 'q4': 0.1,  # Quarterly context
            'annual': 0.1, 'fiscal': 0.1, 'guidance': 0.2,
            'analyst': 0.2, 'forecast': 0.1, 'outlook': 0.2,
            'sec filing': 0.3, 'earnings call': 0.2, 'investor': 0.2
        }
        
        # Calculate weighted sentiment score
        score = 0.0
        found_phrases = []
        context_boost = 0.0
        
        # Check strong positive
        for phrase, weight in strong_positive.items():
            if phrase in text_lower:
                score += weight
                found_phrases.append(f"+{phrase}")
        
        # Check positive
        for phrase, weight in positive.items():
            if phrase in text_lower:
                score += weight
                found_phrases.append(f"+{phrase}")
        
        # Check strong negative
        for phrase, weight in strong_negative.items():
            if phrase in text_lower:
                score += weight  # weight is already negative
                found_phrases.append(f"-{phrase}")
        
        # Check negative
        for phrase, weight in negative.items():
            if phrase in text_lower:
                score += weight  # weight is already negative
                found_phrases.append(f"-{phrase}")
        
        # Apply market context boost
        for phrase, boost in market_context.items():
            if phrase in text_lower:
                context_boost += boost
        
        # Normalize score and apply context
        if len(found_phrases) > 0:
            score = score / max(len(found_phrases), 1)  # Average the sentiment
            score += context_boost * 0.1  # Small boost for market context
        
        # Clamp score to [-1, 1]
        score = max(-1.0, min(1.0, score))
        
        # Determine sentiment category with more nuanced thresholds
        if score >= 0.4:
            sentiment = "very positive"
        elif score >= 0.15:
            sentiment = "positive"
        elif score >= -0.15:
            sentiment = "neutral"
        elif score >= -0.4:
            sentiment = "negative"
        else:
            sentiment = "very negative"
        
        # Calculate confidence based on number of indicators and context
        base_confidence = min(0.9, len(found_phrases) * 0.12)
        context_confidence = min(0.2, context_boost)
        confidence = min(0.95, base_confidence + context_confidence)
        
        # Generate sophisticated reasoning
        reasoning = self._generate_sophisticated_reasoning(
            sentiment, score, found_phrases, context_boost, text_lower
        )
        
        return {
            "sentiment": sentiment,
            "score": score,
            "confidence": confidence,
            "key_phrases": found_phrases[:8],  # Top 8 most relevant
            "reasoning": reasoning
        }
    
    def _generate_sophisticated_reasoning(self, sentiment: str, score: float, 
                                        found_phrases: List[str], context_boost: float, 
                                        text_lower: str) -> str:
        """
        Generate sophisticated reasoning for sentiment analysis
        
        Args:
            sentiment: Determined sentiment category
            score: Numerical sentiment score
            found_phrases: List of key phrases found
            context_boost: Market context boost value
            text_lower: Original text in lowercase
            
        Returns:
            Detailed reasoning string
        """
        if not found_phrases:
            return "No significant sentiment indicators detected. Content appears factual or neutral."
        
        # Separate positive and negative phrases
        positive_phrases = [p[1:] for p in found_phrases if p.startswith('+')]
        negative_phrases = [p[1:] for p in found_phrases if p.startswith('-')]
        
        # Build reasoning based on sentiment
        if sentiment in ["very positive", "positive"]:
            reasoning = f"Analysis indicates {sentiment} sentiment (score: {score:.2f}). "
            if positive_phrases:
                reasoning += f"Strong positive indicators: {', '.join(positive_phrases[:3])}. "
            if negative_phrases:
                reasoning += f"Some concerns noted: {', '.join(negative_phrases[:2])}, but positive signals dominate. "
            if context_boost > 0.1:
                reasoning += "Enhanced by strong market/financial context. "
        
        elif sentiment in ["very negative", "negative"]:
            reasoning = f"Analysis indicates {sentiment} sentiment (score: {score:.2f}). "
            if negative_phrases:
                reasoning += f"Key concerns: {', '.join(negative_phrases[:3])}. "
            if positive_phrases:
                reasoning += f"Some positive aspects: {', '.join(positive_phrases[:2])}, but concerns outweigh. "
            if context_boost > 0.1:
                reasoning += "Market context provides some stability. "
        
        else:  # neutral
            reasoning = f"Neutral sentiment detected (score: {score:.2f}). "
            if positive_phrases and negative_phrases:
                reasoning += f"Balanced indicators - positive: {', '.join(positive_phrases[:2])}, "
                reasoning += f"concerns: {', '.join(negative_phrases[:2])}. "
            elif positive_phrases:
                reasoning += f"Mild positive indicators: {', '.join(positive_phrases[:2])}, but not strongly directional. "
            elif negative_phrases:
                reasoning += f"Some concerns: {', '.join(negative_phrases[:2])}, but not alarming. "
            
            if context_boost > 0.1:
                reasoning += "Professional market context suggests measured, analytical tone. "
        
        # Add confidence context
        if len(found_phrases) >= 5:
            reasoning += "High confidence due to multiple sentiment indicators."
        elif len(found_phrases) >= 3:
            reasoning += "Moderate confidence with several clear indicators."
        else:
            reasoning += "Lower confidence due to limited sentiment signals."
        
        return reasoning
    
    def calculate_growth_score(self, sources: List[Dict[str, Any]], hiring_data: Dict[str, Any], 
                             financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate a comprehensive growth score combining sentiment, hiring, and financial indicators
        
        Args:
            sources: List of news sources for sentiment analysis
            hiring_data: Company hiring and expansion data
            financial_data: Company financial metrics
            
        Returns:
            Dictionary with growth score and breakdown
        """
        try:
            # 1. Sentiment component (40% weight)
            sentiment_analysis = self.analyze_sources_sentiment(sources)
            sentiment_score = sentiment_analysis.get('sentiment_score', 0.0)
            sentiment_weight = 0.4
            
            # 2. Hiring indicators (35% weight)
            hiring_score = self._calculate_hiring_score(hiring_data)
            hiring_weight = 0.35
            
            # 3. Financial momentum (25% weight)
            financial_score = self._calculate_financial_momentum(financial_data)
            financial_weight = 0.25
            
            # Calculate weighted growth score (-1 to 1)
            growth_score = (
                sentiment_score * sentiment_weight +
                hiring_score * hiring_weight +
                financial_score * financial_weight
            )
            
            # Convert to 0-100 scale for display
            display_score = int((growth_score + 1) * 50)
            
            # Determine growth category
            if growth_score >= 0.4:
                growth_category = "Strong Growth"
                growth_emoji = "🚀"
            elif growth_score >= 0.15:
                growth_category = "Moderate Growth"
                growth_emoji = "📈"
            elif growth_score >= -0.15:
                growth_category = "Stable"
                growth_emoji = "📊"
            elif growth_score >= -0.4:
                growth_category = "Cautious"
                growth_emoji = "📉"
            else:
                growth_category = "Declining"
                growth_emoji = "⚠️"
            
            return {
                "growth_score": growth_score,
                "display_score": display_score,
                "growth_category": growth_category,
                "growth_emoji": growth_emoji,
                "components": {
                    "sentiment": {
                        "score": sentiment_score,
                        "weight": sentiment_weight,
                        "contribution": sentiment_score * sentiment_weight
                    },
                    "hiring": {
                        "score": hiring_score,
                        "weight": hiring_weight,
                        "contribution": hiring_score * hiring_weight
                    },
                    "financial": {
                        "score": financial_score,
                        "weight": financial_weight,
                        "contribution": financial_score * financial_weight
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating growth score: {str(e)}")
            return {
                "growth_score": 0.0,
                "display_score": 50,
                "growth_category": "Unknown",
                "growth_emoji": "❓",
                "components": {}
            }
    
    def _calculate_hiring_score(self, hiring_data: Dict[str, Any]) -> float:
        """
        Calculate hiring momentum score from hiring data
        
        Returns:
            Score from -1 to 1
        """
        if not hiring_data:
            return 0.0
        
        score = 0.0
        
        # Hiring status indicators
        hiring_status = hiring_data.get('hiring_status', '').lower()
        if 'actively hiring' in hiring_status:
            score += 0.4
        elif 'hiring' in hiring_status:
            score += 0.2
        elif 'not hiring' in hiring_status or 'freeze' in hiring_status:
            score -= 0.3
        
        # Expansion plans
        expansion = hiring_data.get('expansion_plans', '').lower()
        if expansion in ['yes', 'true', 'expanding', 'growth']:
            score += 0.3
        elif expansion in ['no', 'false', 'contracting']:
            score -= 0.2
        
        # Recent layoffs (negative indicator)
        layoffs = hiring_data.get('recent_layoffs', '').lower()
        if layoffs not in ['not found', 'no', 'none', '']:
            if any(word in layoffs for word in ['major', 'significant', 'massive']):
                score -= 0.5
            else:
                score -= 0.3
        
        # Remote work policy (slight positive for flexibility)
        remote_policy = hiring_data.get('remote_work_policy', '').lower()
        if any(word in remote_policy for word in ['remote', 'hybrid', 'flexible']):
            score += 0.1
        
        return max(-1.0, min(1.0, score))
    
    def _calculate_financial_momentum(self, financial_data: Dict[str, Any]) -> float:
        """
        Calculate financial momentum score from financial data
        
        Returns:
            Score from -1 to 1
        """
        if not financial_data:
            return 0.0
        
        score = 0.0
        
        # Revenue growth indicators
        revenue_growth = financial_data.get('revenue_growth', '')
        if revenue_growth and revenue_growth != 'N/A':
            try:
                # Extract percentage if present
                import re
                growth_match = re.search(r'(\d+)%', str(revenue_growth))
                if growth_match:
                    growth_pct = int(growth_match.group(1))
                    if growth_pct > 20:
                        score += 0.4
                    elif growth_pct > 10:
                        score += 0.3
                    elif growth_pct > 5:
                        score += 0.2
                    elif growth_pct > 0:
                        score += 0.1
                    else:
                        score -= 0.2
            except:
                pass
        
        # Profit indicators
        profit = financial_data.get('profit', '')
        net_income = financial_data.get('net_income', '')
        if profit and profit not in ['N/A', 'Not found']:
            if 'billion' in str(profit).lower():
                score += 0.2
            elif 'million' in str(profit).lower():
                score += 0.1
        
        # Market cap (size indicator)
        market_cap = financial_data.get('market_cap', '')
        if market_cap and 'trillion' in str(market_cap).lower():
            score += 0.1
        
        return max(-1.0, min(1.0, score))
    
    def _score_to_sentiment(self, score: float) -> str:
        """Convert numerical score to sentiment label"""
        if score > 0.2:
            return "positive"
        elif score < -0.2:
            return "negative"
        else:
            return "neutral"
    
    def _generate_sentiment_summary(self, source_sentiments: List[Dict], overall_sentiment: str, avg_score: float) -> str:
        """
        Generate a sophisticated, mature summary of sentiment analysis
        
        Args:
            source_sentiments: List of individual source sentiment analyses
            overall_sentiment: Overall sentiment classification
            avg_score: Average sentiment score
            
        Returns:
            Professional sentiment analysis summary
        """
        if not source_sentiments:
            return "Insufficient source material available for comprehensive sentiment analysis."
        
        # Enhanced sentiment categorization
        very_positive_count = sum(1 for s in source_sentiments if s["sentiment"] == "very positive")
        positive_count = sum(1 for s in source_sentiments if s["sentiment"] == "positive")
        neutral_count = sum(1 for s in source_sentiments if s["sentiment"] == "neutral")
        negative_count = sum(1 for s in source_sentiments if s["sentiment"] == "negative")
        very_negative_count = sum(1 for s in source_sentiments if s["sentiment"] == "very negative")
        
        total_sources = len(source_sentiments)
        total_positive = very_positive_count + positive_count
        total_negative = very_negative_count + negative_count
        
        # Calculate confidence metrics
        avg_confidence = sum(s["confidence"] for s in source_sentiments) / total_sources
        high_confidence_sources = sum(1 for s in source_sentiments if s["confidence"] > 0.7)
        
        summary_parts = []
        
        # Sophisticated overall assessment
        if overall_sentiment == "very positive":
            summary_parts.append(f"📈 Market sentiment analysis reveals STRONGLY POSITIVE outlook (confidence: {avg_score:.2f})")
        elif overall_sentiment == "positive":
            summary_parts.append(f"📈 Market sentiment analysis indicates POSITIVE momentum (confidence: {avg_score:.2f})")
        elif overall_sentiment == "very negative":
            summary_parts.append(f"📉 Market sentiment analysis shows SIGNIFICANT CONCERNS (confidence: {avg_score:.2f})")
        elif overall_sentiment == "negative":
            summary_parts.append(f"📉 Market sentiment analysis reflects CAUTIOUS outlook (confidence: {avg_score:.2f})")
        else:
            summary_parts.append(f"📊 Market sentiment analysis indicates BALANCED perspective (confidence: {avg_score:.2f})")
        
        # Detailed breakdown with professional language
        if very_positive_count > 0 or very_negative_count > 0:
            breakdown = f"Comprehensive analysis of {total_sources} sources: "
            if very_positive_count > 0:
                breakdown += f"{very_positive_count} strongly positive, "
            breakdown += f"{positive_count} positive, {neutral_count} neutral, {negative_count} negative"
            if very_negative_count > 0:
                breakdown += f", {very_negative_count} strongly negative"
        else:
            breakdown = f"Analysis of {total_sources} sources: {total_positive} positive, {neutral_count} neutral, {total_negative} negative"
        
        summary_parts.append(breakdown)
        
        # Sophisticated insights based on distribution
        if total_positive > total_negative * 2:
            summary_parts.append("Market narrative demonstrates strong institutional confidence and positive momentum")
        elif total_negative > total_positive * 2:
            summary_parts.append("Market narrative reflects heightened caution and risk assessment concerns")
        elif total_positive > total_negative:
            summary_parts.append("Market narrative leans optimistic with measured confidence in fundamentals")
        elif total_negative > total_positive:
            summary_parts.append("Market narrative shows prudent skepticism with focus on risk factors")
        else:
            summary_parts.append("Market narrative presents balanced perspective with analytical objectivity")
        
        # Confidence assessment
        if avg_confidence > 0.8:
            summary_parts.append(f"High analytical confidence ({high_confidence_sources}/{total_sources} sources with strong signal clarity)")
        elif avg_confidence > 0.6:
            summary_parts.append(f"Moderate analytical confidence ({high_confidence_sources}/{total_sources} sources with clear indicators)")
        else:
            summary_parts.append(f"Measured analytical confidence (limited sentiment signals across sources)")
        
        return ". ".join(summary_parts) + "."
    
    def fetch_url_content(self, url: str) -> Optional[str]:
        """
        Attempt to fetch content from URL (with fallback handling)
        
        Args:
            url: URL to fetch content from
            
        Returns:
            Content string or None if failed
        """
        try:
            # Simple HTTP request with user agent
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"Failed to fetch {url}: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.warning(f"Error fetching URL {url}: {str(e)}")
            return None
