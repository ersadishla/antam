# LogamMulia Monitor Timer Configurations
# Choose one based on your monitoring needs

# ============================
# OPTION 1: Aggressive Monitoring (Every 5 minutes)
# ============================
# File: logammulia-monitor-aggressive.timer
[Unit]
Description=Run LogamMulia Gold Stock Monitor every 5 minutes
Requires=logammulia-monitor.service

[Timer]
OnCalendar=*:0/5
Persistent=true
RandomizedDelaySec=30

[Install]
WantedBy=timers.target

# ============================
# OPTION 2: Frequent Monitoring (Every 10 minutes) - RECOMMENDED
# ============================
# File: logammulia-monitor-frequent.timer
[Unit]
Description=Run LogamMulia Gold Stock Monitor every 10 minutes
Requires=logammulia-monitor.service

[Timer]
OnCalendar=*:0/10
Persistent=true
RandomizedDelaySec=45

[Install]
WantedBy=timers.target

# ============================
# OPTION 3: Moderate Monitoring (Every 15 minutes) - BALANCED
# ============================
# File: logammulia-monitor-moderate.timer
[Unit]
Description=Run LogamMulia Gold Stock Monitor every 15 minutes
Requires=logammulia-monitor.service

[Timer]
OnCalendar=*:0/15
Persistent=true
RandomizedDelaySec=60

[Install]
WantedBy=timers.target

# ============================
# OPTION 4: Comprehensive Monitoring (Different weights hourly)
# ============================
# This requires multiple services, see setup guide for details

# Service example for 1 gram gold
# File: logammulia-monitor-1gram.service
[Unit]
Description=LogamMulia Gold Stock Monitor - 1 gram
After=network.target

[Service]
Type=oneshot
User=logammulia
Group=logammulia
WorkingDirectory=/opt/logammulia-monitor
ExecStart=/usr/bin/python3 /opt/logammulia-monitor/stock_analyzer.py --weight 1.0 --max-branches 15
StandardOutput=journal
StandardError=journal

# Timer example - runs at minute 5 of every hour
# File: logammulia-monitor-1gram.timer
[Unit]
Description=Monitor 1 gram gold at 5 minutes past every hour
Requires=logammulia-monitor-1gram.service

[Timer]
OnCalendar=*-*-* 05:00:00
Persistent=true

[Install]
WantedBy=timers.target

# ============================
# SETUP INSTRUCTIONS:
# ============================
# 1. Choose your desired timer configuration
# 2. Copy the appropriate .timer file to /etc/systemd/system/
# 3. Modify the service file if needed (change weight, branches, etc.)
# 4. Run: sudo systemctl daemon-reload
# 5. Run: sudo systemctl enable your-chosen-timer.timer
# 6. Run: sudo systemctl start your-chosen-timer.timer
# 7. Check: sudo systemctl list-timers

# Example setup for frequent monitoring:
# sudo cp logammulia-monitor.service /etc/systemd/system/
# sudo cp logammulia-monitor-frequent.timer /etc/systemd/system/logammulia-monitor.timer
# sudo systemctl daemon-reload
# sudo systemctl enable logammulia-monitor.timer
# sudo systemctl start logammulia-monitor.timer