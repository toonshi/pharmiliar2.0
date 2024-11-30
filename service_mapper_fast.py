import os
from dotenv import load_dotenv
from openai import OpenAI
import json
import sqlite3
import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tqdm import tqdm
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from functools import partial

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class FastServiceMapper:
    def __init__(self):
        self.conn = sqlite3.connect('pharmiliar.db')
        self.G = nx.DiGraph()
        self.batch_size = 20  # Increased batch size
        
    def analyze_services_batch(self, services):
        """Analyze a larger batch of services at once"""
        services_text = "\n".join([
            f"Service {i+1}:\nCode: {s['code']}\nDescription: {s['description']}\nPrice: KES {s['base_price']}"
            for i, s in enumerate(services)
        ])
        
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a medical service analyzer. Analyze these services and their relationships efficiently."},
                    {"role": "user", "content": f"""
                    Analyze these medical services and their relationships:
                    {services_text}

                    For each service, provide a JSON object with:
                    - service_code: The service code
                    - department: Medical department
                    - related_services: List of related service codes
                    - typical_pathway: Common treatment sequence
                    
                    Format as a JSON array of objects, keeping responses concise.
                    """}
                ],
                temperature=0.3
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error in batch analysis: {str(e)}")
            return None

    def process_services(self):
        """Process all services with optimized batching"""
        # Get all services
        df = pd.read_sql_query("SELECT * FROM services", self.conn)
        all_analyses = []
        
        # Process in larger batches
        print(f"Processing {len(df)} services in batches of {self.batch_size}...")
        for i in tqdm(range(0, len(df), self.batch_size)):
            batch = df.iloc[i:i+self.batch_size].to_dict('records')
            analysis = self.analyze_services_batch(batch)
            if analysis:
                all_analyses.extend(analysis)
        
        return all_analyses

    def build_network(self, analyses):
        """Build network from analyses"""
        print("Building network...")
        for analysis in analyses:
            self.G.add_node(
                analysis['service_code'],
                department=analysis.get('department', ''),
                pathway=analysis.get('typical_pathway', '')
            )
            
            # Add relationships
            for related in analysis.get('related_services', []):
                self.G.add_edge(
                    analysis['service_code'],
                    related,
                    relationship='related'
                )

    def generate_outputs(self, analyses):
        """Generate all outputs efficiently"""
        print("Generating outputs...")
        
        # Save raw data
        with open('service_analysis.json', 'w') as f:
            json.dump(analyses, f, indent=2)
        
        # Create Excel report
        df_analyses = pd.DataFrame(analyses)
        with pd.ExcelWriter('service_analysis.xlsx') as writer:
            df_analyses.to_excel(writer, sheet_name='Services', index=False)
            
            # Department summary
            dept_summary = df_analyses.groupby('department').size()
            dept_summary.to_excel(writer, sheet_name='Departments')
        
        # Generate network visualization
        plt.figure(figsize=(20, 20))
        pos = nx.spring_layout(self.G)
        nx.draw(self.G, pos, with_labels=True, node_color='lightblue',
               node_size=1000, font_size=8, arrows=True)
        plt.savefig('service_network.png', bbox_inches='tight')
        plt.close()

    def analyze(self):
        """Run optimized analysis"""
        print("Starting fast service analysis...")
        
        # Process all services
        analyses = self.process_services()
        
        # Build network
        self.build_network(analyses)
        
        # Generate outputs
        self.generate_outputs(analyses)
        
        print("\nAnalysis complete! Files generated:")
        print("1. service_analysis.json - Raw analysis data")
        print("2. service_analysis.xlsx - Structured analysis")
        print("3. service_network.png - Network visualization")
        
        self.conn.close()

if __name__ == "__main__":
    mapper = FastServiceMapper()
    mapper.analyze()
