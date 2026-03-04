"""
Polymarket CLOB API Integration

Interacts with Polymarket's Central Limit Order Book for:
- Market discovery
- Order book data
- Trade execution (when live)
"""

import logging
from typing import Dict, List, Optional
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, OrderType

logger = logging.getLogger(__name__)


class PolymarketCLOB:
    """
    Wrapper for Polymarket CLOB API.
    
    Handles market queries and order execution.
    """
    
    def __init__(self, private_key: Optional[str] = None, 
                 proxy_address: Optional[str] = None):
        """
        Initialize Polymarket client.
        
        Args:
            private_key: Ethereum private key (required for live trading)
            proxy_address: Proxy wallet address (required for live trading)
        """
        self.private_key = private_key
        self.proxy_address = proxy_address
        
        # Initialize client (read-only if no credentials)
        if private_key and proxy_address:
            self.client = ClobClient(
                key=private_key,
                chain_id=137,  # Polygon mainnet
                signature_type=2
            )
            logger.info("✅ Polymarket client initialized (authenticated)")
        else:
            # Read-only mode
            self.client = ClobClient(
                host="https://clob.polymarket.com",
                chain_id=137
            )
            logger.info("📝 Polymarket client initialized (read-only)")
    
    async def get_markets(self, keywords: List[str]) -> List[Dict]:
        """
        Search for active markets matching keywords.
        
        Args:
            keywords: List of search terms (e.g., ['BTC', 'bitcoin'])
        
        Returns:
            List of market dicts with id, question, outcomes, prices
        """
        try:
            markets = []
            
            for keyword in keywords:
                response = self.client.get_markets(
                    next_cursor="",
                    limit=20
                )
                
                for market in response.get('data', []):
                    # Filter for keyword match
                    question = market.get('question', '').lower()
                    if keyword.lower() in question:
                        # Get order book for pricing
                        token_id = market['tokens'][0]['token_id']
                        book = self.client.get_order_book(token_id)
                        
                        markets.append({
                            'id': market['condition_id'],
                            'asset': keyword.upper(),
                            'question': market['question'],
                            'token_id': token_id,
                            'bid': float(book['bids'][0]['price']) if book.get('bids') else 0.5,
                            'ask': float(book['asks'][0]['price']) if book.get('asks') else 0.5,
                            'volume': float(market.get('volume', 0))
                        })
            
            logger.info(f"Found {len(markets)} markets for {keywords}")
            return markets
            
        except Exception as e:
            logger.error(f"Error fetching markets: {e}")
            return []
    
    async def place_order(self, market_id: str, side: str, 
                         size: float, price: float) -> Dict:
        """
        Place a limit order on Polymarket.
        
        Args:
            market_id: Market condition ID
            side: 'BUY' or 'SELL'
            size: Order size in USDC
            price: Limit price [0, 1]
        
        Returns:
            Dict with order_id and status
        """
        if not self.private_key:
            raise ValueError("Cannot place order: no credentials provided")
        
        try:
            order = OrderArgs(
                token_id=market_id,
                price=price,
                size=size,
                side=side,
                order_type=OrderType.GTC  # Good-til-cancelled
            )
            
            result = self.client.create_order(order)
            
            logger.info(
                f"✅ Order placed: {side} {size} @ {price:.3f} "
                f"(order_id: {result.get('order_id')})"
            )
            
            return {
                'success': True,
                'order_id': result.get('order_id'),
                'status': result.get('status')
            }
            
        except Exception as e:
            logger.error(f"Order placement failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_order_status(self, order_id: str) -> Dict:
        """
        Check status of an existing order.
        
        Args:
            order_id: Order ID from place_order
        
        Returns:
            Dict with order details
        """
        try:
            order = self.client.get_order(order_id)
            return order
        except Exception as e:
            logger.error(f"Error fetching order: {e}")
            return {}
