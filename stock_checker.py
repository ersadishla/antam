#!/usr/bin/env python3
"""
LogamMulia Stock Availability Checker
Checks gold stock availability at specific branches
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
from datetime import datetime
from branch_parser import BranchLocationParser

class LogamMuliaStockChecker:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://logammulia.com"
        self.branch_parser = BranchLocationParser()
        self.setup_headers()
        self.current_branch = None
        self.csrf_token = None
        
    def setup_headers(self):
        """Setup realistic browser headers"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'id-ID,id;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        })
    
    def load_branches(self, location_file='change-location.html'):
        """Load branch locations from file"""
        self.branch_parser.location_html_file = location_file
        return self.branch_parser.parse_locations()
    
    def extract_csrf_token(self, response):
        """Extract CSRF token from response"""
        soup = BeautifulSoup(response.content, 'html.parser')
        meta_token = soup.find('meta', {'name': '_token'})
        if meta_token:
            self.csrf_token = meta_token.get('content', '')
            return self.csrf_token
        
        # Also check for hidden input
        hidden_input = soup.find('input', {'name': '_token'})
        if hidden_input:
            self.csrf_token = hidden_input.get('value', '')
            
        return self.csrf_token
    
    def simulate_browser_behavior(self):
        """Simulate realistic browser behavior before making requests"""
        # Visit the homepage first
        try:
            self.session.get(self.base_url, timeout=15)
            time.sleep(random.uniform(1, 2))
            
            # Visit a random page to simulate browsing
            pages = ['/id/about', '/id/contact', '/id/product-list']
            random_page = random.choice(pages)
            self.session.get(f"{self.base_url}{random_page}", timeout=15)
            time.sleep(random.uniform(0.5, 1.5))
            
        except Exception:
            pass  # Continue even if these fail
    
    def get_page_with_retry(self, url, max_retries=5):
        """Get page with advanced retry logic and different techniques"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
        for attempt in range(max_retries):
            try:
                # Rotate user agent
                self.session.headers['User-Agent'] = random.choice(user_agents)
                
                # Add random delay
                if attempt > 0:
                    delay = random.uniform(3, 8)
                    print(f"Retry attempt {attempt + 1}/{max_retries}, waiting {delay:.1f}s...")
                    time.sleep(delay)
                
                # Simulate browser behavior before request
                if attempt > 0:
                    self.simulate_browser_behavior()
                
                # Make request with different approaches
                if attempt == 0:
                    # Standard approach
                    response = self.session.get(url, timeout=30)
                elif attempt == 1:
                    # With referer
                    self.session.headers['Referer'] = self.base_url
                    response = self.session.get(url, timeout=30)
                elif attempt == 2:
                    # With cache control disabled
                    self.session.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                    self.session.headers['Pragma'] = 'no-cache'
                    response = self.session.get(url, timeout=30)
                else:
                    # Reset session and try again
                    self.session = requests.Session()
                    self.setup_headers()
                    self.simulate_browser_behavior()
                    response = self.session.get(url, timeout=30)
                
                print(f"Response status: {response.status_code}")
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 403:
                    print(f"403 Forbidden - Attempt {attempt + 1}/{max_retries}")
                    if attempt == max_retries - 1:
                        print("Max retries reached. Trying alternative approach...")
                        # Try to access with a different session
                        return self.try_alternative_access(url)
                else:
                    print(f"Status code: {response.status_code}")
                    
            except requests.RequestException as e:
                print(f"Request failed: {e}")
                if attempt == max_retries - 1:
                    return None
                    
        return None
    
    def try_alternative_access(self, url):
        """Try alternative access methods"""
        try:
            # Try using requests without session
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'id-ID,id;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code == 200:
                print("Alternative access successful!")
                return response
                
        except Exception as e:
            print(f"Alternative access failed: {e}")
            
        return None
    
    def select_branch(self, branch_code):
        """Select a specific branch location"""
        if not self.branch_parser.branches:
            if not self.load_branches():
                return False
        
        branch = self.branch_parser.get_branch_by_code(branch_code)
        if not branch:
            print(f"Branch code {branch_code} not found")
            return False
        
        print(f"Selecting branch: {branch['branch_name']} ({branch['city']})")
        
        # First, visit the main page to get session and CSRF token
        response = self.get_page_with_retry(f"{self.base_url}/id/purchase/gold")
        
        if not response:
            print("Failed to load main page after multiple attempts")
            return False
        
        self.extract_csrf_token(response)
        
        # Now submit location change form
        location_data = {
            '_token': self.csrf_token,
            'location': branch_code
        }
        
        try:
            change_response = self.session.post(
                f"{self.base_url}/do-change-location",
                data=location_data,
                timeout=30,
                allow_redirects=True
            )
            
            if change_response.status_code == 200:
                self.current_branch = branch
                print(f"Successfully selected branch: {branch['branch_name']}")
                return True
            else:
                print(f"Failed to change location: {change_response.status_code}")
                return False
                
        except requests.RequestException as e:
            print(f"Request error during branch selection: {e}")
            return False
    
    def check_stock_availability(self, product_weight=None):
        """Check stock availability for products"""
        if not self.current_branch:
            print("No branch selected. Use select_branch() first.")
            return False
        
        # Reload the purchase page with selected branch using retry logic
        response = self.get_page_with_retry(f"{self.base_url}/id/purchase/gold")
        
        if not response:
            print("Failed to load purchase page after multiple attempts")
            return False
        
        soup = BeautifulSoup(response.content, 'html.parser')
        self._last_soup = soup  # Store for debugging
        stock_data = self.extract_stock_info(soup, product_weight)
        
        return stock_data
    
    def extract_stock_info(self, soup, target_weight=None):
        """Extract stock information from the page"""
        stock_info = {
            'branch': self.current_branch,
            'check_time': datetime.now().isoformat(),
            'products': [],
            'out_of_stock': [],
            'limited_stock': [],
            'available': []
        }
        
        # Look for stock indicators in product inputs
        product_inputs = soup.find_all('input', {'price': True})
        
        for input_elem in product_inputs:
            try:
                weight = float(input_elem.get('weight', 0))
                weight_grams = weight * 1000 if weight < 1 else weight
                price = float(input_elem.get('price', '').replace('.', '').replace(',', ''))
                input_id = input_elem.get('id', '')
                
                # Check if input is disabled
                is_disabled = input_elem.has_attr('disabled')
                max_quantity = input_elem.get('max', '999')
                
                # Look for the specific no-stock indicator
                stock_status = 'Available'
                is_available = True
                
                # Find the product container that might have stock indicators
                product_container = input_elem.find_parent('div')
                while product_container and len(product_container.find_all('input', {'price': True})) <= 1:
                    product_container = product_container.find_parent('div')
                    if product_container and len(product_container.find_all('input', {'price': True})) > 1:
                        break
                
                # Check for no-stock indicator in the container or nearby elements
                if product_container:
                    # Check for specific "no-stock" span
                    no_stock_span = product_container.find('span', class_='no-stock')
                    if no_stock_span and 'Belum tersedia' in no_stock_span.get_text():
                        stock_status = 'Out of Stock'
                        is_available = False
                    
                    # Also check for text-based indicators
                    container_text = product_container.get_text()
                    if 'Belum tersedia' in container_text:
                        stock_status = 'Out of Stock'
                        is_available = False
                    elif 'habis' in container_text.lower() or 'kosong' in container_text.lower():
                        stock_status = 'Out of Stock'
                        is_available = False
                    elif 'terbatas' in container_text.lower() or 'limited' in container_text.lower():
                        stock_status = 'Limited Stock'
                
                # Additional check: look for disabled input
                if is_disabled:
                    stock_status = 'Out of Stock'
                    is_available = False
                
                product = {
                    'weight_grams': weight_grams,
                    'weight_kg': weight,
                    'price_idr': price,
                    'input_id': input_id,
                    'is_available': is_available,
                    'max_quantity': max_quantity,
                    'stock_status': stock_status
                }
                
                stock_info['products'].append(product)
                
                # Categorize by stock status
                if product['stock_status'] == 'Out of Stock':
                    stock_info['out_of_stock'].append(product)
                elif product['stock_status'] == 'Limited Stock':
                    stock_info['limited_stock'].append(product)
                else:
                    stock_info['available'].append(product)
                
            except (ValueError, AttributeError):
                continue
        
        # Filter by target weight if specified
        if target_weight:
            stock_info['products'] = [p for p in stock_info['products'] if p['weight_grams'] == target_weight]
        
        return stock_info
    
    def check_all_branches_stock(self):
        """Check stock across all branches"""
        if not self.branch_parser.branches:
            self.load_branches()
        
        all_branches_stock = []
        
        for branch in self.branch_parser.branches:
            print(f"\nChecking stock for: {branch['branch_name']}...")
            
            if self.select_branch(branch['branch_code']):
                time.sleep(random.uniform(2, 4))  # Rate limiting
                
                stock_data = self.check_stock_availability()
                if stock_data:
                    all_branches_stock.append(stock_data)
            
            time.sleep(random.uniform(3, 5))  # Longer delay between branches
        
        return all_branches_stock
    
    def find_product_in_branches(self, target_weight):
        """Find which branches have a specific product weight in stock"""
        all_stock = self.check_all_branches_stock([target_weight])
        
        available_branches = []
        
        for branch_stock in all_stock:
            for product in branch_stock['products']:
                if product['weight_grams'] == target_weight and product['is_available']:
                    available_branches.append({
                        'branch': branch_stock['branch'],
                        'product': product,
                        'check_time': branch_stock['check_time']
                    })
        
        return available_branches
    
    def debug_stock_detection(self, soup):
        """Debug function to show stock detection elements"""
        print("\n=== DEBUGGING STOCK DETECTION ===")
        
        # Find all no-stock spans
        no_stock_spans = soup.find_all('span', class_='no-stock')
        print(f"Found {len(no_stock_spans)} 'no-stock' spans:")
        for i, span in enumerate(no_stock_spans):
            print(f"  {i+1}. Text: '{span.get_text().strip()}'")
            print(f"     Parent: {span.parent.name if span.parent else 'None'}")
            print(f"     Classes: {span.parent.get('class', []) if span.parent else []}")
        
        # Look for product inputs and their containers
        product_inputs = soup.find_all('input', {'price': True})
        print(f"\nFound {len(product_inputs)} product inputs")
        
        for i, input_elem in enumerate(product_inputs[:3]):  # Check first 3
            weight = input_elem.get('weight', 'N/A')
            print(f"\nInput {i+1}:")
            print(f"  Weight: {weight}")
            print(f"  ID: {input_elem.get('id', 'N/A')}")
            print(f"  Disabled: {input_elem.has_attr('disabled')}")
            
            # Check parent containers for stock indicators
            container = input_elem.find_parent('div')
            level = 0
            while container and level < 5:
                no_stock = container.find('span', class_='no-stock')
                if no_stock:
                    print(f"  Level {level}: Found no-stock span: '{no_stock.get_text().strip()}'")
                    break
                
                if 'Belum tersedia' in container.get_text():
                    print(f"  Level {level}: Found 'Belum tersedia' text")
                    break
                    
                container = container.find_parent('div')
                level += 1
        
        print("=== END DEBUG ===\n")
    
    def print_stock_summary(self, stock_data, debug=False):
        """Print stock availability summary"""
        if not stock_data:
            print("No stock data available")
            return
        
        branch = stock_data['branch']
        print(f"\n" + "="*60)
        print(f"STOCK AVAILABILITY - {branch['branch_name'].upper()}")
        print(f"City: {branch['city']}")
        print(f"Check Time: {stock_data['check_time']}")
        print("="*60)
        
        print(f"\nAvailable Products ({len(stock_data['available'])}):")
        for product in stock_data['available']:
            print(f"  ✓ {product['weight_grams']}g - Rp {product['price_idr']:,} - Max qty: {product['max_quantity']}")
        
        if stock_data['limited_stock']:
            print(f"\nLimited Stock ({len(stock_data['limited_stock'])}):")
            for product in stock_data['limited_stock']:
                print(f"  ⚠ {product['weight_grams']}g - Rp {product['price_idr']:,} - Limited availability")
        
        if stock_data['out_of_stock']:
            print(f"\nOut of Stock ({len(stock_data['out_of_stock'])}):")
            for product in stock_data['out_of_stock']:
                print(f"  ✗ {product['weight_grams']}g - Rp {product['price_idr']:,}")
        
        print("="*60)
        
        # Show debug info if requested
        if debug and hasattr(self, '_last_soup'):
            self.debug_stock_detection(self._last_soup)
    
    def save_stock_data(self, stock_data, filename=None):
        """Save stock data to file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            branch_name = stock_data['branch']['branch_name'].replace(' ', '_').replace('/', '_')
            filename = f'stock_{branch_name}_{timestamp}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(stock_data, f, indent=2, ensure_ascii=False)
        
        print(f"Stock data saved to {filename}")
        return filename

def main():
    """Main function for testing"""
    checker = LogamMuliaStockChecker()
    
    # Load branches
    if not checker.load_branches():
        print("Failed to load branches")
        return
    
    # Example: Check a specific branch
    # First, let's list available branches
    print("Available branches:")
    for branch in checker.branch_parser.branches[:5]:  # Show first 5
        print(f"  {branch['branch_code']}: {branch['branch_name']} ({branch['city']})")
    
    print("\nUse the stock_checker interactively or integrate with other scripts")

if __name__ == "__main__":
    main()