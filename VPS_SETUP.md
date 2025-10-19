# VPS Setup Guide for LogamMulia Stock Monitor

## 🚀 VPS Requirements

### **Minimum Specifications:**
- **CPU:** 1 vCPU
- **RAM:** 512MB - 1GB
- **Storage:** 10GB
- **OS:** Ubuntu 20.04/22.04 or Debian 10/11
- **Network:** Stable internet connection

### **Recommended VPS Providers:**
- **DigitalOcean** ($5/month) - Reliable and easy to use
- **Vultr** ($5/month) - Good performance and locations
- **Linode** ($5/month) - Excellent support
- **AWS EC2** (t2.micro - Free tier) - Free for 12 months

## 📋 Setup Instructions

### **1. VPS Initial Setup**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip git wget curl nano

# Install Python dependencies
pip3 install requests beautifulsoup4 lxml pandas

# Create user for the monitor (optional but recommended)
sudo useradd -m -s /bin/bash goldmonitor
sudo usermod -aG sudo goldmonitor
```

### **2. Deploy the Application**

```bash
# Clone or upload your project
cd /home/goldmonitor
git clone <your-repo-url> logammulia-monitor
# OR upload files manually using scp

cd logammulia-monitor

# Install Python dependencies
pip3 install -r requirements.txt

# Make scripts executable
chmod +x *.py
```

### **3. Configuration**

```bash
# Edit Telegram configuration
nano telegram_config.json

# Test the configuration
python3 stock_analyzer.py --test-telegram
```

## 🔧 Continuous Monitoring Setup

### **Option 1: Systemd Service (Recommended)**

Create a systemd service for automatic monitoring:

```bash
# Create service file
sudo nano /etc/systemd/system/logammulia-monitor.service
```

Add the following content:

```ini
[Unit]
Description=LogamMulia Gold Stock Monitor
After=network.target

[Service]
Type=oneshot
User=goldmonitor
Group=goldmonitor
WorkingDirectory=/home/goldmonitor/logammulia-monitor
ExecStart=/usr/bin/python3 /home/goldmonitor/logammulia-monitor/stock_analyzer.py --weight 1.0 --max-branches 10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### **Option 2: Cron Job (Simple)**

```bash
# Edit crontab
crontab -e

# Add monitoring every 15 minutes
*/15 * * * * cd /home/goldmonitor/logammulia-monitor && python3 stock_analyzer.py --weight 1.0 --max-branches 10 >> /var/log/logammulia-monitor.log 2>&1
```

## ⏰ Monitoring Schedule Options

### **Frequent Monitoring (High Priority)**
```bash
# Every 5 minutes (aggressive)
*/5 * * * * python3 stock_analyzer.py --weight 1.0 --max-branches 5

# Every 10 minutes (recommended for popular weights)
*/10 * * * * python3 stock_analyzer.py --weight 1.0 --max-branches 8
```

### **Moderate Monitoring (Balanced)**
```bash
# Every 15 minutes (recommended)
*/15 * * * * python3 stock_analyzer.py --weight 1.0 --max-branches 10

# Every 30 minutes (less frequent)
*/30 * * * * python3 stock_analyzer.py --weight 1.0 --max-branches 15
```

### **Comprehensive Monitoring (All Weights)**
```bash
# Every hour - check different weights
0 * * * * python3 stock_analyzer.py --weight 0.5 --max-branches 10
10 * * * * python3 stock_analyzer.py --weight 1.0 --max-branches 10
20 * * * * python3 stock_analyzer.py --weight 2.0 --max-branches 10
30 * * * * python3 stock_analyzer.py --weight 5.0 --max-branches 10
40 * * * * python3 stock_analyzer.py --weight 10.0 --max-branches 10
50 * * * * python3 stock_analyzer.py --branches ASB1 ABDG AJK2
```

## 📊 Monitoring and Logging

### **Setup Logging**

```bash
# Create log directory
sudo mkdir -p /var/log/logammulia-monitor
sudo chown goldmonitor:goldmonitor /var/log/logammulia-monitor

# Create log rotation
sudo nano /etc/logrotate.d/logammulia-monitor
```

Add to logrotate config:
```
/var/log/logammulia-monitor/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 goldmonitor goldmonitor
}
```

### **Monitor Service Status**

```bash
# Check service status
sudo systemctl status logammulia-monitor.timer

# View logs
sudo journalctl -u logammulia-monitor -f

# Check recent logs
tail -f /var/log/logammulia-monitor.log
```

## 🛡️ Security Considerations

### **Basic Security Setup**

```bash
# Configure firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow out 53,80,443

# Disable root login
sudo nano /etc/ssh/sshd_config
# Add: PermitRootLogin no
sudo systemctl restart ssh

# Set up fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

### **Application Security**

```bash
# Set proper file permissions
chmod 600 telegram_config.json
chmod 755 *.py

# Create dedicated user with limited privileges
sudo useradd -r -s /bin/false logammulia-user
sudo chown -R logammulia-user:logammulia-user /opt/logammulia-monitor
```

## 🚀 Deployment Script

Save this as `deploy.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Deploying LogamMulia Monitor to VPS..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip git

# Create user
sudo useradd -m -s /bin/bash goldmonitor || true

# Create application directory
sudo mkdir -p /opt/logammulia-monitor
sudo chown goldmonitor:goldmonitor /opt/logammulia-monitor

# Copy files (assumes current directory contains the files)
sudo cp -r . /opt/logammulia-monitor/
sudo chown -R goldmonitor:goldmonitor /opt/logammulia-monitor

# Install Python dependencies
sudo -u goldmonitor pip3 install -r /opt/logammulia-monitor/requirements.txt

# Set up systemd service
sudo cp /opt/logammulia-monitor/logammulia-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable logammulia-monitor.timer
sudo systemctl start logammulia-monitor.timer

echo "✅ Deployment complete!"
echo "Check status with: sudo systemctl status logammulia-monitor.timer"
```

## 📱 Monitoring Commands

### **Useful Commands**

```bash
# Start monitoring
sudo systemctl start logammulia-monitor.timer

# Stop monitoring
sudo systemctl stop logammulia-monitor.timer

# Check schedule
sudo systemctl list-timers logammulia-monitor

# View logs
sudo journalctl -u logammulia-monitor -f

# Test manually
cd /opt/logammulia-monitor
python3 stock_analyzer.py --weight 1.0 --max-branches 3

# Check last run
sudo journalctl -u logammulia-monitor --since "1 hour ago"
```

## 💰 Estimated Costs

### **Monthly VPS Costs:**
- **DigitalOcean:** $5-10/month
- **Vultr:** $5-10/month  
- **Linode:** $5-10/month
- **AWS EC2:** Free tier (12 months), then ~$8/month

### **Total Monthly Cost:** $5-15 USD

This setup ensures your monitor runs 24/7 with automatic restart capabilities and proper logging for troubleshooting.