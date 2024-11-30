# pharmiliar

An AI-powered medical advisory system that helps users understand their medical conditions, get personalized recommendations, and find appropriate healthcare services in Kenya.

## Features

- Interactive medical consultation through natural language
- Personalized medical assessment based on symptoms
- Cost-aware treatment plans (Standard, Budget, and Comprehensive)
- Integration with Kenyan healthcare facilities and services
- Automated report generation and storage
- Vector database for intelligent symptom matching
- Price information for medical services

## Technology Stack

- Python 3.8+
- OpenAI GPT-3.5 for medical analysis
- ChromaDB for vector similarity search
- SQLite for medical services database

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
- Create a `config` directory and add a `.env` file
- Add your OpenAI API key:
```
OPENAI_API_KEY=your-api-key-here
```

## Usage

Run the medical advisor:
```bash
python src/kenya_medical_advisor.py
```

The system will:
1. Ask for your name and location
2. Listen to your medical concern
3. Ask relevant follow-up questions
4. Generate a comprehensive assessment including:
   - Risk level evaluation
   - Immediate steps required
   - Recommended tests
   - Warning signs to watch for
   - Specialist recommendations
5. Provide three treatment plans:
   - Standard Plan
   - Budget Plan (cost-saving options)
   - Comprehensive Plan (full coverage)
6. Save detailed reports in both JSON and TXT formats

## Project Structure

```
pharmiliar/
├── config/
│   └── .env              # Environment variables
├── db/
│   ├── chroma.sqlite3    # Vector database for medical knowledge
│   └── ...              # ChromaDB files
├── reports/              # Generated medical reports
├── src/
│   ├── kenya_medical_advisor.py  # Main application
│   ├── data_enrichment.py        # Service data processing
│   └── cost_estimator.py         # Price estimation
└── requirements.txt      # Python dependencies
```

## Database Schema

The system uses two databases:

1. ChromaDB (Vector Database):
- Stores medical knowledge embeddings
- Enables semantic search for conditions
- Matches symptoms to potential causes

2. SQLite (Service Database):
```sql
CREATE TABLE services (
    description TEXT,
    category TEXT,
    base_price REAL,
    metadata JSON
);
```

## Contributing

Contributions are welcome! Please feel free to submit issues and enhancement requests.

## License

[Your chosen license]

## Disclaimer

This system is designed to provide general medical information and guidance only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition.
