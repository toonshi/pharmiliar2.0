# Pharmiliar - Medical Services Search

An intelligent medical services search system that helps users find and understand available medical services, their costs, and get AI-powered recommendations.

## Features

- Smart natural language search for medical services
- AI-powered service recommendations
- Price range information
- Support for both Radiology and General services
- Intelligent handling of medical terminology and synonyms

## Components

- `service_mapper_final2.py`: Core service search functionality
- `ai_service_mapper.py`: OpenAI-powered intelligent search
- `search_services.py`: User-friendly command-line interface

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pharmiliar.git
cd pharmiliar
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your environment:
- Create a `.env` file in the project root
- Add your OpenAI API key:
```
OPENAI_API_KEY=your-api-key-here
```

## Usage

Run the interactive search interface:
```bash
python search_services.py
```

Example queries:
- "I need an x-ray for my chest pain"
- "Looking for a general consultation"
- "Need an ultrasound for pregnancy"
- "What kind of scan for a head injury?"

## Database Schema

The system uses SQLite with the following main table:

```sql
CREATE TABLE services (
    description TEXT,
    category TEXT,
    code TEXT,
    base_price REAL,
    max_price REAL
);
```

## Contributing

Feel free to submit issues and enhancement requests!
