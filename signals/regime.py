"""
Market Regime Detection

Uses Hidden Markov Model to classify market states:
- State 0: Low volatility
- State 1: Medium volatility
- State 2: High volatility

Adjusts position sizing based on regime.
"""

import logging
import numpy as np
from typing import List
from sklearn.mixture import GaussianMixture

logger = logging.getLogger(__name__)


class RegimeDetector:
    """
    HMM-based regime detection using Gaussian Mixture Model.
    
    Classifies current market state based on return distribution.
    """
    
    def __init__(self, n_regimes: int = 3):
        """
        Initialize regime detector.
        
        Args:
            n_regimes: Number of hidden states (default: 3)
        """
        self.n_regimes = n_regimes
        self.model = GaussianMixture(
            n_components=n_regimes,
            covariance_type='full',
            random_state=42
        )
        self.fitted = False
    
    async def detect(self, returns: List[float]) -> int:
        """
        Detect current market regime.
        
        Args:
            returns: List of recent returns
        
        Returns:
            Regime state (0=low vol, 1=med vol, 2=high vol)
        """
        if len(returns) < 50:
            logger.warning("Insufficient data for regime detection")
            return 1  # Default to medium volatility
        
        try:
            # Prepare features: returns and squared returns (volatility proxy)
            X = np.array(returns).reshape(-1, 1)
            X_squared = X ** 2
            features = np.hstack([X, X_squared])
            
            # Fit model if not yet fitted
            if not self.fitted:
                self.model.fit(features)
                self.fitted = True
                logger.info("✅ Regime detection model fitted")
            
            # Predict current regime
            current_regime = self.model.predict(features[-1:]).item()
            
            # Map to volatility ordering (0=low, 1=med, 2=high)
            regime_map = self._sort_regimes_by_volatility()
            mapped_regime = regime_map[current_regime]
            
            logger.debug(f"Current regime: {mapped_regime}")
            return mapped_regime
            
        except Exception as e:
            logger.error(f"Error detecting regime: {e}")
            return 1  # Default to medium
    
    def _sort_regimes_by_volatility(self) -> dict:
        """
        Sort regimes by volatility (ascending).
        
        Returns:
            Mapping from raw regime index to sorted index
        """
        # Get variance of each regime from covariances
        variances = [self.model.covariances_[i][0, 0] 
                     for i in range(self.n_regimes)]
        
        # Sort indices by variance
        sorted_indices = np.argsort(variances)
        
        # Create mapping: raw_index -> sorted_position
        mapping = {sorted_indices[i]: i for i in range(self.n_regimes)}
        
        return mapping
