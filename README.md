# ⚡ APEX Trading System

<div align="center">

![APEX Banner](https://img.shields.io/badge/APEX-Trading_System-00ff88?style=for-the-badge&logo=bitcoin&logoColor=white)

**Asymmetric Pattern EXploitation Engine**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg?style=flat&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat)](LICENSE)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791.svg?style=flat&logo=postgresql)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7.x-DC382D.svg?style=flat&logo=redis)](https://redis.io)
[![TimescaleDB](https://img.shields.io/badge/TimescaleDB-Enabled-FFD700.svg?style=flat)](https://timescale.com)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg?style=flat)](https://github.com/psf/black)

Systematic trading bot exploiting mispricings between Polymarket prediction markets and actual crypto price dynamics.

[Features](#-features) • [Installation](#-installation) • [Strategy](#-strategy-overview) • [Documentation](#-documentation) • [Performance](#-performance-targets)

</div>

---

## 🎯 What is APEX?

APEX combines **quantitative signals**, **on-chain analytics**, **social sentiment**, and **regime detection** to identify high-probability trades on Polymarket with measurable edge.

```mermaid
graph TB
    A[Data Sources] --> B[Signal Generation]
    A --> C[Regime Detection]
    B --> D[Edge Calculation]
    C --> D
    D --> E{Edge > Threshold?}
    E -->|Yes| F[Position Sizing<br/>Kelly Criterion]
    E -->|No| G[Skip Trade]
    F --> H[Execution Engine]
    H --> I{Paper Mode?}
    I -->|Yes| J[Simulated Fills]
    I -->|No| K[Polymarket CLOB]
    J --> L[PostgreSQL Log]
    K --> L
    
    style A fill:#1a2142,stroke:#00ff88,color:#fff
    style B fill:#1a2142,stroke:#00d4ff,color:#fff
    style D fill:#1a2142,stroke:#ffd700,color:#fff
    style F fill:#1a2142,stroke:#00ff88,color:#fff
    style K fill:#1a2142,stroke:#ff3366,color:#fff
```

## ✨ Features

- 🎲 **Prediction Market Focus** - Trades Polymarket binary options on crypto price movements
- 📊 **Multi-Factor Signals** - Price momentum, volatility, on-chain flows, funding rates, social sentiment
- 🧠 **Regime Detection** - Hidden Markov Model adapts to market volatility states
- 💰 **Kelly Position Sizing** - Optimal capital allocation with safety constraints
- 🔒 **Risk Management** - Edge floors, position caps, drawdown circuit breakers
- 📝 **Paper Trading** - Realistic simulation mode for strategy validation
- 🚀 **Production Ready** - SystemD service, monitoring dashboard, comprehensive logging
- 💾 **Time-Series Optimized** - TimescaleDB for efficient historical data storage

## 🏆 Performance Targets

| Metric | Target |
|--------|--------|
| **Sharpe Ratio** | 2.5+ |
| **Win Rate** | 65%+ |
| **Monthly Return** | 8-15% |
| **Max Drawdown** | <18% |
| **Avg Holding Time** | 6-18 hours |
| **Min Trades/Month** | 40+ |

> [!NOTE]
> These are **target metrics** based on backtesting. Past performance ≠ future results.

## 🚀 Quick Start

### Prerequisites

```bash
# Hardware Requirements
- 8GB+ RAM (64GB recommended)
- 4+ CPU cores
- Ubuntu 22.04 or later
- Stable internet connection
```

### One-Command Install

```bash
curl -sSL https://raw.githubusercontent.com/rustyorb/apex-trading-system/main/install.sh | bash
```

<details>
<summary><b>🔧 Manual Installation (click to expand)</b></summary>

### Step 1: System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Redis
sudo apt install redis-server -y
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Install PostgreSQL + TimescaleDB
sudo apt install postgresql postgresql-contrib -y
sudo sh -c "echo 'deb [signed-by=/usr/share/keyrings/timescale.keyring] https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main' > /etc/apt/sources.list.d/timescaledb.list"
wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/timescale.keyring
sudo apt update
sudo apt install timescaledb-2-postgresql-15 -y
sudo timescaledb-tune --quiet --yes
sudo systemctl restart postgresql
```

### Step 2: Database Setup

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE apex;
CREATE USER apex_user WITH PASSWORD 'your_strong_password';
GRANT ALL PRIVILEGES ON DATABASE apex TO apex_user;
\c apex
CREATE EXTENSION IF NOT EXISTS timescaledb;
\q
```

### Step 3: Python Environment

```bash
# Clone repository
git clone https://github.com/rustyorb/apex-trading-system.git
cd apex-trading-system

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Configuration

```bash
# Copy example env file
cp .env.example .env

# Edit with your credentials
nano .env
```

### Step 5: Initialize Database

```bash
psql -U apex_user -d apex -f db/init_schema.sql
```

### Step 6: Run

```bash
# Start in paper trading mode
python main.py
```

</details>

## 📋 Configuration

### Environment Variables

Create `.env` file from template:

```bash
# ═══════════════════════════════════════════════════
# THE SWITCH (Paper vs Live)
# ═══════════════════════════════════════════════════
IS_PAPER=true                    # Set to false for live trading
PAPER_BALANCE=10000.0

# ═══════════════════════════════════════════════════
# API KEYS
# ═══════════════════════════════════════════════════
POLYMARKET_PK=your_private_key
POLYMARKET_PROXY_ADDRESS=your_proxy_address
BINANCE_API_KEY=
BINANCE_API_SECRET=
BENZINGA_API_KEY=
CRYPTOQUANT_API_KEY=
NEYNAR_API_KEY=

# ═══════════════════════════════════════════════════
# INFRASTRUCTURE
# ═══════════════════════════════════════════════════
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://apex_user:password@localhost:5432/apex

# ═══════════════════════════════════════════════════
# RISK PARAMETERS
# ═══════════════════════════════════════════════════
MAX_POSITION_PCT=0.03            # 3% max per trade
MIN_EDGE_THRESHOLD=0.12          # 12% minimum edge
KELLY_FRACTION=0.25              # Quarter-Kelly for safety
DRAWDOWN_HALT_PCT=0.18           # Stop at 18% drawdown
```

> [!WARNING]
> **NEVER commit `.env` file to version control**. It contains sensitive API keys.

> [!IMPORTANT]
> Start with `IS_PAPER=true` and test thoroughly before going live.

## 🧠 Strategy Overview

### Signal Stack

APEX combines multiple signal sources with weighted contributions:

```mermaid
pie title Signal Weight Distribution
    "Price Factors" : 60
    "On-Chain Data" : 25
    "Social Sentiment" : 15
```

#### 1. Price Factors (60% weight)

- **Momentum**: 20-period z-score of returns
- **Volatility**: 48-hour rolling standard deviation  
- **Volume Divergence**: Price vs. volume correlation

#### 2. On-Chain Signals (25% weight)

- **Exchange Flows**: Net inflow/outflow from CryptoQuant
- **Funding Rates**: Perpetual futures funding regime shifts
- **Whale Activity**: Large wallet accumulation patterns

#### 3. Social Sentiment (15% weight)

- **Cast Velocity**: Farcaster post frequency via Neynar
- **Sentiment Polarity**: FinBERT embeddings
- **Narrative Clustering**: Meme propagation detection

### Edge Calculation

The core trading decision:

$$\text{edge} = |\text{polymarket\_mid} - P_{\text{model}}|$$

Where $P_{\text{model}}$ is computed from weighted factor composite:

$$P_{\text{model}} = \sigma\left(\sum_{i=1}^{n} w_i \cdot z_i\right)$$

- $\sigma$ = sigmoid function
- $w_i$ = factor weights
- $z_i$ = standardized factor values

### Position Sizing (Kelly Criterion)

$$f^* = \frac{p \cdot b - q}{b}$$

$$\text{position\_size} = \min\left(\text{balance} \times f^* \times \text{KELLY\_FRACTION}, \text{balance} \times \text{MAX\_POSITION\_PCT}\right)$$

## 🗂️ Project Structure

```
apex-trading-system/
├── main.py                 # Main entry point
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── README.md             # This file
│
├── data/                 # Data ingestion modules
│   ├── __init__.py
│   ├── binance.py       # WebSocket price feeds
│   ├── polymarket.py    # CLOB API integration
│   ├── news.py          # Benzinga news sentiment
│   ├── onchain.py       # CryptoQuant flows
│   └── farcaster.py     # Neynar social data
│
├── signals/             # Signal generation
│   ├── __init__.py
│   ├── factors.py       # Price/volume factors
│   ├── social.py        # Sentiment analysis
│   └── regime.py        # HMM regime detection
│
├── execution/           # Trade execution
│   ├── __init__.py
│   ├── paper.py         # Simulated trading
│   └── live.py          # Polymarket live execution
│
├── risk/                # Risk management
│   ├── __init__.py
│   └── position_sizer.py  # Kelly sizing + caps
│
├── db/                  # Database
│   ├── __init__.py
│   ├── init_schema.sql  # TimescaleDB schema
│   └── models.py        # SQLAlchemy models
│
├── interface/           # Monitoring dashboard
│   ├── __init__.py
│   └── app.py           # Streamlit dashboard
│
└── tests/               # Unit tests
    ├── __init__.py
    └── test_signals.py
```

## 📊 Monitoring Dashboard

### Launch Streamlit UI

```bash
streamlit run interface/app.py --server.port 8501 --server.address 0.0.0.0
```

Access from any device: `http://<server-ip>:8501`

### Dashboard Features

- [x] Real-time P&L tracking
- [x] Win rate and Sharpe ratio
- [x] Open positions monitor
- [x] Trade history log
- [x] Factor signal visualization
- [x] System health indicators

## 🔒 Risk Management

### Multi-Layer Protection

| Layer | Threshold | Action |
|-------|-----------|--------|
| **Edge Floor** | 12% | Reject low-confidence trades |
| **Position Cap** | 3% per trade | Hard limit on exposure |
| **Total Exposure** | 15% aggregate | Max open positions |
| **Drawdown Halt** | 18% | Emergency stop all trading |
| **Liquidity Filter** | $50K daily volume | Only trade liquid markets |

> [!CAUTION]
> Even with robust risk controls, **trading involves real financial risk**. Only trade capital you can afford to lose.

## 📖 Documentation

- [📘 Full Strategy Documentation](docs/STRATEGY.md)
- [🔧 Installation Guide](docs/INSTALLATION.md)
- [⚙️ Configuration Reference](docs/CONFIGURATION.md)
- [🚀 Deployment Guide](docs/DEPLOYMENT.md)
- [🐛 Troubleshooting](docs/TROUBLESHOOTING.md)
- [📊 Performance Analysis](docs/PERFORMANCE.md)

## 🤝 Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# Format code
black .
flake8 .

# Type checking
mypy .
```

## 🐛 Known Issues & Roadmap

- [ ] **v1.1**: DEJD jump-diffusion modeling for tail risk
- [ ] **v1.2**: Multi-agent portfolio optimization
- [ ] **v1.3**: Automated parameter tuning (Bayesian optimization)
- [ ] **v1.4**: Cross-market arbitrage (Polymarket ↔ Kalshi)
- [ ] **v1.5**: Advanced social signals (Twitter/X, Reddit)

See [CHANGELOG.md](CHANGELOG.md) for version history.

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

> [!WARNING]
> **HIGH RISK ACTIVITY**
> 
> This software is provided for educational and research purposes. Cryptocurrency and prediction market trading involves substantial risk of loss. The authors assume **no liability** for financial losses incurred through use of this system.
> 
> - Past performance does not guarantee future results
> - Markets are volatile and unpredictable  
> - System bugs or API failures can cause losses
> - Start with capital you can afford to lose completely
> - Ensure compliance with local regulations

## 🙏 Acknowledgments

- **Polymarket** - Prediction market platform & CLOB API
- **py-clob-client** - Python SDK for Polymarket
- **TimescaleDB** - Time-series database optimization
- **Neynar** - Farcaster social data API
- **CryptoQuant** - On-chain analytics

## 📬 Contact

- **GitHub Issues**: [Report bugs or request features](https://github.com/rustyorb/apex-trading-system/issues)
- **Discussions**: [Ask questions or share strategies](https://github.com/rustyorb/apex-trading-system/discussions)

---

<div align="center">

**Built with ⚡ by systematic traders, for systematic traders**

[![Star this repo](https://img.shields.io/github/stars/rustyorb/apex-trading-system?style=social)](https://github.com/rustyorb/apex-trading-system)
[![Follow @rustyorb](https://img.shields.io/github/followers/rustyorb?label=Follow&style=social)](https://github.com/rustyorb)

</div>
