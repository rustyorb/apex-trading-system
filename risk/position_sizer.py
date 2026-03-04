"""
Position Sizing with Kelly Criterion

Calculates optimal position size based on:
- Edge (model probability vs market price)
- Win rate (historical)
- Kelly fraction (for safety)
- Hard caps (max position %)
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PositionSizer:
    """
    Kelly Criterion position sizer with safety constraints.
    """
    
    def __init__(self, max_position_pct: float = 0.03,
                 kelly_fraction: float = 0.25):
        """
        Initialize position sizer.
        
        Args:
            max_position_pct: Maximum position as % of balance (e.g., 0.03 = 3%)
            kelly_fraction: Fraction of Kelly to use (e.g., 0.25 = quarter-Kelly)
        """
        self.max_position_pct = max_position_pct
        self.kelly_fraction = kelly_fraction
    
    def calculate(self, edge: float, balance: float, 
                 regime: int = 1, win_rate: Optional[float] = None) -> float:
        """
        Calculate optimal position size.
        
        Args:
            edge: Absolute edge (model_prob - polymarket_mid)
            balance: Current balance in USDC
            regime: Market regime (0=low vol, 1=med, 2=high vol)
            win_rate: Historical win rate (if None, estimated from edge)
        
        Returns:
            Position size in USDC
        """
        # Estimate win rate if not provided
        if win_rate is None:
            # Simple heuristic: higher edge = higher win rate
            # Clamp between 0.5 and 0.75
            win_rate = 0.5 + min(edge, 0.25)
        
        # Kelly formula: f* = (p*b - q) / b
        # Where:
        #   p = win probability
        #   q = 1 - p (loss probability)
        #   b = odds received (for binary: 1)
        
        p = win_rate
        q = 1 - p
        b = 1.0  # Binary outcome
        
        kelly_fraction_raw = (p * b - q) / b
        
        # Apply safety fraction (quarter-Kelly)
        kelly_fraction_safe = kelly_fraction_raw * self.kelly_fraction
        
        # Adjust for regime (reduce in high volatility)
        regime_multipliers = {
            0: 1.0,   # Low vol: full sizing
            1: 0.8,   # Med vol: 80%
            2: 0.5    # High vol: 50%
        }
        regime_adj = regime_multipliers.get(regime, 0.8)
        
        kelly_fraction_adjusted = kelly_fraction_safe * regime_adj
        
        # Calculate position size
        position_size = balance * kelly_fraction_adjusted
        
        # Apply hard cap
        max_size = balance * self.max_position_pct
        position_size = min(position_size, max_size)
        
        # Floor at $10 minimum
        position_size = max(position_size, 10.0)
        
        logger.debug(
            f"Position sizing: edge={edge:.1%}, win_rate={win_rate:.1%}, "
            f"kelly={kelly_fraction_adjusted:.3f}, size=${position_size:.2f}"
        )
        
        return position_size
