"""
Factor Signal Calculation

Computes quantitative factors from price/volume data:
- Momentum (z-scored returns)
- Volatility (rolling standard deviation)
- Volume divergence (price vs volume correlation)
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict

logger = logging.getLogger(__name__)


class FactorCalculator:
    """
    Calculates standardized factor signals from OHLCV data.
    """
    
    def __init__(self, lookback_window: int = 100):
        """
        Initialize factor calculator.
        
        Args:
            lookback_window: Number of periods for z-score normalization
        """
        self.lookback_window = lookback_window
    
    async def compute(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Compute all factors for given price data.
        
        Args:
            df: DataFrame with columns ['timestamp', 'price', 'volume']
        
        Returns:
            Dict of factor_name: z_score
        """
        if len(df) < 20:
            logger.warning("Insufficient data for factor calculation")
            return {}
        
        try:
            # Calculate returns
            df['returns'] = df['price'].pct_change()
            
            # ══════════════════════════════════════════════
            # MOMENTUM
            # ══════════════════════════════════════════════
            # 20-period cumulative return
            momentum = df['returns'].rolling(20).sum().iloc[-1]
            momentum_zscore = self._zscore(momentum, df['returns'].rolling(20).sum())
            
            # ══════════════════════════════════════════════
            # VOLATILITY
            # ══════════════════════════════════════════════
            # 48-period rolling std of returns
            volatility = df['returns'].rolling(48).std().iloc[-1]
            volatility_zscore = self._zscore(volatility, df['returns'].rolling(48).std())
            
            # ══════════════════════════════════════════════
            # VOLUME DIVERGENCE
            # ══════════════════════════════════════════════
            # Correlation between price and volume (20-period)
            volume_changes = df['volume'].pct_change()
            correlation = df['returns'].rolling(20).corr(volume_changes).iloc[-1]
            volume_div_zscore = self._zscore(correlation, 
                                             df['returns'].rolling(20).corr(volume_changes))
            
            return {
                'momentum_zscore': momentum_zscore,
                'volatility_zscore': volatility_zscore,
                'volume_div_zscore': volume_div_zscore,
                # Placeholder for on-chain/funding (would integrate APIs)
                'onchain_zscore': 0.0,
                'funding_zscore': 0.0
            }
            
        except Exception as e:
            logger.error(f"Error computing factors: {e}")
            return {}
    
    def _zscore(self, value: float, series: pd.Series) -> float:
        """
        Calculate z-score of value relative to series.
        
        Args:
            value: Current value
            series: Historical series for normalization
        
        Returns:
            Z-score (number of standard deviations from mean)
        """
        series = series.dropna().tail(self.lookback_window)
        
        if len(series) < 2:
            return 0.0
        
        mean = series.mean()
        std = series.std()
        
        if std == 0:
            return 0.0
        
        return (value - mean) / std
