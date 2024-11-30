import os
import json
import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict, Tuple
import openai
from dotenv import load_dotenv

class OpenAIServiceMapper:
    def __init__(self, api_key: str, persist_directory: str = "db"):
        """Initialize the service mapper with ChromaDB and OpenAI embeddings."""
        self.api_key = api_key
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Use OpenAI embeddings
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=api_key,
            model_name="text-embedding-ada-002"
        )
        
        # Create or get collections
        self.services_collection = self.client.get_or_create_collection(
            name="medical_services",
            embedding_function=self.embedding_function
        )
        
        self.analyses_collection = self.client.get_or_create_collection(
            name="query_analyses",
            embedding_function=self.embedding_function
        )
        
        # Load initial services if collection is empty
        if self.services_collection.count() == 0:
            self._load_initial_services()

    def _load_initial_services(self):
        """Load initial medical services into the vector database."""
        services = [
            {
                "id": "XR1020",
                "description": "Chest X-ray",
                "category": "RADIOLOGY",
                "base_price": 500.00,
                "keywords": "lung chest thorax xray radiograph screening cancer respiratory"
            },
            {
                "id": "XR00104",
                "description": "CT Scan Chest",
                "category": "RADIOLOGY",
                "base_price": 5000.00,
                "keywords": "lung chest thorax ct scan screening cancer detailed comprehensive"
            },
            {
                "id": "AC001",
                "description": "Consultation Adult",
                "category": "GENERAL",
                "base_price": 150.00,
                "keywords": "consultation checkup screening initial assessment general"
            },
            {
                "id": "XR0056",
                "description": "Chest PA/Lateral Views",
                "category": "RADIOLOGY",
                "base_price": 800.00,
                "keywords": "chest xray lung screening multiple views comprehensive"
            }
        ]
        
        # Add services to ChromaDB
        self.services_collection.add(
            ids=[s["id"] for s in services],
            documents=[f"{s['description']} - {s['category']} - {s['keywords']}" for s in services],
            metadatas=services
        )

    def _analyze_query(self, query: str) -> Dict:
        """Analyze the query using OpenAI."""
        # Check cache first
        similar_queries = self.analyses_collection.query(
            query_texts=[query],
            n_results=1
        )
        
        if similar_queries["distances"][0] and similar_queries["distances"][0][0] < 0.1:
            print("Using cached analysis...")
            return json.loads(similar_queries["documents"][0][0])
        
        # Generate new analysis using OpenAI's new API format
        system_prompt = """You are a medical service advisor. Analyze the query and provide:
        1. Key health concerns
        2. Recommended diagnostic tests
        3. Priority of services (high/medium/low)
        Format as JSON with fields: 'concerns', 'tests', 'priority'"""
        
        client = openai.OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
        )
        
        analysis = response.choices[0].message.content
        
        # Cache the analysis
        self.analyses_collection.add(
            ids=[query[:64]],
            documents=[analysis],
            metadatas=[{"query": query}]
        )
        
        return json.loads(analysis)

    def search(self, query: str) -> Tuple[List[Dict], str]:
        """Search for relevant medical services."""
        # Analyze the query
        analysis = self._analyze_query(query)
        
        # Enhance query with analysis
        enhanced_query = f"{query} {analysis.get('concerns', '')} {analysis.get('tests', '')}"
        
        # Search for services
        results = self.services_collection.query(
            query_texts=[enhanced_query],
            n_results=5
        )
        
        # Process results
        services = []
        for idx, metadata in enumerate(results["metadatas"][0]):
            if metadata:
                service = metadata.copy()
                service["relevance"] = 1 - results["distances"][0][idx]
                services.append(service)
        
        # Sort by relevance and category
        services.sort(key=lambda x: (
            x["category"] != "RADIOLOGY",  # Radiology first for screening
            -x["relevance"],  # Higher relevance first
            x["base_price"]  # Lower price first
        ))
        
        # Generate recommendation
        recommendation = self._generate_recommendation(services, analysis)
        
        return services, recommendation

    def _generate_recommendation(self, services: List[Dict], analysis: Dict) -> str:
        """Generate a personalized recommendation."""
        if not services:
            return "No specific services found matching your needs."
        
        # Group services
        diagnostics = [s for s in services if s["category"] == "RADIOLOGY"]
        consultations = [s for s in services if s["category"] == "GENERAL"]
        
        # Build recommendation
        recommendation = []
        priority = analysis.get("priority", "medium").lower()
        
        # Add consultation recommendation
        if consultations:
            recommendation.append(f"1. Start with a {consultations[0]['description']} (KES {consultations[0]['base_price']:.2f}) "
                               "for initial assessment and medical history review.")
        
        # Add diagnostic recommendations
        if diagnostics:
            if priority == "high":
                recommendation.append("\n2. Given your health concerns, we strongly recommend:")
            else:
                recommendation.append("\n2. Based on the consultation, your doctor may recommend:")
            
            for i, diagnostic in enumerate(diagnostics[:2], 1):
                recommendation.append(f"   {i}. {diagnostic['description']} (KES {diagnostic['base_price']:.2f})")
        
        # Add priority-based note
        if priority == "high":
            recommendation.append("\nNote: Given your symptoms and risk factors, we recommend scheduling")
            recommendation.append("these screenings as soon as possible for early detection and better outcomes.")
        else:
            recommendation.append("\nNote: The actual tests required will be determined during your consultation.")
            recommendation.append("Early screening is important for preventive care and better health outcomes.")
        
        return "\n".join(recommendation)

    def close(self):
        """Close the ChromaDB client."""
        self.client.close()
