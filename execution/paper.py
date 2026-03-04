"""
Paper Trading Execution Engine

Simulates order execution with realistic fills.
No real capital at risk.
"""

import logging
from typing import Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class PaperTrader:
    """
    Simulated trading engine for paper trading.
    
    Tracks virtual balance and simulates realistic fills.
    """
    
    def __init__(self, initial_balance: float, db):
        """
        Initialize paper trader.
        
        Args:
            initial_balance: Starting balance in USDC
            db: Database connection
        """
        self.balance = initial_balance
        self.initial_balance = initial_balance
        self.db = db
        self.open_positions = {}
        
        logger.info(f"📝 Paper trader initialized with ${initial_balance:,.2f}")
    
    async def get_balance(self) -> float:
        """Get current balance."""
        return self.balance
    
    async def place_order(self, market_id: str, direction: str, 
                         size_usdc: float, explanation: Dict) -> Dict:
        """
        Simulate order placement.
        
        Args:
            market_id: Market identifier
            direction: 'YES' or 'NO'
            size_usdc: Position size in USDC
            explanation: Dict with edge, factors, etc.
        
        Returns:
            Dict with success status and order details
        """
        try:
            # Check if we have sufficient balance
            if size_usdc > self.balance:
                logger.warning(
                    f"⚠️ Insufficient balance: ${size_usdc:.2f} > ${self.balance:.2f}"
                )
                return {
                    'success': False,
                    'error': 'Insufficient balance'
                }
            
            # Simulate realistic entry price (with slippage)
            polymarket_mid = explanation.get('polymarket_mid', 0.5)
            slippage = 0.01  # 1% slippage
            
            if direction == 'YES':
                entry_price = polymarket_mid * (1 + slippage)
            else:
                entry_price = (1 - polymarket_mid) * (1 + slippage)
            
            # Clip to valid range
            entry_price = max(0.01, min(0.99, entry_price))
            
            # Calculate shares purchased
            shares = size_usdc / entry_price
            
            # Update balance
            self.balance -= size_usdc
            
            # Store position
            position_id = f"{market_id}_{datetime.utcnow().timestamp()}"
            self.open_positions[position_id] = {
                'market_id': market_id,
                'direction': direction,
                'shares': shares,
                'entry_price': entry_price,
                'size_usdc': size_usdc,
                'timestamp': datetime.utcnow(),
                'explanation': explanation
            }
            
            # Log to database
            await self._log_trade(
                market_id=market_id,
                asset=explanation.get('asset', 'UNKNOWN'),
                direction=direction,
                size_usdc=size_usdc,
                entry_price=entry_price,
                edge=explanation.get('edge', 0),
                regime=explanation.get('regime', 1),
                explanation=explanation
            )
            
            logger.info(
                f"📝 Paper trade: {direction} {shares:.2f} shares @ ${entry_price:.3f} "
                f"(${size_usdc:.2f})"
            )
            
            return {
                'success': True,
                'position_id': position_id,
                'entry_price': entry_price,
                'shares': shares
            }
            
        except Exception as e:
            logger.error(f"Error placing paper order: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _log_trade(self, **kwargs):
        """
        Log trade to database.
        
        Args:
            **kwargs: Trade parameters
        """
        try:
            # Would insert into trades table here
            # For now, just log
            logger.debug(f"Trade logged: {kwargs}")
        except Exception as e:
            logger.error(f"Error logging trade: {e}")
