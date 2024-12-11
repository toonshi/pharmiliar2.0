"""Service management for medical advisor system."""

import sqlite3
import pandas as pd
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions

class ServiceManager:
    def __init__(self, api_key: str):
        """Initialize service manager."""
        self.project_root = Path(__file__).parent.parent.parent
        self.db_dir = self.project_root / "db"
        self.db_dir.mkdir(exist_ok=True)
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=str(self.db_dir))
        self.embedding_func = embedding_functions.OpenAIEmbeddingFunction(
            api_key=api_key,
            model_name="text-embedding-ada-002"
        )
    
    def _reset_collection(self, name: str):
        """Reset a collection by deleting and recreating it."""
        try:
            # Delete if exists
            self.chroma_client.delete_collection(name)
            print(f"Deleted existing collection: {name}")
        except ValueError:
            print(f"Note: Collection {name} doesn't exist yet")
        
        # Create new collection
        collection = self.chroma_client.create_collection(
            name=name,
            embedding_function=self.embedding_func
        )
        print(f"Created new collection: {name}")
        return collection
    
    def load_services(self):
        """Load services from SQLite to ChromaDB."""
        # Get SQLite database path
        db_path = self.project_root / "data" / "processed" / "hospital_services.db"
        
        if not db_path.exists():
            raise FileNotFoundError(f"Database not found at {db_path}")
        
        # Connect to SQLite
        print(f"Connecting to SQLite database at {db_path}")
        conn = sqlite3.connect(str(db_path))
        
        try:
            # Load services with department info
            print("Loading services from SQLite...")
            services_df = pd.read_sql("""
                SELECT 
                    s.id, s.code, s.description, s.normal_rate,
                    d.name as department_name
                FROM services s
                JOIN departments d ON s.department_id = d.id
                WHERE s.normal_rate > 0
                ORDER BY s.normal_rate DESC
            """, conn)
            
            print(f"Found {len(services_df)} services")
            
            # Create fresh collection
            print("\nResetting ChromaDB collection...")
            collection = self._reset_collection("medical_services")
            
            # Prepare data for ChromaDB
            documents = []
            metadatas = []
            ids = []
            
            print("Preparing services for ChromaDB...")
            for _, service in services_df.iterrows():
                # Create rich service description
                service_desc = (
                    f"Medical service: {service.description}\n"
                    f"Department: {service.department_name}\n"
                    f"Service code: {service.code}\n"
                    f"Price: KSH {service.normal_rate:.2f}"
                )
                
                # Create metadata
                metadata = {
                    "service_id": str(service.id),
                    "code": service.code,
                    "department": service.department_name,
                    "price": float(service.normal_rate)
                }
                
                documents.append(service_desc)
                metadatas.append(metadata)
                ids.append(f"service_{service.id}")
            
            # Add services in batches
            batch_size = 100
            total_batches = (len(documents) + batch_size - 1) // batch_size
            
            print(f"Adding services in {total_batches} batches...")
            for i in range(0, len(documents), batch_size):
                batch_end = min(i + batch_size, len(documents))
                batch_num = (i // batch_size) + 1
                
                print(f"Adding batch {batch_num}/{total_batches} (services {i+1} to {batch_end})")
                collection.add(
                    documents=documents[i:batch_end],
                    metadatas=metadatas[i:batch_end],
                    ids=ids[i:batch_end]
                )
            
            print(f"\nSuccessfully loaded {len(documents)} services into ChromaDB")
            print(f"Collection now has {collection.count()} services")
            return collection.count()
            
        finally:
            conn.close()
    
    def get_collection(self):
        """Get the medical services collection."""
        try:
            return self.chroma_client.get_collection(
                name="medical_services",
                embedding_function=self.embedding_func
            )
        except ValueError:
            return None
