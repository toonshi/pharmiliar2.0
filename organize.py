import os
import shutil

# Create directories
dirs = ['src', 'data', 'data/raw', 'data/processed', 'config']
for d in dirs:
    os.makedirs(d, exist_ok=True)

# Define file mappings
moves = {
    # Source files
    'openai_service_mapper_v2.py': 'src/service_mapper.py',
    'openai_search_services_v2.py': 'src/search_services.py',
    'data_cleaning.py': 'src/data_cleaning.py',
    'data_enrichment.py': 'src/data_enrichment.py',
    'data_analysis.py': 'src/data_analysis.py',
    
    # Data files
    'cleaned_data.xlsx': 'data/processed/cleaned_data.xlsx',
    'extracted_data.xlsx': 'data/raw/extracted_data.xlsx',
    
    # Config files
    '.env': 'config/.env',
    'requirements.txt': 'requirements.txt',
    '.gitignore': '.gitignore',
    'README.md': 'README.md'
}

# Move files to new locations
for src, dst in moves.items():
    if os.path.exists(src):
        # Create destination directory if it doesn't exist
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(src, dst)
        print(f"Moved {src} to {dst}")
    else:
        print(f"Warning: {src} not found")

# Move db directory if it exists
if os.path.exists('db'):
    if os.path.exists('data/processed/db'):
        shutil.rmtree('data/processed/db')
    shutil.move('db', 'data/processed/db')
    print("Moved db directory to data/processed/db")

# Create a new .gitignore if it doesn't exist
gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environment
.env
.venv
venv/
ENV/

# IDEs
.idea/
.vscode/
*.swp
*.swo

# Project specific
data/processed/db/
*.log
"""

with open('.gitignore', 'w') as f:
    f.write(gitignore_content)
print("Updated .gitignore")

# Update README.md with new structure
readme_content = """# Medical Services Search System

An intelligent search system for medical services using OpenAI embeddings and ChromaDB for vector search.

## Project Structure

```
├── config/             # Configuration files
│   └── .env           # Environment variables
├── data/              # Data files
│   ├── processed/     # Cleaned and processed data
│   │   ├── db/       # Vector database
│   │   └── *.xlsx    # Processed Excel files
│   └── raw/          # Raw data files
├── src/               # Source code
│   ├── service_mapper.py    # Core service mapping logic
│   ├── search_services.py   # Search interface
│   ├── data_cleaning.py     # Data cleaning utilities
│   ├── data_enrichment.py   # Data enrichment logic
│   └── data_analysis.py     # Analysis and visualization
├── .gitignore         # Git ignore rules
└── requirements.txt   # Python dependencies
```

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment:
   - Copy `config/.env.example` to `config/.env`
   - Add your OpenAI API key to `config/.env`

## Usage

1. Run the search interface:
   ```bash
   python src/search_services.py
   ```

2. Process new data:
   ```bash
   python src/data_cleaning.py
   python src/data_enrichment.py
   python src/data_analysis.py
   ```

## Features

- AI-powered service matching
- Accurate cost estimates
- Personalized recommendations
- Priority-based care plans
- Comprehensive medical service database
"""

with open('README.md', 'w') as f:
    f.write(readme_content)
print("Updated README.md")

# Remove old files
files_to_remove = [
    f for f in os.listdir('.')
    if f.endswith('.py') 
    and f not in ['organize.py']
    and not f.startswith('__')
    and os.path.isfile(f)
]

for f in files_to_remove:
    os.remove(f)
    print(f"Removed old file: {f}")

print("\nOrganization complete! New structure is ready.")
