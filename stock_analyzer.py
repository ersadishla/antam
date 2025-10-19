#!/usr/bin/env python3
"""
LogamMulia Branch Stock Analyzer
Comprehensive tool for analyzing gold stock availability across branches
"""

import json
import pandas as pd
from datetime import datetime
from stock_checker import LogamMuliaStockChecker
from branch_parser import BranchLocationParser
from telegram_notifier import TelegramNotifier, load_config
import argparse
import time
import os

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
        
        if not self.stock_checker.select_branch(branch_code):
            return None
        
        time.sleep(2)  # Wait for page to load
        stock_data = self.stock_checker.check_stock_availability(target_weights)
        
        # Send Telegram alert if stock is available
        if stock_data and self.telegram_enabled and self.telegram_notifier:
            available_items = self.extract_available_items(stock_data, target_weights)
            if available_items:
                print(f"📱 Sending Telegram alert for {len(available_items)} available items at {stock_data['branch']['branch_name']}")
                self.telegram_notifier.send_stock_alert(available_items)
        
        return stock_data
    
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
    
    def create_availability_report(self, target_weights=None):
        """Create comprehensive availability report"""
        if not self.all_stock_data:
            print("No stock data available. Run stock checks first.")
            return None
        
        report = {
            'report_date': datetime.now().isoformat(),
            'total_branches_checked': len(self.all_stock_data),
            'target_weights': target_weights,
            'summary': {},
            'branch_details': []
        }
        
        total_products = 0
        total_available = 0
        total_out_of_stock = 0
        total_limited = 0
        
        for stock_data in self.all_stock_data:
            branch_info = {
                'branch': stock_data['branch'],
                'check_time': stock_data['check_time'],
                'total_products': len(stock_data['products']),
                'available_count': len(stock_data['available']),
                'out_of_stock_count': len(stock_data['out_of_stock']),
                'limited_stock_count': len(stock_data['limited_stock']),
                'products': []
            }
            
            total_products += branch_info['total_products']
            total_available += branch_info['available_count']
            total_out_of_stock += branch_info['out_of_stock_count']
            total_limited += branch_info['limited_stock_count']
            
            # Add product details
            for product in stock_data['products']:
                if not target_weights or product['weight_grams'] in target_weights:
                    branch_info['products'].append({
                        'weight_grams': product['weight_grams'],
                        'price': product['price_idr'],
                        'stock_status': product['stock_status'],
                        'is_available': product['is_available']
                    })
            
            report['branch_details'].append(branch_info)
        
        report['summary'] = {
            'total_products_checked': total_products,
            'total_available': total_available,
            'total_out_of_stock': total_out_of_stock,
            'total_limited_stock': total_limited,
            'availability_rate': (total_available / total_products * 100) if total_products > 0 else 0
        }
        
        return report
    
    def print_availability_summary(self, report):
        """Print availability summary"""
        if not report:
            return
        
        summary = report['summary']
        print(f"\n" + "="*80)
        print("LOGAM MULIA STOCK AVAILABILITY REPORT")
        print("="*80)
        print(f"Report Date: {report['report_date']}")
        print(f"Branches Checked: {report['total_branches_checked']}")
        
        if report['target_weights']:
            print(f"Target Weights: {report['target_weights']}g")
        
        print(f"\nSUMMARY:")
        print(f"  Total Products Checked: {summary['total_products_checked']}")
        print(f"  Available: {summary['total_available']} ({summary['availability_rate']:.1f}%)")
        print(f"  Out of Stock: {summary['total_out_of_stock']}")
        print(f"  Limited Stock: {summary['total_limited_stock']}")
        
        print(f"\nBRANCH DETAILS:")
        for branch in report['branch_details']:
            branch_name = branch['branch']['branch_name']
            city = branch['branch']['city']
            available = branch['available_count']
            total = branch['total_products']
            
            print(f"  {city} - {branch_name}: {available}/{total} available")
            
            # Show products if limited
            if len(branch['products']) <= 5:
                for product in branch['products']:
                    status = "✓" if product['is_available'] else "✗"
                    print(f"    {status} {product['weight_grams']}g - Rp {product['price']:,}")
        
        print("="*80)
    
    def export_to_csv(self, report, filename=None):
        """Export report to CSV"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'stock_availability_report_{timestamp}.csv'
        
        rows = []
        for branch in report['branch_details']:
            for product in branch['products']:
                rows.append({
                    'branch_code': branch['branch']['branch_code'],
                    'branch_name': branch['branch']['branch_name'],
                    'city': branch['branch']['city'],
                    'branch_type': branch['branch']['branch_type'],
                    'weight_grams': product['weight_grams'],
                    'price_idr': product['price'],
                    'stock_status': product['stock_status'],
                    'is_available': product['is_available'],
                    'check_time': branch['check_time']
                })
        
        df = pd.DataFrame(rows)
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"Report exported to {filename}")
        return filename
    
    def export_to_json(self, report, filename=None):
        """Export report to JSON"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'stock_availability_report_{timestamp}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"Report exported to {filename}")
        return filename
    
    def quick_check(self, target_weight, max_branches=3, shipping_only=False):
        """Quick check for specific weight across major branches"""
        if shipping_only:
            print(f"📦 Quick stock check for {target_weight}g gold (shipping branches only)...")
            available = self.find_product_availability(target_weight, max_branches, shipping_only=True)
        else:
            print(f"Quick stock check for {target_weight}g gold...")
            available = self.find_product_availability(target_weight, max_branches)
        
        if available:
            print(f"\n✓ Found {target_weight}g gold at {len(available)} branch(es):")
            for i, branch in enumerate(available, 1):
                shipping_icon = "📦" if shipping_only else ""
                print(f"  {i}. {shipping_icon}{branch['branch_name']} ({branch['city']})")
                print(f"     Status: {branch['stock_status']}")
                print(f"     Price: Rp {branch['price']:,}")
                print(f"     Checked: {branch['check_time']}")
                print()
        else:
            location_type = "shipping branches" if shipping_only else "checked branches"
            print(f"\n✗ {target_weight}g gold not available at {location_type}")
            print("Try checking more branches or different weights")
        
        return available
    
    def check_all_shipping_branches(self, target_weight=None):
        """Check stock across all branches that can ship via courier"""
        if not self.branch_parser.branches:
            self.load_branches()
        
        shipping_branches = self.branch_parser.get_shipping_branches()
        shipping_codes = [b['branch_code'] for b in shipping_branches]
        
        print(f"📦 Checking {len(shipping_branches)} shipping-capable branches...")
        print("(Branches that can send gold via courier)\n")
        
        if target_weight:
            print(f"Target: {target_weight}g gold")
        
        results = self.check_multiple_branches(shipping_codes, [target_weight] if target_weight else None)
        return results
    
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
    """Main function"""
    parser = argparse.ArgumentParser(description='Analyze LogamMulia gold stock availability')
    parser.add_argument('--weight', type=float, help='Check specific weight in grams')
    parser.add_argument('--branches', nargs='+', help='Specific branch codes to check')
    parser.add_argument('--max-branches', type=int, default=5, help='Maximum branches to check')
    parser.add_argument('--export', choices=['csv', 'json', 'both'], default='both')
    parser.add_argument('--quick', action='store_true', help='Quick check mode')
    parser.add_argument('--debug', action='store_true', help='Debug mode - show HTML detection details')
    parser.add_argument('--debug-branch', help='Debug specific branch for stock detection')
    parser.add_argument('--shipping-only', action='store_true', help='Check only shipping-capable branches (courier delivery)')
    parser.add_argument('--no-telegram', action='store_true', help='Disable Telegram notifications')
    parser.add_argument('--test-telegram', action='store_true', help='Test Telegram configuration and send test message')
    
    args = parser.parse_args()
    
    # Initialize analyzer with Telegram settings
    analyzer = StockAnalyzer(enable_telegram=not args.no_telegram)
    
    # Load branches
    if not analyzer.load_branches():
        print("Failed to load branches")
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
        target_weight = args.weight
        
        if args.quick:
            # Quick check for specific weight
            available = analyzer.quick_check(target_weight, args.max_branches, args.shipping_only)
        else:
            # Comprehensive check
            available = analyzer.find_product_availability(target_weight, args.max_branches)
            
            if available:
                print(f"\n{target_weight}g gold available at:")
                for branch in available:
                    print(f"  - {branch['branch_name']} ({branch['city']}) - {branch['stock_status']}")
            else:
                print(f"\n{target_weight}g gold not found at checked branches")
    
    elif args.branches:
        # Check specific branches
        print(f"Checking {len(args.branches)} branches...")
        results = analyzer.check_multiple_branches(args.branches)
        
        if results:
            report = analyzer.create_availability_report()
            analyzer.print_availability_summary(report)
            
            if args.export in ['json', 'both']:
                analyzer.export_to_json(report)
            if args.export in ['csv', 'both']:
                analyzer.export_to_csv(report)
    
    elif args.shipping_only:
        # Check all shipping-capable branches
        if args.weight:
            results = analyzer.check_all_shipping_branches(args.weight)
        else:
            results = analyzer.check_all_shipping_branches()
        
        if results:
            report = analyzer.create_availability_report(args.weight)
            analyzer.print_availability_summary(report)
            
            if args.export in ['json', 'both']:
                analyzer.export_to_json(report)
            if args.export in ['csv', 'both']:
                analyzer.export_to_csv(report)
    
    else:
        # Default: check a few major branches
        print("Checking major branches for stock...")
        major_branches = ['ASB1', 'ABDG', 'AJK2', 'ASMG', 'AJOG']  # Surabaya, Bandung, Jakarta, Semarang, Yogya
        results = analyzer.check_multiple_branches(major_branches)
        
        if results:
            report = analyzer.create_availability_report()
            analyzer.print_availability_summary(report)
            
            if args.export in ['json', 'both']:
                analyzer.export_to_json(report)
            if args.export in ['csv', 'both']:
                analyzer.export_to_csv(report)
    
    return 0

if __name__ == "__main__":
    exit(main())