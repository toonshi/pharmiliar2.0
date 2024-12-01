from typing import Dict, List, Tuple
from service_mapper import OpenAIServiceMapper
from journey_planner import MedicalJourneyPlanner

class MedicalCostEstimator:
    def __init__(self, api_key: str):
        """Initialize with both journey planner and service mapper."""
        self.journey_planner = MedicalJourneyPlanner(api_key)
        self.service_mapper = OpenAIServiceMapper(api_key)
        
    def estimate_costs(self, query: str) -> Tuple[Dict, List[Dict]]:
        """Create a journey plan with detailed cost estimates."""
        # Get the basic journey plan
        plan, alternatives = self.journey_planner.create_journey_plan(query)
        
        # Add cost estimates to immediate steps
        total_immediate_cost = 0
        for step in plan["immediate_steps"]:
            # Search for matching service
            services, _ = self.service_mapper.search(step["name"])
            if services:
                # Get the most relevant service
                service = services[0]
                step["estimated_cost"] = service["base_price"]
                step["service_id"] = service["id"]
                total_immediate_cost += service["base_price"]
            else:
                step["estimated_cost"] = None
                step["service_id"] = None
        
        plan["total_immediate_cost"] = total_immediate_cost
        
        # Add cost estimates to follow-up plan
        monthly_followup_cost = 0
        for step in plan["followup_plan"]:
            services, _ = self.service_mapper.search(step["name"])
            if services:
                service = services[0]
                step["estimated_cost"] = service["base_price"]
                step["service_id"] = service["id"]
                
                # Calculate monthly cost based on frequency
                frequency = step["frequency"]
                if frequency == "1_MONTH":
                    monthly_followup_cost += service["base_price"]
                elif frequency == "2_WEEKS":
                    monthly_followup_cost += service["base_price"] * 2
                elif frequency == "3_MONTHS":
                    monthly_followup_cost += service["base_price"] / 3
                elif frequency == "6_MONTHS":
                    monthly_followup_cost += service["base_price"] / 6
            else:
                step["estimated_cost"] = None
                step["service_id"] = None
        
        plan["monthly_followup_cost"] = monthly_followup_cost
        
        # Calculate savings for alternatives
        for alt in alternatives:
            if "estimated_savings" in alt:
                savings_percent = float(alt["estimated_savings"].split("-")[0]) / 100
                alt["immediate_cost_after_savings"] = total_immediate_cost * (1 - savings_percent)
                alt["monthly_cost_after_savings"] = monthly_followup_cost * (1 - savings_percent)
            elif "estimated_cost_increase" in alt:
                increase_percent = float(alt["estimated_cost_increase"].split("-")[0]) / 100
                alt["immediate_cost_after_increase"] = total_immediate_cost * (1 + increase_percent)
                alt["monthly_cost_after_increase"] = monthly_followup_cost * (1 + increase_percent)
        
        return plan, alternatives

    def format_cost_plan(self, plan: Dict, alternatives: List[Dict]) -> str:
        """Format the cost plan into a user-friendly text."""
        output = []
        
        # Use the journey planner's formatting first
        output.append(self.journey_planner.format_journey_plan(plan, alternatives))
        
        # Add detailed cost breakdown
        output.append("\n=== Cost Breakdown ===")
        
        # Immediate costs
        output.append("\nImmediate Costs:")
        for step in plan["immediate_steps"]:
            cost = f"KES {step['estimated_cost']:,.2f}" if step['estimated_cost'] else "Cost data not available"
            output.append(f"- {step['name']}: {cost}")
        output.append(f"\nTotal Initial Cost: KES {plan['total_immediate_cost']:,.2f}")
        
        # Monthly follow-up costs
        if plan["followup_plan"]:
            output.append("\nMonthly Follow-up Costs:")
            for step in plan["followup_plan"]:
                if step['estimated_cost']:
                    frequency = step["frequency"].replace("_", " ").lower()
                    cost = f"KES {step['estimated_cost']:,.2f} (every {frequency})"
                else:
                    cost = "Cost data not available"
                output.append(f"- {step['name']}: {cost}")
            output.append(f"\nEstimated Monthly Follow-up Cost: KES {plan['monthly_followup_cost']:,.2f}")
        
        # Cost comparisons for alternatives
        output.append("\n=== Cost Comparisons ===")
        for alt in alternatives:
            output.append(f"\n{alt['name']}:")
            if "immediate_cost_after_savings" in alt:
                output.append(f"Initial Cost: KES {alt['immediate_cost_after_savings']:,.2f}")
                output.append(f"Monthly Cost: KES {alt['monthly_cost_after_savings']:,.2f}")
                output.append(f"Potential Savings: {alt['estimated_savings']}")
            elif "immediate_cost_after_increase" in alt:
                output.append(f"Initial Cost: KES {alt['immediate_cost_after_increase']:,.2f}")
                output.append(f"Monthly Cost: KES {alt['monthly_cost_after_increase']:,.2f}")
                output.append(f"Cost Increase: {alt['estimated_cost_increase']}")
        
        # Long-term cost projection
        months = 12  # Project for a year
        base_annual_cost = plan['total_immediate_cost'] + (plan['monthly_followup_cost'] * months)
        output.append(f"\n=== Annual Cost Projection ===")
        output.append(f"Base Plan: KES {base_annual_cost:,.2f}")
        
        for alt in alternatives:
            if "monthly_cost_after_savings" in alt:
                annual = alt['immediate_cost_after_savings'] + (alt['monthly_cost_after_savings'] * months)
                output.append(f"{alt['name']}: KES {annual:,.2f}")
            elif "monthly_cost_after_increase" in alt:
                annual = alt['immediate_cost_after_increase'] + (alt['monthly_cost_after_increase'] * months)
                output.append(f"{alt['name']}: KES {annual:,.2f}")
        
        return "\n".join(output)

def main():
    import os
    from pathlib import Path
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv(os.path.join(Path(__file__).parent.parent, "config", ".env"))
    
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment variables")
        return
    
    # Initialize estimator
    estimator = MedicalCostEstimator(api_key)
    
    print("\nWelcome to Medical Cost Journey Planner")
    print("=" * 50)
    print("\nDescribe your medical condition or concern:")
    print("Examples:")
    print("- I was just diagnosed with diabetes")
    print("- I need to start hypertension treatment")
    print("- My doctor says I need regular kidney function tests")
    print("- I want to start cancer screening")
    
    while True:
        query = input("\nYour medical concern (or 'quit' to exit): ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            break
            
        if not query:
            continue
        
        print("\nAnalyzing your medical needs and calculating costs...")
        try:
            # Create cost plan
            plan, alternatives = estimator.estimate_costs(query)
            
            # Format and display the plan
            formatted_plan = estimator.format_cost_plan(plan, alternatives)
            print("\n" + formatted_plan)
            
        except Exception as e:
            print(f"\nError creating cost plan: {str(e)}")
            print("Please try again with a different description.")
    
    print("\nThank you for using Medical Cost Journey Planner!")

if __name__ == "__main__":
    main()
