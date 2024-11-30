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
from concurrent.futures import ThreadPoolExecutor
import time

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class OptimizedServiceMapper:
    def __init__(self):
        self.conn = sqlite3.connect('pharmiliar.db')
        self.G = nx.DiGraph()
        self.batch_size = 10  # Balanced batch size
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

    def analyze_services_batch(self, services):
        """Analyze a batch of services with full detail"""
        services_text = "\n".join([
            f"Service {i+1}:\nCode: {s['code']}\nDescription: {s['description']}\nPrice: KES {s['base_price']}"
            for i, s in enumerate(services)
        ])
        
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": """You are a medical service analyzer with expertise in clinical pathways and treatment protocols. 
                    Provide detailed, accurate analysis of medical services and their relationships."""},
                    {"role": "user", "content": f"""
                    Analyze these medical services in detail:
                    {services_text}

                    For each service, provide a JSON object with:
                    1. service_code: The service code
                    2. department: Medical department this belongs to
                    3. service_type: Type of service (diagnostic, therapeutic, preventive, etc.)
                    4. description_enriched: Clear, patient-friendly description
                    5. related_services: {{
                        "prerequisites": [services required before this],
                        "concurrent": [services typically done together],
                        "follow_ups": [services typically done after]
                    }}
                    6. medical_context: {{
                        "conditions": [medical conditions requiring this],
                        "symptoms": [symptoms this addresses],
                        "urgency_level": "routine/urgent/emergency"
                    }}
                    7. treatment_pathway: {{
                        "phase": "initial diagnosis/treatment/follow-up",
                        "typical_sequence": [ordered list of treatment steps],
                        "alternative_paths": [alternative treatment options]
                    }}
                    8. patient_preparation: [steps patient needs to take]
                    9. typical_duration: estimated time for service
                    10. complexity_level: "low/medium/high"

                    Ensure accuracy and clinical relevance in the analysis.
                    Format as a JSON array of objects.
                    """}
                ],
                temperature=0.3
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error in batch analysis: {str(e)}")
            return None

    def process_services(self):
        """Process services with caching and error handling"""
        df = pd.read_sql_query("SELECT * FROM services", self.conn)
        cache = self.load_cache()
        all_analyses = []
        
        # Group services by department for more coherent analysis
        df['dept'] = df['description'].apply(lambda x: x.split()[0] if x else 'Unknown')
        grouped = df.groupby('dept')
        
        print(f"Processing {len(df)} services in batches of {self.batch_size}...")
        
        for dept, group in grouped:
            print(f"\nAnalyzing {dept} department...")
            for i in tqdm(range(0, len(group), self.batch_size)):
                batch = group.iloc[i:i+self.batch_size].to_dict('records')
                batch_key = tuple(s['code'] for s in batch)
                
                if batch_key in cache:
                    all_analyses.extend(cache[batch_key])
                    continue
                
                analysis = self.analyze_services_batch(batch)
                if analysis:
                    cache[batch_key] = analysis
                    all_analyses.extend(analysis)
                    # Save cache periodically
                    if len(all_analyses) % 50 == 0:
                        self.save_cache(cache)
                
                # Respect API rate limits
                time.sleep(1)
        
        self.save_cache(cache)
        return all_analyses

    def build_detailed_network(self, analyses):
        """Build rich network with detailed relationships"""
        print("Building detailed network...")
        for analysis in analyses:
            # Add node with full attributes
            self.G.add_node(
                analysis['service_code'],
                **{k: v for k, v in analysis.items() if k != 'related_services'}
            )
            
            # Add relationship edges
            for rel_type, services in analysis['related_services'].items():
                for service in services:
                    self.G.add_edge(
                        analysis['service_code'],
                        service,
                        relationship_type=rel_type
                    )

    def generate_comprehensive_outputs(self, analyses):
        """Generate detailed outputs and visualizations"""
        print("Generating comprehensive outputs...")
        
        # Save full analysis
        with open('detailed_service_analysis.json', 'w') as f:
            json.dump(analyses, f, indent=2)
        
        # Create detailed Excel report
        with pd.ExcelWriter('service_analysis_detailed.xlsx') as writer:
            # Main service analysis
            df_analyses = pd.json_normalize(analyses)
            df_analyses.to_excel(writer, sheet_name='Services', index=False)
            
            # Department analysis
            dept_analysis = df_analyses.groupby('department').agg({
                'service_type': 'value_counts',
                'complexity_level': 'value_counts',
                'medical_context.urgency_level': 'value_counts'
            })
            dept_analysis.to_excel(writer, sheet_name='Department_Analysis')
            
            # Treatment pathways
            pathways = pd.DataFrame([
                {
                    'service': a['service_code'],
                    'pathway': a['treatment_pathway']['phase'],
                    'sequence': str(a['treatment_pathway']['typical_sequence'])
                }
                for a in analyses
            ])
            pathways.to_excel(writer, sheet_name='Treatment_Pathways')
            
            # Service relationships
            relationships = pd.DataFrame([
                {
                    'service': a['service_code'],
                    'prerequisites': str(a['related_services']['prerequisites']),
                    'concurrent': str(a['related_services']['concurrent']),
                    'follow_ups': str(a['related_services']['follow_ups'])
                }
                for a in analyses
            ])
            relationships.to_excel(writer, sheet_name='Service_Relationships')
        
        # Generate network visualization
        plt.figure(figsize=(20, 20))
        pos = nx.spring_layout(self.G)
        
        # Draw nodes by department
        departments = nx.get_node_attributes(self.G, 'department')
        unique_depts = set(departments.values())
        colors = plt.cm.rainbow(np.linspace(0, 1, len(unique_depts)))
        dept_colors = dict(zip(unique_depts, colors))
        
        for dept in unique_depts:
            nodes = [n for n, d in departments.items() if d == dept]
            nx.draw_networkx_nodes(self.G, pos, nodelist=nodes,
                                 node_color=[dept_colors[dept]],
                                 node_size=1000, alpha=0.7,
                                 label=dept)
        
        # Draw edges by relationship type
        edge_colors = {
            'prerequisites': 'blue',
            'concurrent': 'green',
            'follow_ups': 'red'
        }
        
        for rel_type, color in edge_colors.items():
            edges = [(u, v) for (u, v, d) in self.G.edges(data=True)
                    if d['relationship_type'] == rel_type]
            nx.draw_networkx_edges(self.G, pos, edgelist=edges,
                                 edge_color=color, arrows=True,
                                 label=rel_type)
        
        nx.draw_networkx_labels(self.G, pos, font_size=8)
        plt.legend()
        plt.title("Medical Service Relationships Network")
        plt.savefig('service_network_detailed.png', bbox_inches='tight', dpi=300)
        plt.close()

    def analyze(self):
        """Run complete analysis pipeline"""
        print("Starting comprehensive service analysis...")
        
        # Process all services
        analyses = self.process_services()
        
        # Build detailed network
        self.build_detailed_network(analyses)
        
        # Generate comprehensive outputs
        self.generate_comprehensive_outputs(analyses)
        
        print("\nAnalysis complete! Generated files:")
        print("1. detailed_service_analysis.json - Complete analysis data")
        print("2. service_analysis_detailed.xlsx - Multi-sheet detailed analysis")
        print("3. service_network_detailed.png - High-resolution network visualization")
        print("4. analysis_cache.json - Cached analyses for future use")
        
        self.conn.close()

if __name__ == "__main__":
    mapper = OptimizedServiceMapper()
    mapper.analyze()
