"""
APEX Trading System - Configuration Management

Loads and validates configuration from environment variables.
"""

import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Config:
    """
    Configuration container for APEX system.
    
    Loads settings from environment variables with validation.
    """
    
    def __init__(self):
        """Load and validate configuration."""
        
        # ═══════════════════════════════════════════════════════════
        # PAPER/LIVE MODE
        # ═══════════════════════════════════════════════════════════
        self.IS_PAPER = self._get_bool('IS_PAPER', default=True)
        self.PAPER_BALANCE = self._get_float('PAPER_BALANCE', default=10000.0)
        
        # ═══════════════════════════════════════════════════════════
        # API CREDENTIALS
        # ═══════════════════════════════════════════════════════════
        self.POLYMARKET_PK = self._get_str('POLYMARKET_PK')
        self.POLYMARKET_PROXY_ADDRESS = self._get_str('POLYMARKET_PROXY_ADDRESS')
        
        self.BINANCE_API_KEY = self._get_str('BINANCE_API_KEY', required=False)
        self.BINANCE_API_SECRET = self._get_str('BINANCE_API_SECRET', required=False)
        
        self.BENZINGA_API_KEY = self._get_str('BENZINGA_API_KEY', required=False)
        self.CRYPTOQUANT_API_KEY = self._get_str('CRYPTOQUANT_API_KEY', required=False)
        self.NEYNAR_API_KEY = self._get_str('NEYNAR_API_KEY', required=False)
        
        # ═══════════════════════════════════════════════════════════
        # INFRASTRUCTURE
        # ═══════════════════════════════════════════════════════════
        self.REDIS_URL = self._get_str('REDIS_URL', default='redis://localhost:6379')
        self.DATABASE_URL = self._get_str(
            'DATABASE_URL',
            default='postgresql://apex_user:password@localhost:5432/apex'
        )
        
        # ═══════════════════════════════════════════════════════════
        # RISK PARAMETERS
        # ═══════════════════════════════════════════════════════════
        self.MAX_POSITION_PCT = self._get_float('MAX_POSITION_PCT', default=0.03)
        self.MIN_EDGE_THRESHOLD = self._get_float('MIN_EDGE_THRESHOLD', default=0.12)
        self.KELLY_FRACTION = self._get_float('KELLY_FRACTION', default=0.25)
        self.DRAWDOWN_HALT_PCT = self._get_float('DRAWDOWN_HALT_PCT', default=0.18)
        
        # ═══════════════════════════════════════════════════════════
        # ADVANCED SETTINGS
        # ═══════════════════════════════════════════════════════════
        self.LOG_LEVEL = self._get_str('LOG_LEVEL', default='INFO')
        self.MAX_OPEN_POSITIONS = self._get_int('MAX_OPEN_POSITIONS', default=5)
        self.MIN_MARKET_LIQUIDITY = self._get_float('MIN_MARKET_LIQUIDITY', default=50000.0)
        
        # Validate configuration
        self._validate()
        
        logger.info("Configuration loaded successfully")
    
    def _get_str(self, key: str, default: Optional[str] = None, required: bool = True) -> Optional[str]:
        """Get string from environment."""
        value = os.getenv(key, default)
        if required and not value:
            raise ValueError(f"Missing required config: {key}")
        return value
    
    def _get_int(self, key: str, default: Optional[int] = None) -> int:
        """Get integer from environment."""
        value = os.getenv(key)
        if value is None:
            if default is None:
                raise ValueError(f"Missing required config: {key}")
            return default
        return int(value)
    
    def _get_float(self, key: str, default: Optional[float] = None) -> float:
        """Get float from environment."""
        value = os.getenv(key)
        if value is None:
            if default is None:
                raise ValueError(f"Missing required config: {key}")
            return default
        return float(value)
    
    def _get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean from environment."""
        value = os.getenv(key)
        if value is None:
            return default
        return value.lower() in ('true', '1', 'yes', 'on')
    
    def _validate(self):
        """Validate configuration values."""
        # Risk parameter validation
        if not 0 < self.MAX_POSITION_PCT <= 0.10:
            raise ValueError("MAX_POSITION_PCT must be between 0 and 0.10 (10%)")
        
        if not 0 < self.MIN_EDGE_THRESHOLD <= 0.50:
            raise ValueError("MIN_EDGE_THRESHOLD must be between 0 and 0.50 (50%)")
        
        if not 0 < self.KELLY_FRACTION <= 1.0:
            raise ValueError("KELLY_FRACTION must be between 0 and 1.0")
        
        if not 0 < self.DRAWDOWN_HALT_PCT <= 0.50:
            raise ValueError("DRAWDOWN_HALT_PCT must be between 0 and 0.50 (50%)")
        
        # Warn if running live without proper credentials
        if not self.IS_PAPER:
            if not self.POLYMARKET_PK or not self.POLYMARKET_PROXY_ADDRESS:
                raise ValueError("POLYMARKET credentials required for live trading")
            
            logger.warning(
                "⚠️  LIVE TRADING MODE ENABLED - REAL MONEY AT RISK ⚠️"
            )
    
    def __repr__(self) -> str:
        """String representation (masks sensitive data)."""
        return f"""
        APEX Configuration:
          Mode: {'PAPER' if self.IS_PAPER else 'LIVE'}
          Risk: edge≥{self.MIN_EDGE_THRESHOLD:.1%}, pos≤{self.MAX_POSITION_PCT:.1%}, halt@{self.DRAWDOWN_HALT_PCT:.1%}
          DB: {self.DATABASE_URL.split('@')[-1] if '@' in self.DATABASE_URL else 'local'}
        """
