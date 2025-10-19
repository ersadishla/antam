# Telegram Integration Setup

## Quick Setup Guide

### 1. Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Save the **bot token** (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Get Your Chat ID

1. Add your bot to your group
2. Send any message to the bot in the group
3. Visit: `https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates`
4. Look for `chat.id` in the response (negative numbers are group chat IDs)
5. Save the **chat ID**

### 3. Configure the Tool

Edit `telegram_config.json`:

```json
{
  "bot_token": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
  "chat_id": "-1001234567890",
  "enable_alerts": true,
  "enable_error_notifications": false,
  "enable_summary_reports": false
}
```

### 4. Test Configuration

```bash
# Test your Telegram setup
python stock_analyzer.py --test-telegram

# Run with Telegram notifications (default)
python stock_analyzer.py --weight 1.0 --max-branches 3

# Run without Telegram notifications
python stock_analyzer.py --weight 1.0 --max-branches 3 --no-telegram
```

## Features

- **🚨 Instant Alerts**: Get notified immediately when stock becomes available
- **📊 Rich Formatting**: Beautiful messages with prices, branch locations, and availability
- **🎯 Targeted Notifications**: Only sends alerts when stock exists (no spam)
- **🏪 Branch Grouping**: Items grouped by store location for easy reading
- **💰 Price Formatting**: Human-readable price formatting (Rp 1.2M, Rp 242.8K, etc.)

## Message Format

The bot sends formatted messages like:

```
🏆 LOGAM MULIA STOCK ALERT 🏆
📅 2025-01-19 15:30:45

🎯 Available Gold Items Found:

1. 🏪 Surabaya Darmo (Surabaya)
   • 1g - Rp 242.8M - Available
   • 5g - Rp 1,195.5M - Limited Stock

2. 🏪 Bandung (Bandung)
   • 2g - Rp 480.6M - Available

🔔 Quick Actions:
• Visit: https://logammulia.com/id/purchase/gold
• Check location: Select your preferred branch
• Act fast: Limited stock available!

#logammulia #gold #investment #stockalert
```

## Troubleshooting

**Bot not responding?**
- Check bot token is correct
- Ensure bot is added to the group
- Verify chat ID (group IDs are negative numbers)

**No notifications?**
- Check `enable_alerts` is `true` in config
- Make sure stock is actually available (the tool only sends alerts when stock exists)
- Try `--test-telegram` to verify connection

**Error messages?**
- Enable `enable_error_notifications` in config to get debugging info
- Check your bot has permission to send messages in the group