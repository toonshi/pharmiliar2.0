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
import time
import numpy as np

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class RobustServiceMapper:
    def __init__(self):
        self.conn = sqlite3.connect('pharmiliar.db')
        self.G = nx.DiGraph()
        self.batch_size = 10
        self.cache_file = 'analysis_cache.json'
        
    def load_cache(self):
        """Load previously analyzed services"""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        return {}

    def save_cache(self, cache):
        """Save analyzed services to cache"""
        with open(self.cache_file, 'w') as f:
            json.dump(cache, f, indent=2)

    def clean_department_name(self, dept):
        """Clean department names for consistency"""
        if not dept:
            return "Unknown"
        # Remove special characters and normalize
        dept = dept.replace('/', '_').replace('.', '_').strip()
        return dept or "Unknown"

    def analyze_services_batch(self, services):
        """Analyze a batch of services with robust error handling"""
        services_text = "\n".join([
            f"Service {i+1}:\nCode: {s['code']}\nDescription: {s['description']}\nPrice: KES {s['base_price']}"
            for i, s in enumerate(services)
        ])
        
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a medical service analyzer. Return ONLY a valid JSON array."},
                    {"role": "user", "content": f"""
                    Analyze these medical services and return a JSON array.
                    Each object MUST have EXACTLY these fields:
                    {{
                        "service_code": "<code>",
                        "department": "<department>",
                        "service_type": "<type>",
                        "description": "<description>",
                        "related_codes": []
                    }}

                    Services to analyze:
                    {services_text}

                    IMPORTANT: Return ONLY the JSON array, no other text.
                    """}
                ],
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean up common JSON formatting issues
            if not content.startswith('['):
                content = '[' + content
            if not content.endswith(']'):
                content = content + ']'
            
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                print(f"JSON parsing failed: {str(e)}")
                return self.create_basic_analysis(services)
                
        except Exception as e:
            print(f"API call failed: {str(e)}")
            return self.create_basic_analysis(services)

    def create_basic_analysis(self, services):
        """Create basic analysis when GPT-4 fails"""
        return [{
            "service_code": s["code"],
            "department": self.clean_department_name(s["description"].split()[0]) if s["description"] else "Unknown",
            "service_type": "Standard",
            "description": s["description"] or "No description available",
            "related_codes": []
        } for s in services]

    def process_services(self):
        """Process all services with improved error handling"""
        df = pd.read_sql_query("SELECT * FROM services", self.conn)
        cache = self.load_cache()
        all_analyses = []
        
        # Group by department for more coherent analysis
        df['dept'] = df['description'].apply(lambda x: self.clean_department_name(x.split()[0]) if x else "Unknown")
        grouped = df.groupby('dept')
        
        print(f"Processing {len(df)} services in batches of {self.batch_size}...")
        
        for dept, group in grouped:
            print(f"\nAnalyzing {dept} department ({len(group)} services)...")
            for i in tqdm(range(0, len(group), self.batch_size)):
                batch = group.iloc[i:i+self.batch_size].to_dict('records')
                
                # Use string key instead of tuple
                batch_key = '_'.join(s['code'] if s['code'] is not None else 'UNKNOWN' for s in batch)
                
                if batch_key in cache:
                    print(f"Using cached analysis for batch")
                    all_analyses.extend(cache[batch_key])
                    continue
                
                # Add retries for failed batches
                max_retries = 3
                for retry in range(max_retries):
                    analysis = self.analyze_services_batch(batch)
                    if analysis:
                        cache[batch_key] = analysis
                        all_analyses.extend(analysis)
                        # Save cache after each successful batch
                        self.save_cache(cache)
                        break
                    elif retry < max_retries - 1:
                        print(f"Retry {retry + 1} for batch...")
                        time.sleep(2)
                
                time.sleep(1)  # Rate limiting
        
        return all_analyses

    def build_network(self, analyses):
        """Build network from analyses"""
        print("Building network...")
        for analysis in analyses:
            # Add node
            self.G.add_node(
                analysis['service_code'],
                department=analysis['department'],
                service_type=analysis['service_type'],
                description=analysis['description']
            )
            
            # Add edges for related services
            for related in analysis['related_codes']:
                self.G.add_edge(
                    analysis['service_code'],
                    related,
                    relationship='related'
                )

    def generate_outputs(self, analyses):
        """Generate analysis outputs"""
        print("Generating outputs...")
        
        # Save complete analysis
        with open('service_analysis.json', 'w') as f:
            json.dump(analyses, f, indent=2)
        
        # Create Excel report
        df_analyses = pd.DataFrame(analyses)
        with pd.ExcelWriter('service_analysis.xlsx') as writer:
            # Main analysis
            df_analyses.to_excel(writer, sheet_name='Services', index=False)
            
            # Department summary
            dept_summary = df_analyses.groupby('department').agg({
                'service_code': 'count',
                'service_type': lambda x: x.value_counts().to_dict()
            }).rename(columns={'service_code': 'total_services'})
            dept_summary.to_excel(writer, sheet_name='Departments')
        
        # Generate network visualization
        plt.figure(figsize=(20, 20))
        pos = nx.spring_layout(self.G)
        
        # Color nodes by department
        departments = nx.get_node_attributes(self.G, 'department')
        unique_depts = list(set(departments.values()))
        colors = plt.cm.tab20(np.linspace(0, 1, len(unique_depts)))
        color_map = dict(zip(unique_depts, colors))
        
        nx.draw(self.G, pos,
               node_color=[color_map[departments[node]] for node in self.G.nodes()],
               with_labels=True,
               node_size=1000,
               font_size=8,
               arrows=True)
        
        plt.title("Service Relationships Network")
        plt.savefig('service_network.png', bbox_inches='tight', dpi=300)
        plt.close()

    def analyze(self):
        """Run complete analysis"""
        print("Starting service analysis...")
        
        analyses = self.process_services()
        
        print("\nBuilding network and generating outputs...")
        self.build_network(analyses)
        self.generate_outputs(analyses)
        
        print("\nAnalysis complete! Files generated:")
        print("1. service_analysis.json - Raw analysis data")
        print("2. service_analysis.xlsx - Structured analysis")
        print("3. service_network.png - Network visualization")
        print(f"4. {self.cache_file} - Analysis cache")
        
        self.conn.close()

if __name__ == "__main__":
    mapper = RobustServiceMapper()
    mapper.analyze()
