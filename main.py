#!/usr/bin/env python3
"""
APEX Trading System - Main Entry Point

Asymmetric Pattern EXploitation engine for Polymarket prediction markets.
Combines multi-factor signals, regime detection, and Kelly position sizing.

Usage:
    python main.py

Environment:
    See .env.example for required configuration
"""

import asyncio
import logging
import sys
from datetime import datetime
from typing import Dict, List

import pandas as pd
from dotenv import load_dotenv

from config import Config
from data.binance import BinanceWebSocket
from data.polymarket import PolymarketCLOB
from signals.factors import FactorCalculator
from signals.regime import RegimeDetector
from signals.social import SocialSignals
from execution.paper import PaperTrader
from execution.live import LiveTrader
from risk.position_sizer import PositionSizer
from db.models import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('apex.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class APEXTradingSystem:
    """
    Main orchestrator for APEX trading system.
    
    Coordinates data ingestion, signal generation, regime detection,
    position sizing, and trade execution.
    """
    
    def __init__(self):
        """Initialize APEX system components."""
        logger.info("🚀 Initializing APEX Trading System...")
        
        # Load configuration
        load_dotenv()
        self.config = Config()
        
        # Initialize database
        self.db = Database(self.config.DATABASE_URL)
        
        # Data sources
        self.binance = BinanceWebSocket()
        self.polymarket = PolymarketCLOB(
            private_key=self.config.POLYMARKET_PK,
            proxy_address=self.config.POLYMARKET_PROXY_ADDRESS
        )
        
        # Signal generators
        self.factor_calc = FactorCalculator()
        self.regime_detector = RegimeDetector()
        self.social_signals = SocialSignals(
            neynar_api_key=self.config.NEYNAR_API_KEY
        )
        
        # Risk management
        self.position_sizer = PositionSizer(
            max_position_pct=self.config.MAX_POSITION_PCT,
            kelly_fraction=self.config.KELLY_FRACTION
        )
        
        # Execution engine (paper or live)
        if self.config.IS_PAPER:
            logger.info("📝 Running in PAPER TRADING mode")
            self.trader = PaperTrader(
                initial_balance=self.config.PAPER_BALANCE,
                db=self.db
            )
        else:
            logger.warning("🔴 Running in LIVE TRADING mode - REAL MONEY")
            self.trader = LiveTrader(
                polymarket=self.polymarket,
                db=self.db
            )
        
        # State tracking
        self.price_data: Dict[str, pd.DataFrame] = {}
        self.current_regime = 1  # Start in medium volatility regime
        self.drawdown = 0.0
        self.peak_balance = self.config.PAPER_BALANCE
        
        logger.info("✅ APEX initialized successfully")
    
    async def run(self):
        """
        Main event loop.
        
        Continuously:
        1. Ingests real-time data
        2. Calculates factor signals
        3. Detects market regime
        4. Computes edge for available markets
        5. Sizes positions optimally
        6. Executes trades when edge exceeds threshold
        """
        logger.info("▶️  Starting main event loop...")
        
        # Start data streams
        await self.binance.connect(['BTCUSDT', 'ETHUSDT', 'SOLUSDT'])
        
        try:
            while True:
                # Update price data
                await self._update_price_data()
                
                # Detect market regime
                await self._update_regime()
                
                # Scan for trading opportunities
                opportunities = await self._scan_markets()
                
                # Execute trades for high-edge opportunities
                for opp in opportunities:
                    if opp['edge'] >= self.config.MIN_EDGE_THRESHOLD:
                        await self._execute_trade(opp)
                
                # Check risk controls
                await self._check_risk_controls()
                
                # Sleep before next iteration
                await asyncio.sleep(10)  # 10 second cycle
                
        except KeyboardInterrupt:
            logger.info("⏹️  Shutdown signal received")
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}", exc_info=True)
        finally:
            await self._shutdown()
    
    async def _update_price_data(self):
        """Fetch latest price data from WebSocket feeds."""
        try:
            for asset in ['BTC', 'ETH', 'SOL']:
                latest = await self.binance.get_latest_price(f"{asset}USDT")
                
                if asset not in self.price_data:
                    self.price_data[asset] = pd.DataFrame()
                
                # Append to historical data
                new_row = pd.DataFrame([{
                    'timestamp': datetime.utcnow(),
                    'price': latest['price'],
                    'volume': latest['volume']
                }])
                
                self.price_data[asset] = pd.concat(
                    [self.price_data[asset], new_row],
                    ignore_index=True
                )
                
                # Keep only last 1000 rows
                if len(self.price_data[asset]) > 1000:
                    self.price_data[asset] = self.price_data[asset].tail(1000)
                
        except Exception as e:
            logger.error(f"Error updating price data: {e}")
    
    async def _update_regime(self):
        """Update market regime using HMM."""
        try:
            # Combine all asset data for regime detection
            all_returns = []
            for asset, df in self.price_data.items():
                if len(df) > 1:
                    returns = df['price'].pct_change().dropna()
                    all_returns.extend(returns.tolist())
            
            if len(all_returns) > 50:  # Minimum data requirement
                self.current_regime = await self.regime_detector.detect(
                    all_returns
                )
                logger.debug(f"Current regime: {self.current_regime}")
                
        except Exception as e:
            logger.error(f"Error updating regime: {e}")
    
    async def _scan_markets(self) -> List[Dict]:
        """
        Scan Polymarket for trading opportunities.
        
        Returns:
            List of opportunity dicts with edge calculations
        """
        opportunities = []
        
        try:
            # Get active crypto markets from Polymarket
            markets = await self.polymarket.get_markets(['BTC', 'ETH', 'SOL'])
            
            for market in markets:
                asset = market['asset']
                
                if asset not in self.price_data:
                    continue
                
                # Calculate factor signals
                factors = await self.factor_calc.compute(
                    self.price_data[asset]
                )
                
                # Get social sentiment
                social_score = await self.social_signals.get_sentiment(asset)
                
                # Combine into model probability
                model_prob = self._compute_model_probability(
                    factors, social_score
                )
                
                # Calculate edge
                polymarket_mid = (market['bid'] + market['ask']) / 2
                edge = abs(polymarket_mid - model_prob)
                
                opportunities.append({
                    'market_id': market['id'],
                    'asset': asset,
                    'polymarket_mid': polymarket_mid,
                    'model_prob': model_prob,
                    'edge': edge,
                    'factors': factors,
                    'social_score': social_score,
                    'regime': self.current_regime
                })
                
            # Sort by edge (highest first)
            opportunities.sort(key=lambda x: x['edge'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error scanning markets: {e}")
        
        return opportunities
    
    def _compute_model_probability(self, factors: Dict, social_score: float) -> float:
        """
        Combine factor signals into model probability.
        
        Uses weighted sum passed through sigmoid:
        P_model = sigmoid(w1*z1 + w2*z2 + ... + wn*zn)
        
        Args:
            factors: Dict of factor z-scores
            social_score: Social sentiment score [-1, 1]
        
        Returns:
            Probability in [0, 1]
        """
        # Weights (sum to 1.0)
        weights = {
            'momentum': 0.30,
            'volatility': 0.15,
            'volume_divergence': 0.15,
            'onchain_flow': 0.15,
            'funding_rate': 0.10,
            'social': 0.15
        }
        
        # Weighted sum
        score = (
            weights['momentum'] * factors.get('momentum_zscore', 0) +
            weights['volatility'] * factors.get('volatility_zscore', 0) +
            weights['volume_divergence'] * factors.get('volume_div_zscore', 0) +
            weights['onchain_flow'] * factors.get('onchain_zscore', 0) +
            weights['funding_rate'] * factors.get('funding_zscore', 0) +
            weights['social'] * social_score
        )
        
        # Sigmoid transformation to [0, 1]
        prob = 1 / (1 + pd.np.exp(-score))
        
        return prob
    
    async def _execute_trade(self, opportunity: Dict):
        """
        Execute a trade for the given opportunity.
        
        Args:
            opportunity: Dict with edge, market info, signals
        """
        try:
            # Get current balance
            balance = await self.trader.get_balance()
            
            # Calculate position size using Kelly
            position_size = self.position_sizer.calculate(
                edge=opportunity['edge'],
                balance=balance,
                regime=opportunity['regime']
            )
            
            # Determine direction (YES if model_prob > polymarket_mid)
            direction = 'YES' if opportunity['model_prob'] > opportunity['polymarket_mid'] else 'NO'
            
            # Execute trade
            result = await self.trader.place_order(
                market_id=opportunity['market_id'],
                direction=direction,
                size_usdc=position_size,
                explanation={
                    'edge': opportunity['edge'],
                    'model_prob': opportunity['model_prob'],
                    'polymarket_mid': opportunity['polymarket_mid'],
                    'regime': opportunity['regime'],
                    'factors': opportunity['factors']
                }
            )
            
            if result['success']:
                logger.info(
                    f"✅ Trade executed: {opportunity['asset']} {direction} "
                    f"${position_size:.2f} @ edge={opportunity['edge']:.1%}"
                )
            else:
                logger.warning(f"⚠️ Trade failed: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error executing trade: {e}", exc_info=True)
    
    async def _check_risk_controls(self):
        """
        Check risk controls and halt trading if thresholds breached.
        """
        try:
            balance = await self.trader.get_balance()
            
            # Update peak and drawdown
            if balance > self.peak_balance:
                self.peak_balance = balance
            
            self.drawdown = (self.peak_balance - balance) / self.peak_balance
            
            # Circuit breaker: halt if drawdown exceeds threshold
            if self.drawdown >= self.config.DRAWDOWN_HALT_PCT:
                logger.critical(
                    f"🛑 DRAWDOWN CIRCUIT BREAKER TRIGGERED: {self.drawdown:.1%} "
                    f"(threshold: {self.config.DRAWDOWN_HALT_PCT:.1%})"
                )
                await self._shutdown()
                sys.exit(1)
                
        except Exception as e:
            logger.error(f"Error checking risk controls: {e}")
    
    async def _shutdown(self):
        """Clean shutdown of all components."""
        logger.info("🛑 Shutting down APEX system...")
        
        try:
            await self.binance.disconnect()
            await self.db.close()
            logger.info("✅ Shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


def main():
    """Entry point."""
    print("""
    ⚡ APEX TRADING SYSTEM ⚡
    Asymmetric Pattern EXploitation Engine
    """)
    
    # Create and run system
    system = APEXTradingSystem()
    
    try:
        asyncio.run(system.run())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
