"""Service priority categorization with improved oxygen service handling."""

from typing import Dict

class ServicePriorityV2:
    # Keywords for different service types
    SERVICE_KEYWORDS = {
        "basic_test": [
            # Lab tests
            "swab", "culture", "sputum", "blood test", "urine",
            "sample", "aspirate", "analysis"
        ],
        "basic_treatment": [
            # Basic treatments
            "antibiotics", "medication", "nebulizer", "inhaler",
            "oral medication", "injection", "dressing"
        ],
        "oxygen_therapy": [  # New category for oxygen-related services
            "oxygen therapy", "oxygen administration", "oxygen catheter",
            "oxygen nk", "oxygen level", "oxygen saturation"
        ],
        "imaging": [
            # Imaging services
            "x-ray", "xray", "radiograph", "chest x", "scan",
            "ultrasound", "imaging"
        ],
        "monitoring": [
            # Monitoring services
            "monitoring", "observation", "vital signs", "follow-up"
        ],
        "advanced": [
            # Advanced procedures
            "surgery", "endoscopy", "biopsy", "ct scan", "mri",
            "specialist", "intensive"
        ]
    }
    
    # Price thresholds for different service levels
    PRICE_THRESHOLDS = {
        "basic": 500,    # Basic services up to 500 KSH
        "standard": 2000,  # Standard services up to 2000 KSH
        "advanced": float('inf')  # Advanced services (no limit)
    }
    
    @classmethod
    def get_service_priority(cls, service: Dict) -> str:
        """Determine the priority level of a service based on description and price."""
        desc_lower = service["description"].lower()
        price = float(service["price"])
        
        # Check for oxygen-related services first
        if any(kw in desc_lower for kw in cls.SERVICE_KEYWORDS["oxygen_therapy"]):
            return "oxygen_therapy"
        
        # Check for monitoring services
        if any(kw in desc_lower for kw in cls.SERVICE_KEYWORDS["monitoring"]):
            return "monitoring"
        
        # Check for basic tests
        if price <= cls.PRICE_THRESHOLDS["basic"]:
            if any(kw in desc_lower for kw in cls.SERVICE_KEYWORDS["basic_test"]):
                return "basic_test"
            elif any(kw in desc_lower for kw in cls.SERVICE_KEYWORDS["basic_treatment"]):
                return "basic_treatment"
        
        # Check for imaging services
        if any(kw in desc_lower for kw in cls.SERVICE_KEYWORDS["imaging"]):
            return "imaging"
        
        # Check for advanced procedures
        if any(kw in desc_lower for kw in cls.SERVICE_KEYWORDS["advanced"]):
            return "advanced"
            
        # Default categorization based on price
        if price <= cls.PRICE_THRESHOLDS["basic"]:
            return "basic_treatment"
        elif price <= cls.PRICE_THRESHOLDS["standard"]:
            return "standard"
        else:
            return "advanced"
    
    @classmethod
    def get_priority_weight(cls, priority: str) -> float:
        """Get the weight for a priority level for sorting."""
        weights = {
            "basic_test": 5.0,
            "basic_treatment": 4.0,
            "oxygen_therapy": 3.8,  # Special weight for oxygen services
            "monitoring": 3.5,
            "imaging": 3.0,
            "standard": 2.5,
            "advanced": 2.0
        }
        return weights.get(priority, 1.0)
    
    @classmethod
    def get_priority_display_name(cls, priority: str) -> str:
        """Get a display name for a priority level."""
        names = {
            "basic_test": "Essential Tests",
            "basic_treatment": "Basic Treatments",
            "oxygen_therapy": "Oxygen Therapy",  # New display name
            "monitoring": "Monitoring Services",
            "imaging": "Imaging Services",
            "standard": "Standard Procedures",
            "advanced": "Advanced Procedures"
        }
        return names.get(priority, "Other Services")
    
    @classmethod
    def consolidate_oxygen_services(cls, services: list) -> list:
        """Consolidate similar oxygen-related services."""
        # Group oxygen services by department
        dept_services = {}
        non_oxygen = []
        
        for service in services:
            if cls.get_service_priority(service) == "oxygen_therapy":
                dept = service["department"]
                if dept not in dept_services:
                    dept_services[dept] = []
                dept_services[dept].append(service)
            else:
                non_oxygen.append(service)
        
        # Keep only the best oxygen service per department
        consolidated = non_oxygen
        for dept_list in dept_services.values():
            # Sort by relevance score and price
            best_service = sorted(
                dept_list,
                key=lambda x: (x.get("relevance_score", 0), -float(x["price"])),
                reverse=True
            )[0]
            consolidated.append(best_service)
        
        return consolidated
