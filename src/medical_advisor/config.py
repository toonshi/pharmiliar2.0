"""Configuration module for the Medical Advisor system."""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DB_DIR = PROJECT_ROOT / "db"
REPORTS_DIR = PROJECT_ROOT / "reports"

# Create necessary directories
DB_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# Environment variables
ENV_PATH = CONFIG_DIR / ".env"

# OpenAI configuration
OPENAI_MODEL = "gpt-3.5-turbo"
EMBEDDING_MODEL = "text-embedding-ada-002"

# Database configuration
CHROMA_COLLECTION = "medical_services_v2"
MAX_RESULTS = 10
