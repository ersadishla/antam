#!/usr/bin/env python3
"""
Telegram Notifier for LogamMulia Stock Checker
Sends notifications when gold stock is available
"""

import requests
import json
from datetime import datetime
from typing import List, Dict, Optional

class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.session = requests.Session()
        
    def test_connection(self) -> bool:
        """Test if the bot connection works"""
        try:
            response = self.session.get(f"{self.base_url}/getMe")
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_info = data.get('result', {})
                    print(f"✅ Connected to bot: @{bot_info.get('username', 'Unknown')}")
                    return True
            print(f"❌ Bot connection failed: {response.text}")
            return False
        except Exception as e:
            print(f"❌ Error connecting to bot: {e}")
            return False
    
    def send_message(self, message: str, parse_mode: str = 'Markdown') -> bool:
        """Send a message to the configured chat"""
        try:
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            
            response = self.session.post(f"{self.base_url}/sendMessage", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    print("✅ Telegram message sent successfully")
                    return True
            
            print(f"❌ Failed to send Telegram message: {response.text}")
            return False
            
        except Exception as e:
            print(f"❌ Error sending Telegram message: {e}")
            return False
    
    def format_stock_alert(self, available_items: List[Dict]) -> str:
        """Format available stock items into a readable message"""
        if not available_items:
            return ""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"""🏆 *LOGAM MULIA STOCK ALERT* 🏆
📅 {timestamp}

🎯 *Available Gold Items Found:*

"""
        
        # Group by branch for better readability
        branch_groups = {}
        for item in available_items:
            branch_name = item['branch_name']
            if branch_name not in branch_groups:
                branch_groups[branch_name] = []
            branch_groups[branch_name].append(item)
        
        for i, (branch_name, items) in enumerate(branch_groups.items(), 1):
            city = items[0]['city']
            message += f"\n{i}. 🏪 *{branch_name}* ({city})\n"
            
            for item in items:
                weight = item['weight_grams']
                price = item['price']
                status = item['stock_status']
                
                # Format price nicely
                if price >= 1000000:
                    price_str = f"Rp {price/1000000:.1f}M"
                elif price >= 1000:
                    price_str = f"Rp {price/1000:.0f}K"
                else:
                    price_str = f"Rp {price:,}"
                
                message += f"   • {weight}g - {price_str} - {status}\n"
        
        message += f"""
🔔 *Quick Actions:*
• Visit: https://logammulia.com/id/purchase/gold
• Check location: Select your preferred branch
• Act fast: Limited stock available!

📊 Checked {len(set(item['branch_code'] for item in available_items))} branches
💰 Items available: {len(available_items)}

#logammulia #gold #investment #stockalert
"""
        
        return message
    
    def send_stock_alert(self, available_items: List[Dict]) -> bool:
        """Send alert for available stock items"""
        if not available_items:
            print("No available items to notify about")
            return True
        
        message = self.format_stock_alert(available_items)
        if not message:
            return False
        
        print(f"📤 Sending Telegram alert for {len(available_items)} available items...")
        return self.send_message(message)
    
    def send_error_notification(self, error_msg: str, context: str = "") -> bool:
        """Send error notification for debugging"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"""⚠️ *LogamMulia Checker Error*
📅 {timestamp}
🔧 {context}

{error_msg}

#debug #error
"""
        
        return self.send_message(message)
    
    def send_summary_report(self, total_branches: int, total_products: int, 
                          available_count: int, check_duration: str = "") -> bool:
        """Send daily/weekly summary report"""
        if available_count == 0:
            return True  # Only send if there's something to report
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = f"""📊 *LogamMulia Stock Summary*
📅 {timestamp}
{f"⏱️ Duration: {check_duration}" if check_duration else ""}

📈 *Summary:*
• Branches checked: {total_branches}
• Products scanned: {total_products}
• ✅ Available: {available_count}
• ❌ Out of stock: {total_products - available_count}
• 📊 Availability rate: {(available_count/total_products*100):.1f}%

💰 *Investment opportunities found!*

#summary #logammulia #goldreport
"""
        
        return self.send_message(message)

def load_config(config_file: str = 'telegram_config.json') -> Optional[Dict]:
    """Load Telegram configuration from file"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Config file {config_file} not found")
        print("📝 Please create it with your bot token and chat ID")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing config file: {e}")
        return None

def create_sample_config(config_file: str = 'telegram_config.json'):
    """Create a sample configuration file"""
    sample_config = {
        "bot_token": "YOUR_BOT_TOKEN_HERE",
        "chat_id": "YOUR_CHAT_ID_HERE",
        "enable_alerts": True,
        "enable_error_notifications": False,
        "enable_summary_reports": False
    }
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(sample_config, f, indent=2, ensure_ascii=False)
    
    print(f"📝 Sample config created: {config_file}")
    print("🔧 Edit this file with your bot token and chat ID")

def main():
    """Test the Telegram notifier"""
    print("🧪 Testing Telegram notifier...")
    
    config = load_config()
    if not config:
        create_sample_config()
        return
    
    notifier = TelegramNotifier(
        bot_token=config['bot_token'],
        chat_id=config['chat_id']
    )
    
    if notifier.test_connection():
        # Test message
        test_items = [
            {
                'branch_name': 'Surabaya Darmo',
                'city': 'Surabaya',
                'branch_code': 'ASB1',
                'weight_grams': 1.0,
                'price': 242800000,
                'stock_status': 'Available'
            },
            {
                'branch_name': 'Bandung',
                'city': 'Bandung',
                'branch_code': 'ABDG',
                'weight_grams': 5.0,
                'price': 1195500000,
                'stock_status': 'Limited Stock'
            }
        ]
        
        notifier.send_stock_alert(test_items)

if __name__ == "__main__":
    main()