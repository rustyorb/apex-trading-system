#!/bin/bash
set -e

echo "================================================"
echo "APEX Trading System - Automated Installation"
echo "================================================"
echo ""

# Check if running on Ubuntu
if [[ ! -f /etc/lsb-release ]] || ! grep -q "Ubuntu" /etc/lsb-release; then
    echo "⚠️  Warning: This script is designed for Ubuntu 22.04+"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for sudo access
if ! sudo -v; then
    echo "❌ Error: This script requires sudo privileges"
    exit 1
fi

echo "📦 Step 1/8: Updating system packages..."
sudo apt update && sudo apt upgrade -y

echo ""
echo "📦 Step 2/8: Installing Redis..."
sudo apt install redis-server -y
sudo systemctl start redis-server
sudo systemctl enable redis-server
echo "✅ Redis installed and running"

echo ""
echo "📦 Step 3/8: Installing PostgreSQL 15..."
sudo apt install postgresql postgresql-contrib -y
echo "✅ PostgreSQL installed"

echo ""
echo "📦 Step 4/8: Installing TimescaleDB..."
sudo sh -c "echo 'deb [signed-by=/usr/share/keyrings/timescale.keyring] \
https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main' \
> /etc/apt/sources.list.d/timescaledb.list"

wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | \
sudo gpg --dearmor -o /usr/share/keyrings/timescale.keyring

sudo apt update
sudo apt install timescaledb-2-postgresql-15 -y

echo "🔧 Tuning TimescaleDB for your hardware..."
sudo timescaledb-tune --quiet --yes
sudo systemctl restart postgresql
echo "✅ TimescaleDB installed and configured"

echo ""
echo "📦 Step 5/8: Installing Python 3.11 and dependencies..."
sudo apt install python3.11 python3.11-venv python3.11-dev \
                 build-essential libpq-dev -y
echo "✅ Python environment ready"

echo ""
echo "🗄️  Step 6/8: Setting up database..."
read -p "Enter database password for apex_user: " -s DB_PASSWORD
echo

sudo -u postgres psql <<EOF
CREATE DATABASE apex;
CREATE USER apex_user WITH PASSWORD '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE apex TO apex_user;
\c apex
CREATE EXTENSION IF NOT EXISTS timescaledb;
EOF

echo "✅ Database created"

echo ""
echo "📂 Step 7/8: Setting up project structure..."
mkdir -p ~/apex/{core,data,external,interface,utils,db}

# Create virtual environment
cd ~/apex
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

echo "✅ Project structure created"

echo ""
echo "📦 Step 8/8: Installing Python dependencies..."

# Create requirements.txt if it doesn't exist
cat > requirements.txt <<EOF
pandas==2.2.0
numpy==1.26.3
asyncio==3.4.3
websockets==12.0
python-dotenv==1.0.0
redis==5.0.1
psycopg2-binary==2.9.9
sqlalchemy==2.0.25
asyncpg==0.29.0
py-clob-client==0.25.0
python-binance==1.0.19
requests==2.31.0
scikit-learn==1.4.0
scipy==1.12.0
sentence-transformers==2.3.1
streamlit==1.30.0
plotly==5.18.0
EOF

pip install -r requirements.txt
echo "✅ Python dependencies installed"

echo ""
echo "⚙️  Creating configuration template..."

cat > .env.template <<EOF
# ═══════════════════════════════════════════════════
# PAPER/LIVE MODE TOGGLE
# ═══════════════════════════════════════════════════
IS_PAPER=true
PAPER_BALANCE=10000.0

# ═══════════════════════════════════════════════════
# API CREDENTIALS
# ═══════════════════════════════════════════════════
POLYMARKET_PK=your_private_key_here
POLYMARKET_PROXY_ADDRESS=your_proxy_address_here
BINANCE_API_KEY=
BINANCE_API_SECRET=
BENZINGA_API_KEY=
CRYPTOQUANT_API_KEY=
NEYNAR_API_KEY=

# ═══════════════════════════════════════════════════
# INFRASTRUCTURE
# ═══════════════════════════════════════════════════
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://apex_user:$DB_PASSWORD@localhost:5432/apex

# ═══════════════════════════════════════════════════
# RISK PARAMETERS
# ═══════════════════════════════════════════════════
MAX_POSITION_PCT=0.03
MIN_EDGE_THRESHOLD=0.12
KELLY_FRACTION=0.25
DRAWDOWN_HALT_PCT=0.18
EOF

cp .env.template .env
echo "✅ Configuration template created (.env file)"

echo ""
echo "🗄️  Initializing database schema..."
if [ -f db/init_schema.sql ]; then
    PGPASSWORD=$DB_PASSWORD psql -U apex_user -d apex -h localhost -f db/init_schema.sql
    echo "✅ Database schema initialized"
else
    echo "⚠️  db/init_schema.sql not found. You'll need to initialize the schema manually."
fi

echo ""
echo "================================================"
echo "✅ APEX Trading System Installation Complete!"
echo "================================================"
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Edit configuration:"
echo "   nano ~/apex/.env"
echo ""
echo "2. Add your API credentials to .env file"
echo ""
echo "3. Activate virtual environment:"
echo "   cd ~/apex && source venv/bin/activate"
echo ""
echo "4. Run the bot:"
echo "   python main.py"
echo ""
echo "5. Launch dashboard (optional):"
echo "   streamlit run interface/app.py --server.port 8501"
echo ""
echo "⚠️  Important: System starts in PAPER mode (IS_PAPER=true)"
echo "   Test thoroughly before switching to live trading."
echo ""
echo "📊 Database credentials:"
echo "   Database: apex"
echo "   User: apex_user"
echo "   Host: localhost"
echo "   Port: 5432"
echo ""
echo "🔧 SystemD service installation (optional):"
echo "   sudo cp systemd/apex-bot.service /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable apex-bot"
echo "   sudo systemctl start apex-bot"
echo ""
