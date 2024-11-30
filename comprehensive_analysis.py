import os
from dotenv import load_dotenv
import openai
import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict
import networkx as nx
import matplotlib.pyplot as plt
from tqdm import tqdm

# Load environment variables
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

class ComprehensiveAnalyzer:
    def __init__(self):
        self.conn = sqlite3.connect('pharmiliar.db')
        self.service_patterns = defaultdict(list)
        self.treatment_paths = nx.DiGraph()
        
    def analyze_service_batch(self, services_batch):
        """Analyze a batch of services using OpenAI"""
        services_text = "\n".join([
            f"Service {i+1}:\nCode: {s['code']}\nDescription: {s['description']}\nPrice: KES {s['base_price']}"
            for i, s in enumerate(services_batch)
        ])
        
        prompt = f"""
        Analyze these medical services from a hospital charge sheet:
        {services_text}

        For each service, provide a JSON response with:
        1. department: Medical department
        2. service_type: Category (diagnostic, therapeutic, preventive, etc.)
        3. description_enriched: Patient-friendly description
        4. related_services: List of medical services typically used with this one
        5. treatment_pathway: Where this service typically falls in a treatment journey (initial diagnosis, treatment, follow-up)
        6. medical_conditions: Common conditions requiring this service
        7. service_group: Broader category this service belongs to
        8. typical_combinations: Other services commonly used together with this
        9. prerequisites: Required tests or conditions before this service
        10. follow_ups: Recommended follow-up services

        Format as a JSON array with one object per service.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a medical service analyzer specializing in healthcare service patterns and treatment pathways."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error in batch analysis: {str(e)}")
            return None

    def analyze_all_services(self, batch_size=5):
        """Analyze all services in the database"""
        query = "SELECT * FROM services"
        df = pd.read_sql_query(query, self.conn)
        
        all_analyses = []
        
        print(f"Analyzing {len(df)} services in batches of {batch_size}...")
        for i in tqdm(range(0, len(df), batch_size)):
            batch = df.iloc[i:i+batch_size].to_dict('records')
            analysis = self.analyze_service_batch(batch)
            if analysis:
                all_analyses.extend(analysis)
            
        return all_analyses

    def build_service_network(self, analyses):
        """Build a network of related services"""
        G = nx.DiGraph()
        
        for analysis in analyses:
            service_id = analysis.get('service_code')
            if not service_id:
                continue
                
            # Add node
            G.add_node(service_id, **analysis)
            
            # Add edges for related services
            for related in analysis.get('related_services', []):
                G.add_edge(service_id, related, relationship='related')
            
            # Add edges for treatment pathway
            for prereq in analysis.get('prerequisites', []):
                G.add_edge(prereq, service_id, relationship='prerequisite')
            
            for followup in analysis.get('follow_ups', []):
                G.add_edge(service_id, followup, relationship='follow_up')
        
        return G

    def find_common_combinations(self, analyses):
        """Find commonly combined services"""
        combinations = defaultdict(int)
        
        for analysis in analyses:
            service_group = analysis.get('service_group')
            if service_group:
                for combo in analysis.get('typical_combinations', []):
                    key = tuple(sorted([service_group, combo]))
                    combinations[key] += 1
        
        return dict(combinations)

    def generate_reports(self, analyses, service_network):
        """Generate comprehensive reports and visualizations"""
        # Convert analyses to DataFrame
        df_analyses = pd.DataFrame(analyses)
        
        # Create Excel report
        with pd.ExcelWriter('comprehensive_analysis.xlsx') as writer:
            # Service Categories
            df_analyses.groupby('department')['service_type'].value_counts().unstack().to_excel(
                writer, sheet_name='Department_Services'
            )
            
            # Treatment Pathways
            pathway_df = df_analyses.groupby('treatment_pathway')['service_group'].value_counts().unstack()
            pathway_df.to_excel(writer, sheet_name='Treatment_Pathways')
            
            # Service Combinations
            pd.DataFrame(self.find_common_combinations(analyses).items(),
                        columns=['Combination', 'Frequency']).to_excel(
                writer, sheet_name='Common_Combinations'
            )
            
            # Department Analysis
            dept_analysis = df_analyses.groupby('department').agg({
                'service_type': 'count',
                'medical_conditions': lambda x: list(set(sum(x, [])))
            })
            dept_analysis.to_excel(writer, sheet_name='Department_Analysis')

        # Generate network visualization
        plt.figure(figsize=(15, 15))
        pos = nx.spring_layout(service_network)
        nx.draw(service_network, pos, with_labels=True, node_size=1000, 
                node_color='lightblue', font_size=8)
        plt.savefig('service_network.png')
        plt.close()

        # Save network data
        nx.write_gexf(service_network, 'service_network.gexf')

    def run_analysis(self):
        """Run the complete analysis pipeline"""
        print("Starting comprehensive analysis...")
        
        # Analyze all services
        analyses = self.analyze_all_services()
        
        print("Building service network...")
        service_network = self.build_service_network(analyses)
        
        print("Generating reports...")
        self.generate_reports(analyses, service_network)
        
        # Save raw analysis
        with open('raw_analysis.json', 'w') as f:
            json.dump(analyses, f, indent=2)
        
        print("\nAnalysis complete! Generated files:")
        print("1. comprehensive_analysis.xlsx - Detailed analysis and statistics")
        print("2. service_network.png - Visual representation of service relationships")
        print("3. service_network.gexf - Network data for further analysis")
        print("4. raw_analysis.json - Raw analysis data")
        
        self.conn.close()

def main():
    analyzer = ComprehensiveAnalyzer()
    analyzer.run_analysis()

if __name__ == "__main__":
    main()
