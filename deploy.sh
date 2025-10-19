#!/bin/bash
set -e

# LogamMulia Monitor VPS Deployment Script
# This script automates the entire setup process

echo "🚀 Starting LogamMulia Monitor VPS Deployment..."
echo "================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should be run as a regular user with sudo privileges"
   exit 1
fi

# Configuration variables
INSTALL_DIR="/opt/logammulia-monitor"
SERVICE_USER="logammulia"
MONITORING_FREQUENCY="frequent"  # Options: aggressive, frequent, moderate

# Get user preferences
echo "📋 Configuration Options:"
echo "========================"

read -p "Enter monitoring frequency (aggressive/frequent/moderate) [frequent]: " freq_input
MONITORING_FREQUENCY=${freq_input:-frequent}

# Fixed command parameters
MONITOR_BRANCHES="ASB1 ASB2"
COMMAND_ARGS="--branches ASB1 ASB2"

echo ""
print_status "Configuration Summary:"
echo "  - Monitoring Frequency: $MONITORING_FREQUENCY"
echo "  - Branches: $MONITOR_BRANCHES"
echo "  - Command: python stock_analyzer.py $COMMAND_ARGS"
echo ""

read -p "Continue with deployment? (y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    print_status "Deployment cancelled."
    exit 0
fi

print_status "Starting deployment..."

# Update system packages
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
print_status "Installing required packages..."
sudo apt install -y python3 python3-pip git curl wget nano

# Create service user
print_status "Creating service user..."
if ! id "$SERVICE_USER" &>/dev/null; then
    sudo useradd -r -s /bin/false -m $SERVICE_USER
    print_status "Created user: $SERVICE_USER"
else
    print_warning "User $SERVICE_USER already exists"
fi

# Create installation directory
print_status "Creating installation directory..."
sudo mkdir -p $INSTALL_DIR

# Copy application files
# print_status "Installing application files..."
# sudo cp -r . $INSTALL_DIR/
# sudo chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR

# Install Python dependencies
print_status "Installing Python dependencies..."
sudo -u $SERVICE_USER pip3 install -r $INSTALL_DIR/requirements.txt

# Set up proper permissions
print_status "Setting up file permissions..."
sudo chmod +x $INSTALL_DIR/*.py
sudo chmod 600 $INSTALL_DIR/telegram_config.json
sudo chown $SERVICE_USER:$SERVICE_USER $INSTALL_DIR/telegram_config.json

# Create log directory
print_status "Setting up logging..."
sudo mkdir -p /var/log/logammulia-monitor
sudo chown $SERVICE_USER:$SERVICE_USER /var/log/logammulia-monitor

# Install systemd service
print_status "Installing systemd service..."

# Create service file with user configuration
cat > /tmp/logammulia-monitor.service << EOF
[Unit]
Description=LogamMulia Gold Stock Monitor
After=network.target

[Service]
Type=oneshot
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/stock_analyzer.py $COMMAND_ARGS
StandardOutput=journal
StandardError=journal
Restart=on-failure
RestartSec=30
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/logammulia-monitor.service /etc/systemd/system/

# Install timer based on frequency choice
print_status "Installing timer for $MONITORING_FREQUENCY monitoring..."

case $MONITORING_FREQUENCY in
    "aggressive")
        TIMER_INTERVAL="*:0/5"
        DELAY="30"
        ;;
    "frequent")
        TIMER_INTERVAL="*:0/10"
        DELAY="45"
        ;;
    "moderate")
        TIMER_INTERVAL="*:0/15"
        DELAY="60"
        ;;
    *)
        TIMER_INTERVAL="*:0/10"
        DELAY="45"
        ;;
esac

cat > /tmp/logammulia-monitor.timer << EOF
[Unit]
Description=Run LogamMulia Gold Stock Monitor every ${TIMER_INTERVAL#*:} minutes
Requires=logammulia-monitor.service

[Timer]
OnCalendar=$TIMER_INTERVAL
Persistent=true
RandomizedDelaySec=$DELAY

[Install]
WantedBy=timers.target
EOF

sudo mv /tmp/logammulia-monitor.timer /etc/systemd/system/

# Setup log rotation
print_status "Setting up log rotation..."
cat > /tmp/logammulia-monitor << EOF
/var/log/logammulia-monitor/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $SERVICE_USER $SERVICE_USER
    postrotate
        systemctl reload logammulia-monitor > /dev/null 2>&1 || true
    endscript
}
EOF

sudo mv /tmp/logammulia-monitor /etc/logrotate.d/

# Test configuration
print_status "Testing Telegram configuration..."
if sudo -u $SERVICE_USER python3 $INSTALL_DIR/stock_analyzer.py --test-telegram; then
    print_status "✅ Telegram configuration test passed!"
else
    print_error "❌ Telegram configuration test failed!"
    print_warning "Please check your telegram_config.json before continuing"
    read -p "Continue anyway? (y/N): " continue_anyway
    if [[ ! $continue_anyway =~ ^[Yy]$ ]]; then
        print_status "Deployment cancelled due to Telegram configuration failure."
        exit 1
    fi
fi

# Enable and start services
print_status "Enabling and starting services..."
sudo systemctl daemon-reload
sudo systemctl enable logammulia-monitor.timer
sudo systemctl start logammulia-monitor.timer

# Setup basic firewall
print_status "Configuring basic firewall..."
if ! command -v ufw &> /dev/null; then
    sudo apt install -y ufw
fi

sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow out 53,80,443

# Create management script
print_status "Creating management script..."
cat > /tmp/logammulia-manager << 'EOF'
#!/bin/bash
# LogamMulia Monitor Management Script

case "$1" in
    status)
        echo "=== Service Status ==="
        sudo systemctl status logammulia-monitor.timer
        echo ""
        echo "=== Timer Schedule ==="
        sudo systemctl list-timers logammulia-monitor
        ;;
    logs)
        echo "=== Recent Logs ==="
        sudo journalctl -u logammulia-monitor --since "1 hour ago" -f
        ;;
    stop)
        echo "Stopping LogamMulia Monitor..."
        sudo systemctl stop logammulia-monitor.timer
        ;;
    start)
        echo "Starting LogamMulia Monitor..."
        sudo systemctl start logammulia-monitor.timer
        ;;
    restart)
        echo "Restarting LogamMulia Monitor..."
        sudo systemctl restart logammulia-monitor.timer
        ;;
    test)
        echo "Testing Telegram configuration..."
        sudo -u logammulia python3 /opt/logammulia-monitor/stock_analyzer.py --test-telegram
        ;;
    manual)
        shift
        echo "Running manual check..."
        sudo -u logammulia python3 /opt/logammulia-monitor/stock_analyzer.py "$@"
        ;;
    *)
        echo "Usage: $0 {status|logs|stop|start|restart|test|manual [args]}"
        echo ""
        echo "Commands:"
        echo "  status   - Show service status and next run time"
        echo "  logs     - Show recent logs"
        echo "  stop     - Stop monitoring"
        echo "  start    - Start monitoring"
        echo "  restart  - Restart monitoring"
        echo "  test     - Test Telegram configuration"
        echo "  manual   - Run manual check with optional args"
        echo ""
        echo "Example: $0 manual --branches ASB1 ASB2"
        exit 1
        ;;
esac
EOF

sudo mv /tmp/logammulia-manager /usr/local/bin/
sudo chmod +x /usr/local/bin/logammulia-manager

# Final verification
print_status "Verifying installation..."
sleep 2

if sudo systemctl is-active --quiet logammulia-monitor.timer; then
    print_status "✅ Timer is active"
else
    print_error "❌ Timer failed to start"
fi

if sudo systemctl is-enabled --quiet logammulia-monitor.timer; then
    print_status "✅ Timer is enabled (will start on boot)"
else
    print_error "❌ Timer is not enabled"
fi

# Display final information
echo ""
echo "🎉 Deployment Complete!"
echo "======================="
echo ""
echo "Installation Directory: $INSTALL_DIR"
echo "Service User: $SERVICE_USER"
echo "Monitoring Frequency: $MONITORING_FREQUENCY"
echo "Branches Monitored: $MONITOR_BRANCHES"
echo "Command: python stock_analyzer.py $COMMAND_ARGS"
echo ""
echo "📋 Management Commands:"
echo "  logammulia-manager status    - Check service status"
echo "  logammulia-manager logs      - View logs"
echo "  logammulia-manager stop      - Stop monitoring"
echo "  logammulia-manager start     - Start monitoring"
echo "  logammulia-manager test      - Test Telegram"
echo "  logammulia-manager manual    - Run manual check"
echo ""
echo "📊 Check next run time:"
echo "  sudo systemctl list-timers logammulia-monitor"
echo ""
echo "📱 Your Telegram bot will receive alerts when gold is available at ASB1 and ASB2!"
echo ""
echo "🔧 Configuration file location:"
echo "  $INSTALL_DIR/telegram_config.json"
echo ""

# Show next scheduled run
echo "⏰ Next scheduled runs:"
sudo systemctl list-timers logammulia-monitor --no-pager

print_status "Deployment completed successfully! 🎉"