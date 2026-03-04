"""
Social Sentiment Signals

Aggregates social sentiment from:
- Farcaster (via Neynar API)
- News sentiment (Benzinga)

Returns sentiment score in [-1, 1] range.
"""

import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)


class SocialSignals:
    """
    Social sentiment aggregator.
    """
    
    def __init__(self, neynar_api_key: Optional[str] = None,
                 benzinga_api_key: Optional[str] = None):
        """
        Initialize social signal collector.
        
        Args:
            neynar_api_key: Neynar API key for Farcaster data
            benzinga_api_key: Benzinga API key for news
        """
        self.neynar_key = neynar_api_key
        self.benzinga_key = benzinga_api_key
    
    async def get_sentiment(self, asset: str) -> float:
        """
        Get aggregated sentiment score for asset.
        
        Args:
            asset: Asset symbol (e.g., 'BTC', 'ETH')
        
        Returns:
            Sentiment score in [-1, 1] where:
            -1 = extremely bearish
             0 = neutral
            +1 = extremely bullish
        """
        scores = []
        
        # Farcaster sentiment
        if self.neynar_key:
            farcaster_score = await self._get_farcaster_sentiment(asset)
            if farcaster_score is not None:
                scores.append(farcaster_score)
        
        # News sentiment
        if self.benzinga_key:
            news_score = await self._get_news_sentiment(asset)
            if news_score is not None:
                scores.append(news_score)
        
        # Return average (or 0 if no data)
        return sum(scores) / len(scores) if scores else 0.0
    
    async def _get_farcaster_sentiment(self, asset: str) -> Optional[float]:
        """
        Get sentiment from Farcaster posts.
        
        Args:
            asset: Asset symbol
        
        Returns:
            Sentiment score or None
        """
        try:
            # Query Neynar for recent casts mentioning asset
            url = "https://api.neynar.com/v2/farcaster/cast/search"
            headers = {"api_key": self.neynar_key}
            params = {
                "q": asset.lower(),
                "limit": 25
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=5)
            
            if response.status_code == 200:
                casts = response.json().get('result', {}).get('casts', [])
                
                if not casts:
                    return None
                
                # Simple sentiment: count bullish vs bearish keywords
                bullish_keywords = ['bullish', 'moon', 'pump', 'buy', 'long', '🚀', '📈']
                bearish_keywords = ['bearish', 'dump', 'sell', 'short', 'rekt', '📉', '🐻']
                
                bullish_count = 0
                bearish_count = 0
                
                for cast in casts:
                    text = cast.get('text', '').lower()
                    bullish_count += sum(1 for kw in bullish_keywords if kw in text)
                    bearish_count += sum(1 for kw in bearish_keywords if kw in text)
                
                total = bullish_count + bearish_count
                if total == 0:
                    return 0.0
                
                # Normalize to [-1, 1]
                sentiment = (bullish_count - bearish_count) / total
                
                logger.debug(
                    f"{asset} Farcaster sentiment: {sentiment:.2f} "
                    f"({len(casts)} casts, {bullish_count} bull, {bearish_count} bear)"
                )
                
                return sentiment
            
        except Exception as e:
            logger.error(f"Error fetching Farcaster sentiment: {e}")
        
        return None
    
    async def _get_news_sentiment(self, asset: str) -> Optional[float]:
        """
        Get sentiment from news articles.
        
        Args:
            asset: Asset symbol
        
        Returns:
            Sentiment score or None
        """
        # Placeholder - would integrate Benzinga API
        # Returns neutral for now
        return 0.0
