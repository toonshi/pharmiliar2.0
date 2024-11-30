import os
from dotenv import load_dotenv
from openai import OpenAI
import json
import sqlite3
import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use('Agg')  # Use Agg backend instead of Tk
import matplotlib.pyplot as plt
from tqdm import tqdm

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class ServiceMapper:
    def __init__(self):
        self.conn = sqlite3.connect('pharmiliar.db')
        self.G = nx.DiGraph()
        
    def get_service_context(self, service_batch):
        """Ask GPT-4 to analyze how services are related in medical context"""
        services_text = "\n".join([
            f"Service {i+1}:\nCode: {s['code']}\nDescription: {s['description']}\nPrice: KES {s['base_price']}"
            for i, s in enumerate(service_batch)
        ])
        
        prompt = f"""
        Analyze these medical services and explain how they are related in a clinical context:
        {services_text}

        For each service, explain:
        1. What medical conditions typically require this service
        2. What other services usually precede this service
        3. What services typically follow this service
        4. What services are usually ordered together with this service
        5. What department typically orders this service

        Provide the response as a JSON array where each object has:
        {{
            "service_code": "code",
            "conditions": ["condition1", "condition2"],
            "preceding_services": ["service1", "service2"],
            "following_services": ["service1", "service2"],
            "concurrent_services": ["service1", "service2"],
            "ordering_department": "department",
            "clinical_pathway": "description of where this fits in treatment"
        }}
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a medical service analyzer with expertise in clinical pathways and treatment protocols."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error in context analysis: {str(e)}")
            return None

    def build_service_relationships(self):
        """Build network of service relationships"""
        query = "SELECT * FROM services"
        df = pd.read_sql_query(query, self.conn)
        
        batch_size = 5
        all_relationships = []
        
        print(f"Analyzing {len(df)} services in batches of {batch_size}...")
        for i in tqdm(range(0, len(df), batch_size)):
            batch = df.iloc[i:i+batch_size].to_dict('records')
            relationships = self.get_service_context(batch)
            if relationships:
                all_relationships.extend(relationships)
        
        return all_relationships

    def create_network(self, relationships):
        """Create network graph from relationships"""
        for rel in relationships:
            self.G.add_node(rel['service_code'], 
                           conditions=rel['conditions'],
                           department=rel['ordering_department'],
                           pathway=rel['clinical_pathway'])
            
            for prev in rel['preceding_services']:
                self.G.add_edge(prev, rel['service_code'], 
                              relationship_type='precedes')
            
            for next_service in rel['following_services']:
                self.G.add_edge(rel['service_code'], next_service,
                              relationship_type='follows')
            
            for concurrent in rel['concurrent_services']:
                self.G.add_edge(rel['service_code'], concurrent,
                              relationship_type='concurrent')
    
    def find_treatment_paths(self):
        """Find common treatment pathways in the network"""
        paths = []
        for source in self.G.nodes():
            for target in self.G.nodes():
                if source != target:
                    try:
                        paths.extend(list(nx.all_simple_paths(self.G, source, target, cutoff=3)))
                    except:
                        continue
        return paths

    def generate_visualizations(self):
        """Generate network visualizations"""
        plt.figure(figsize=(20, 20))
        pos = nx.spring_layout(self.G)
        
        nx.draw_networkx_nodes(self.G, pos, node_size=1000, 
                             node_color='lightblue')
        
        edge_colors = {'precedes': 'blue', 'follows': 'green', 
                      'concurrent': 'red'}
        
        for edge_type, color in edge_colors.items():
            edge_list = [(u, v) for (u, v, d) in self.G.edges(data=True) 
                        if d['relationship_type'] == edge_type]
            nx.draw_networkx_edges(self.G, pos, edgelist=edge_list, 
                                 edge_color=color, arrows=True)
        
        nx.draw_networkx_labels(self.G, pos, font_size=8)
        
        plt.title("Medical Service Relationships Network")
        plt.savefig('service_network_detailed.png', bbox_inches='tight')
        plt.close()

    def generate_reports(self):
        """Generate analysis reports"""
        paths = self.find_treatment_paths()
        
        nodes_df = pd.DataFrame.from_dict(dict(self.G.nodes(data=True)), 
                                        orient='index')
        
        edges_df = pd.DataFrame([(u, v, d['relationship_type']) 
                               for u, v, d in self.G.edges(data=True)],
                              columns=['Service1', 'Service2', 'Relationship'])
        
        with pd.ExcelWriter('service_relationships.xlsx') as writer:
            nodes_df.to_excel(writer, sheet_name='Services')
            edges_df.to_excel(writer, sheet_name='Relationships')
            if paths:
                pd.DataFrame(paths, columns=[f'Step_{i+1}' for i in range(max(len(p) for p in paths))])\
                    .to_excel(writer, sheet_name='Treatment_Paths')

    def analyze(self):
        """Run complete analysis"""
        print("Starting service relationship analysis...")
        relationships = self.build_service_relationships()
        
        print("Creating network graph...")
        self.create_network(relationships)
        
        print("Generating visualizations...")
        self.generate_visualizations()
        
        print("Creating reports...")
        self.generate_reports()
        
        with open('service_relationships.json', 'w') as f:
            json.dump(relationships, f, indent=2)
        
        print("\nAnalysis complete! Generated files:")
        print("1. service_network_detailed.png - Visual map of service relationships")
        print("2. service_relationships.xlsx - Detailed analysis of relationships")
        print("3. service_relationships.json - Raw relationship data")
        
        self.conn.close()

if __name__ == "__main__":
    mapper = ServiceMapper()
    mapper.analyze()
