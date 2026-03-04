"""
Binance WebSocket Integration

Real-time price data via WebSocket streams.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional
import websockets
from datetime import datetime

logger = logging.getLogger(__name__)


class BinanceWebSocket:
    """
    WebSocket client for Binance price streams.
    
    Subscribes to ticker streams for real-time OHLCV data.
    """
    
    BASE_URL = "wss://stream.binance.com:9443/ws"
    
    def __init__(self):
        self.ws = None
        self.symbols: List[str] = []
        self.latest_prices: Dict[str, Dict] = {}
        self._running = False
    
    async def connect(self, symbols: List[str]):
        """
        Connect to Binance WebSocket and subscribe to symbols.
        
        Args:
            symbols: List of trading pairs (e.g., ['BTCUSDT', 'ETHUSDT'])
        """
        self.symbols = [s.lower() for s in symbols]
        
        # Build stream URL
        streams = "/".join([f"{symbol}@ticker" for symbol in self.symbols])
        url = f"{self.BASE_URL}/{streams}"
        
        logger.info(f"Connecting to Binance WebSocket: {symbols}")
        
        try:
            self.ws = await websockets.connect(url)
            self._running = True
            
            # Start listening task
            asyncio.create_task(self._listen())
            
            logger.info("✅ Binance WebSocket connected")
        except Exception as e:
            logger.error(f"Failed to connect to Binance: {e}")
            raise
    
    async def _listen(self):
        """
        Listen for incoming messages and update latest prices.
        """
        try:
            async for message in self.ws:
                data = json.loads(message)
                
                # Handle multi-stream format
                if 'stream' in data:
                    stream = data['stream']
                    ticker = data['data']
                    symbol = stream.split('@')[0].upper()
                else:
                    ticker = data
                    symbol = ticker['s']
                
                # Update latest price cache
                self.latest_prices[symbol] = {
                    'price': float(ticker['c']),  # Close price
                    'bid': float(ticker['b']),
                    'ask': float(ticker['a']),
                    'volume': float(ticker['v']),
                    'timestamp': datetime.utcnow()
                }
                
                logger.debug(f"{symbol}: ${ticker['c']}")
                
        except websockets.exceptions.ConnectionClosed:
            logger.warning("⚠️ Binance WebSocket connection closed")
            self._running = False
        except Exception as e:
            logger.error(f"Error in WebSocket listener: {e}")
            self._running = False
    
    async def get_latest_price(self, symbol: str) -> Optional[Dict]:
        """
        Get most recent price data for symbol.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
        
        Returns:
            Dict with price, bid, ask, volume, timestamp
        """
        return self.latest_prices.get(symbol.upper())
    
    async def disconnect(self):
        """Close WebSocket connection."""
        if self.ws:
            await self.ws.close()
            logger.info("🔌 Binance WebSocket disconnected")
    
    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is currently connected."""
        return self._running
