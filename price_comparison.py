import sqlite3
import pandas as pd
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

class PriceComparison:
    def __init__(self, db_path='pharmiliar.db'):
        self.db_path = db_path
        
    def connect(self):
        """Connect to the database"""
        return sqlite3.connect(self.db_path)
    
    def search_service(self, search_term, threshold=80):
        """Search for a service using fuzzy matching"""
        conn = self.connect()
        
        # Get all services
        query = """
        SELECT s.*, h.name as hospital_name 
        FROM services s
        JOIN hospitals h ON s.hospital_id = h.id
        """
        services = pd.read_sql_query(query, conn)
        
        # Perform fuzzy matching on description
        matches = []
        for _, service in services.iterrows():
            ratio = fuzz.token_sort_ratio(search_term.lower(), 
                                        str(service['description']).lower())
            if ratio >= threshold:
                matches.append({
                    'service': service,
                    'match_ratio': ratio
                })
        
        # Sort by match quality
        matches.sort(key=lambda x: x['match_ratio'], reverse=True)
        
        conn.close()
        return matches
    
    def compare_prices(self, service_code):
        """Compare prices for a specific service across hospitals"""
        conn = self.connect()
        
        query = """
        SELECT s.*, h.name as hospital_name 
        FROM services s
        JOIN hospitals h ON s.hospital_id = h.id
        WHERE s.code = ?
        """
        
        prices = pd.read_sql_query(query, conn, params=(service_code,))
        conn.close()
        
        if len(prices) == 0:
            return None
            
        return {
            'service': prices.iloc[0]['description'],
            'prices': prices[['hospital_name', 'base_price', 'max_price']].to_dict('records'),
            'stats': {
                'avg_price': prices['base_price'].mean(),
                'min_price': prices['base_price'].min(),
                'max_price': prices['base_price'].max(),
                'price_range': prices['base_price'].max() - prices['base_price'].min()
            }
        }
    
    def find_alternatives(self, service_code, price_threshold=0.2):
        """Find alternative services with similar descriptions but lower prices"""
        conn = self.connect()
        
        # Get the original service
        query = "SELECT * FROM services WHERE code = ?"
        original = pd.read_sql_query(query, conn, params=(service_code,))
        
        if len(original) == 0:
            conn.close()
            return None
            
        original_service = original.iloc[0]
        
        # Get all services in the same category
        query = """
        SELECT s.*, h.name as hospital_name 
        FROM services s
        JOIN hospitals h ON s.hospital_id = h.id
        WHERE s.category = ? AND s.code != ?
        """
        alternatives = pd.read_sql_query(query, conn, 
                                       params=(original_service['category'], service_code))
        
        conn.close()
        
        # Find similar services with lower prices
        matches = []
        for _, service in alternatives.iterrows():
            ratio = fuzz.token_sort_ratio(str(original_service['description']).lower(),
                                        str(service['description']).lower())
            
            # Check if price is lower within threshold
            if (ratio >= 70 and 
                service['base_price'] < original_service['base_price'] * (1 + price_threshold)):
                matches.append({
                    'service': service,
                    'similarity': ratio,
                    'savings': original_service['base_price'] - service['base_price']
                })
        
        return sorted(matches, key=lambda x: x['savings'], reverse=True)

def main():
    # Example usage
    comparator = PriceComparison()
    
    # Example 1: Search for a service
    print("\nSearching for 'x-ray'...")
    matches = comparator.search_service('x-ray')
    for match in matches[:5]:
        service = match['service']
        print(f"Service: {service['description']}")
        print(f"Price: {service['base_price']}")
        print(f"Match quality: {match['match_ratio']}%\n")
    
    # Example 2: Compare prices
    if matches:
        service_code = matches[0]['service']['code']
        print(f"\nComparing prices for {service_code}...")
        comparison = comparator.compare_prices(service_code)
        if comparison:
            print(f"Service: {comparison['service']}")
            print("\nPrices by Hospital:")
            for price in comparison['prices']:
                print(f"{price['hospital_name']}: {price['base_price']}")
            print("\nPrice Statistics:")
            for stat, value in comparison['stats'].items():
                print(f"{stat}: {value}")
    
    # Example 3: Find alternatives
    if matches:
        print(f"\nFinding alternatives for {service_code}...")
        alternatives = comparator.find_alternatives(service_code)
        if alternatives:
            print("\nAlternative Services:")
            for alt in alternatives[:5]:
                service = alt['service']
                print(f"Service: {service['description']}")
                print(f"Price: {service['base_price']}")
                print(f"Potential savings: {alt['savings']}")
                print(f"Similarity: {alt['similarity']}%\n")

if __name__ == "__main__":
    main()
