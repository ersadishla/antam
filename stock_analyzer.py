#!/usr/bin/env python3
"""
LogamMulia Branch Stock Analyzer
Comprehensive tool for analyzing gold stock availability across branches
"""

from datetime import datetime
from stock_checker import LogamMuliaStockChecker
from branch_parser import BranchLocationParser
from telegram_notifier import TelegramNotifier, load_config
import argparse
import time

class StockAnalyzer:
    def __init__(self, enable_telegram=True):
        self.stock_checker = LogamMuliaStockChecker()
        self.branch_parser = BranchLocationParser()
        self.all_stock_data = []
        self.telegram_enabled = enable_telegram
        self.telegram_notifier = None
        
        # Initialize Telegram if enabled
        if self.telegram_enabled:
            self.init_telegram()
    
    def init_telegram(self):
        """Initialize Telegram notifier"""
        try:
            config = load_config()
            if config and config.get('enable_alerts', True):
                self.telegram_notifier = TelegramNotifier(
                    bot_token=config['bot_token'],
                    chat_id=config['chat_id']
                )
                if self.telegram_notifier.test_connection():
                    print("📱 Telegram notifications enabled")
                    self.telegram_enabled = True
                else:
                    print("⚠️ Telegram connection failed, notifications disabled")
                    self.telegram_enabled = False
            else:
                print("📱 Telegram notifications disabled in config")
                self.telegram_enabled = False
        except Exception as e:
            print(f"⚠️ Failed to initialize Telegram: {e}")
            self.telegram_enabled = False
        
    def load_branches(self, location_file='change-location.html'):
        """Load branch locations"""
        self.branch_parser.location_html_file = location_file
        return self.branch_parser.parse_locations()
    
    def check_branch_stock(self, branch_code, target_weights=None):
        """Check stock for a specific branch"""
        print(f"Checking stock for branch {branch_code}...")
        
        try:
            if not self.stock_checker.select_branch(branch_code):
                # Send error notification if branch selection fails
                if self.telegram_enabled and self.telegram_notifier:
                    error_msg = f"Failed to select branch {branch_code} - branch might not exist or website changed"
                    self.telegram_notifier.send_error_notification(error_msg, f"Branch Selection Error - {branch_code}")
                return None
            
            time.sleep(2)  # Wait for page to load
            stock_data = self.stock_checker.check_stock_availability(target_weights)
            
            if not stock_data:
                # Send error notification if stock data retrieval fails
                if self.telegram_enabled and self.telegram_notifier:
                    error_msg = f"Failed to retrieve stock data for branch {branch_code} - possible scraping detection or website issue"
                    self.telegram_notifier.send_error_notification(error_msg, f"Scraping Error - {branch_code}")
                return None
            
            # Send Telegram alert if stock is available
            if self.telegram_enabled and self.telegram_notifier:
                available_items = self.extract_available_items(stock_data, target_weights)
                if available_items:
                    print(f"📱 Sending Telegram alert for {len(available_items)} available items at {stock_data['branch']['branch_name']}")
                    self.telegram_notifier.send_stock_alert(available_items)
                else:
                    print(f"✅ No available stock at {stock_data['branch']['branch_name']}")
            
            return stock_data
            
        except Exception as e:
            # Send error notification for any unexpected errors
            if self.telegram_enabled and self.telegram_notifier:
                error_msg = f"Unexpected error checking branch {branch_code}: {str(e)}"
                self.telegram_notifier.send_error_notification(error_msg, f"Unexpected Error - {branch_code}")
            print(f"❌ Error checking branch {branch_code}: {e}")
            return None
    
    def extract_available_items(self, stock_data, target_weights=None):
        """Extract available items from stock data"""
        if not stock_data or not stock_data.get('products'):
            return []
        
        available_items = []
        branch_info = stock_data['branch']
        
        for product in stock_data['products']:
            # Filter by target weights if specified
            if target_weights and product['weight_grams'] not in target_weights:
                continue
            
            # Only include available items
            if product['is_available']:
                available_items.append({
                    'branch_name': branch_info['branch_name'],
                    'city': branch_info['city'],
                    'branch_code': branch_info['branch_code'],
                    'weight_grams': product['weight_grams'],
                    'price': product['price_idr'],
                    'stock_status': product['stock_status'],
                    'check_time': stock_data['check_time']
                })
        
        return available_items
    
    def send_telegram_summary(self, all_results, target_weights=None):
        """Send Telegram summary of all available items found"""
        if not self.telegram_enabled or not self.telegram_notifier:
            return
        
        all_available_items = []
        for stock_data in all_results:
            available_items = self.extract_available_items(stock_data, target_weights)
            all_available_items.extend(available_items)
        
        if all_available_items:
            print(f"📱 Sending Telegram summary for {len(all_available_items)} total available items")
            self.telegram_notifier.send_stock_alert(all_available_items)
        else:
            print("📱 No available items found, no Telegram notification sent")
    
    def check_multiple_branches(self, branch_codes, target_weights=None):
        """Check stock for multiple branches"""
        results = []
        
        for i, branch_code in enumerate(branch_codes):
            print(f"\n[{i+1}/{len(branch_codes)}] Checking {branch_code}...")
            
            stock_data = self.check_branch_stock(branch_code, target_weights)
            if stock_data:
                results.append(stock_data)
            else:
                print(f"Failed to get stock data for {branch_code}")
            
            # Rate limiting with progressive delays
            if i < len(branch_codes) - 1:
                delay = 5 + (i % 3) * 3  # 5-11 seconds varying delays
                print(f"Waiting {delay} seconds before next check...")
                time.sleep(delay)
        
        self.all_stock_data = results
        
        # Send Telegram summary of all available items found
        self.send_telegram_summary(results, target_weights)
        
        return results
    
    def find_product_availability(self, target_weight, max_branches=5, shipping_only=False):
        """Find which branches have a specific product weight in stock"""
        print(f"Finding branches with {target_weight}g gold in stock...")
        
        if shipping_only:
            print(f"📦 Finding shipping-capable branches with {target_weight}g gold...")
            branches = self.branch_parser.get_shipping_branches()
        else:
            print(f"Finding branches with {target_weight}g gold...")
            # Get all branches sorted by major cities first
        
        # Prioritize major cities
        priority_cities = ['Jakarta', 'Surabaya', 'Bandung', 'Medan', 'Semarang']
        priority_branches = [b for b in branches if b['city'] in priority_cities]
        other_branches = [b for b in branches if b['city'] not in priority_cities]
        
        ordered_branches = priority_branches + other_branches
        
        # Limit to max_branches
        limited_branches = ordered_branches[:max_branches]
        branch_codes = [b['branch_code'] for b in limited_branches]
        
        results = self.check_multiple_branches(branch_codes, [target_weight])
        
        # Filter for available products
        available_branches = []
        for stock_data in results:
            for product in stock_data['products']:
                if product['weight_grams'] == target_weight and product['is_available']:
                    available_branches.append({
                        'branch_code': stock_data['branch']['branch_code'],
                        'branch_name': stock_data['branch']['branch_name'],
                        'city': stock_data['branch']['city'],
                        'stock_status': product['stock_status'],
                        'price': product['price_idr'],
                        'check_time': stock_data['check_time']
                    })
        
        return available_branches
    
    def debug_check(self, branch_code):
        """Debug check for a single branch to see stock detection details"""
        print(f"DEBUG check for branch {branch_code}...")
        
        stock_data = self.check_branch_stock(branch_code)
        if stock_data:
            # Show detailed debug info
            self.stock_checker.print_stock_summary(stock_data, debug=True)
        else:
            print("Failed to get stock data")
        
        return stock_data

def main():
    """Main function - Telegram-only notifications for stock availability"""
    parser = argparse.ArgumentParser(description='Monitor LogamMulia gold stock and send Telegram alerts')
    parser.add_argument('--weight', type=float, help='Check specific weight in grams')
    parser.add_argument('--branches', nargs='+', help='Specific branch codes to check')
    parser.add_argument('--max-branches', type=int, default=5, help='Maximum branches to check')
    parser.add_argument('--debug-branch', help='Debug specific branch for stock detection')
    parser.add_argument('--shipping-only', action='store_true', help='Check only shipping-capable branches (courier delivery)')
    parser.add_argument('--no-telegram', action='store_true', help='Disable Telegram notifications')
    parser.add_argument('--test-telegram', action='store_true', help='Test Telegram configuration and send test message')
    
    args = parser.parse_args()
    
    # Initialize analyzer with Telegram settings
    print("🚀 Starting LogamMulia Stock Monitor...")
    analyzer = StockAnalyzer(enable_telegram=not args.no_telegram)
    
    # Load branches
    if not analyzer.load_branches():
        error_msg = "Failed to load branches - website structure may have changed"
        print(f"❌ {error_msg}")
        if analyzer.telegram_enabled and analyzer.telegram_notifier:
            analyzer.telegram_notifier.send_error_notification(error_msg, "Initialization Error")
        return 1
    
    if args.test_telegram:
        if analyzer.telegram_enabled and analyzer.telegram_notifier:
            print("🧪 Testing Telegram notifications...")
            # Create test data
            test_items = [
                {
                    'branch_name': 'Test Branch',
                    'city': 'Test City',
                    'branch_code': 'TEST',
                    'weight_grams': 1.0,
                    'price': 242800000,
                    'stock_status': 'Available - Test',
                    'check_time': datetime.now().isoformat()
                }
            ]
            success = analyzer.telegram_notifier.send_stock_alert(test_items)
            if success:
                print("✅ Telegram test successful!")
            else:
                print("❌ Telegram test failed!")
        else:
            print("❌ Telegram not enabled. Check your configuration.")
        return 0
    
    if args.debug_branch:
        # Debug specific branch
        analyzer.debug_check(args.debug_branch)
        
    elif args.weight:
        # Check specific weight
        target_weight = args.weight
        print(f"🎯 Monitoring {target_weight}g gold availability...")
        
        if args.shipping_only:
            print("📦 Checking shipping-capable branches only...")
            branches = analyzer.branch_parser.get_shipping_branches()
            branch_codes = [b['branch_code'] for b in branches[:args.max_branches]]
        else:
            # Get priority branches
            priority_cities = ['Jakarta', 'Surabaya', 'Bandung', 'Medan', 'Semarang']
            priority_branches = [b for b in analyzer.branch_parser.branches if b['city'] in priority_cities]
            other_branches = [b for b in analyzer.branch_parser.branches if b['city'] not in priority_cities]
            ordered_branches = priority_branches + other_branches
            limited_branches = ordered_branches[:args.max_branches]
            branch_codes = [b['branch_code'] for b in limited_branches]
        
        print(f"📍 Checking {len(branch_codes)} branches: {', '.join(branch_codes)}")
        results = analyzer.check_multiple_branches(branch_codes, [target_weight])
        
        if results:
            available_count = sum(len(r['available']) for r in results)
            if available_count > 0:
                print(f"🎉 Found {available_count} available items!")
            else:
                print("✅ No available stock found, but monitoring is working")
        else:
            print("⚠️ Failed to check branches")
    
    elif args.branches:
        # Check specific branches
        print(f"🔍 Checking {len(args.branches)} specific branches...")
        results = analyzer.check_multiple_branches(args.branches)
        
        if results:
            available_count = sum(len(r['available']) for r in results)
            print(f"📊 Checked {len(results)} branches, found {available_count} available items")
    
    else:
        # Default: check major branches
        print("🌟 Checking major branches for stock...")
        major_branches = ['ASB1', 'ABDG', 'AJK2', 'ASMG', 'AJOG']  # Surabaya, Bandung, Jakarta, Semarang, Yogya
        print(f"📍 Checking {len(major_branches)} major branches: {', '.join(major_branches)}")
        results = analyzer.check_multiple_branches(major_branches)
        
        if results:
            available_count = sum(len(r['available']) for r in results)
            if available_count > 0:
                print(f"🎉 Found {available_count} available items across major branches!")
            else:
                print("✅ No available stock at major branches (monitoring active)")
        else:
            print("⚠️ Failed to check major branches")
    
    print("✅ Monitoring complete - check Telegram for any stock alerts!")
    return 0

if __name__ == "__main__":
    exit(main())