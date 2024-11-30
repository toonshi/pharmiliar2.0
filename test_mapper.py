from service_mapper_v6 import ServiceMapper

def test_service(mapper, service_name):
    print(f"\nTesting service: {service_name}")
    print("-" * 50)
    matches = mapper.find_matching_services(service_name)
    if matches:
        print(f"Found {len(matches)} matches:")
        for match in matches:
            print(f"- {match['description']} ({match['category']}) - KES {match['price']}")
    else:
        print("No matches found")

# Test the mapper
mapper = ServiceMapper()

# Test basic services
test_services = [
    "Consultation",
    "Pain medication", 
    "Blood tests",
    "Physical exam",
    "CT scan",
    "MRI",
    "IV line",
    "Oxygen",
    "Dressing",
    "Urine test",
    "Blood sugar",
    "Liver function",
    "Ward admission",
    "ICU"
]

for service in test_services:
    test_service(mapper, service)
