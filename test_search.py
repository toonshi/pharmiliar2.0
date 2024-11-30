from service_mapper_clean import ServiceMapper

def test_search():
    """Test improved search functionality."""
    mapper = ServiceMapper()
    
    test_cases = [
        ("Radiology", "x-ray chest"),
        ("Radiology", "ultrasound scan"),
        ("Radiology", "ct brain"),
        ("Radiology", "mri"),
        ("General", "consultation"),
        ("General", "examination"),
    ]
    
    print("\nTesting Improved Search")
    print("=" * 50)
    
    for category, term in test_cases:
        print(f"\nSearching for '{term}' in {category}:")
        services = mapper.find_services(category, term)
        
        if services:
            min_price, max_price = mapper.get_price_range(category, term)
            print(f"Found {len(services)} services")
            print(f"Price range: KES {min_price:.2f} - {max_price:.2f}")
            
            for service in services:
                print(f"- {service['description']} ({service['code']})")
                print(f"  Price: KES {service['base_price']:.2f}")
        else:
            print("No services found")
    
    mapper.close()

if __name__ == "__main__":
    test_search()
