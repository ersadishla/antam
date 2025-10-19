#!/usr/bin/env python3
"""
LogamMulia Branch Location Parser
Extracts branch information and handles stock availability checking
"""

from bs4 import BeautifulSoup
import json
import csv
from datetime import datetime
import re

class BranchLocationParser:
    def __init__(self, location_html_file=None):
        self.location_html_file = location_html_file
        self.branches = []
        self.soup = None
        
    def parse_locations(self):
        """Parse branch locations from HTML file"""
        if not self.location_html_file:
            print("No location HTML file provided")
            return False
            
        try:
            with open(self.location_html_file, 'r', encoding='utf-8') as file:
                self.soup = BeautifulSoup(file.read(), 'html.parser')
        except Exception as e:
            print(f"Error loading location file: {e}")
            return False
        
        # Extract branch options from select element
        select_element = self.soup.find('select', {'id': 'location'})
        if not select_element:
            print("No location select element found")
            return False
        
        options = select_element.find_all('option')
        
        for option in options:
            value = option.get('value', '').strip()
            text = option.get_text().strip()
            
            if value and text != 'Pilih lokasi Butik Emas Logam Mulia':
                branch_info = self.parse_branch_info(value, text)
                self.branches.append(branch_info)
        
        print(f"Found {len(self.branches)} branches")
        return True
    
    def parse_branch_info(self, branch_code, full_text):
        """Parse branch information from option text"""
        # Extract city and branch type
        parts = full_text.split(',')
        
        # Clean up branch name
        branch_name = parts[0].strip()
        if 'BELM - ' in branch_name:
            branch_name = branch_name.replace('BELM - ', '')
        
        # Extract city
        city = parts[-1].strip() if len(parts) > 1 else branch_name
        
        # Determine branch type with exact patterns
        branch_type = 'Regular'
        is_pickup_only = False
        can_ship = True
        
        if 'pengambilan Di Butik' in branch_name or 'Pengambilan Di Butik' in branch_name:
            branch_type = 'Pickup Only'
            is_pickup_only = True
            can_ship = False
        elif 'Pengiriman Ekspedisi' in branch_name:
            branch_type = 'Shipping Only'
            can_ship = True
        
        # Clean branch name further
        if ' (' in branch_name:
            branch_name = branch_name.split(' (')[0].strip()
        
        return {
            'branch_code': branch_code,
            'branch_name': branch_name,
            'city': city,
            'branch_type': branch_type,
            'can_ship': can_ship,
            'is_pickup_only': is_pickup_only,
            'full_address': full_text,
            'is_active': True,
            'stock_data': {}
        }
    
    def get_branches_by_city(self):
        """Group branches by city"""
        cities = {}
        for branch in self.branches:
            city = branch['city']
            if city not in cities:
                cities[city] = []
            cities[city].append(branch)
        return cities
    
    def get_branch_by_code(self, branch_code):
        """Get branch by code"""
        for branch in self.branches:
            if branch['branch_code'] == branch_code:
                return branch
        return None
    
    def get_shipping_branches(self):
        """Get branches that can ship via courier"""
        return [branch for branch in self.branches if branch['can_ship']]
    
    def get_pickup_only_branches(self):
        """Get branches that are pickup only"""
        return [branch for branch in self.branches if branch['is_pickup_only']]
    
    def print_branch_summary(self):
        """Print summary of all branches"""
        print("\n" + "="*80)
        print("LOGAM MULIA BRANCH LOCATIONS")
        print("="*80)
        
        cities = self.get_branches_by_city()
        shipping_branches = self.get_shipping_branches()
        pickup_branches = self.get_pickup_only_branches()
        
        print(f"\nTotal Branches: {len(self.branches)}")
        print(f"Cities Covered: {len(cities)}")
        print(f"Shipping Capable: {len(shipping_branches)}")
        print(f"Pickup Only: {len(pickup_branches)}")
        
        print(f"\n📦 SHIPPING BRANCHES (Can send via courier):")
        for branch in sorted(shipping_branches, key=lambda x: x['city']):
            shipping_icon = "🚚" if branch['branch_type'] == 'Shipping Only' else "📦"
            print(f"  {shipping_icon} {branch['city']} - {branch['branch_name']} ({branch['branch_code']})")
        
        if pickup_branches:
            print(f"\n🏪 PICKUP ONLY BRANCHES:")
            for branch in sorted(pickup_branches, key=lambda x: x['city']):
                print(f"  🏪 {branch['city']} - {branch['branch_name']} ({branch['branch_code']})")
        
        print("="*80)
    
    def save_branch_data(self, filename=None):
        """Save branch data to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'logammulia_branches_{timestamp}.json'
        
        data = {
            'extraction_date': datetime.now().isoformat(),
            'total_branches': len(self.branches),
            'branches': self.branches
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Branch data saved to {filename}")
        return filename

def main():
    """Main function"""
    parser = BranchLocationParser('change-location.html')
    
    if parser.parse_locations():
        parser.print_branch_summary()
        parser.save_branch_data()
        return True
    else:
        print("Failed to parse branch locations")
        return False

if __name__ == "__main__":
    main()