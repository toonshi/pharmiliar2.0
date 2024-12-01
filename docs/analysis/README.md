# Hospital Price Analysis Documentation

## Overview

This documentation covers the Hospital Price Analysis package, which provides tools for analyzing and visualizing hospital service pricing data. The package handles three main price tiers:

- Normal Rate (E.A.)
- Special Rate (Private)
- Non-E.A. Rate

## Table of Contents

1. [Getting Started](getting_started.md)
2. [Data Models](data_models.md)
3. [Data Processing](data_processing.md)
4. [Visualizations](visualizations.md)
5. [Price Analysis](price_analysis.md)
6. [Anomaly Detection](anomaly_detection.md)

## Quick Start

```python
# Import required modules
from analysis.base import init_db
from analysis.data_processing import migrate_data
from analysis.visualizations import generate_all_visualizations
from analysis.anomalies import analyze_price_anomalies

# Initialize database
engine = init_db()

# Migrate data from Excel
migrate_data('path/to/excel/file.xlsx')

# Generate visualizations
generate_all_visualizations()

# Analyze price anomalies
anomalies = analyze_price_anomalies()
```

## Package Structure

```
src/analysis/
├── __init__.py          # Package initialization
├── base.py              # Database models and setup
├── data_processing.py   # Data cleaning and migration
├── visualizations.py    # Visualization functions
└── anomalies.py         # Anomaly detection
```

## Key Features

1. **Data Management**
   - Excel data import
   - Data cleaning and validation
   - SQLite database storage

2. **Price Analysis**
   - Department-wise analysis
   - Price tier comparisons
   - Service variant tracking

3. **Visualizations**
   - Price distributions
   - Department comparisons
   - Price correlations

4. **Anomaly Detection**
   - Unusual price patterns
   - Data entry error detection
   - Price consistency checks

## Contributing

To contribute to this package:

1. Follow the code organization structure
2. Add documentation for new features
3. Include unit tests for new functionality
4. Update relevant documentation files

## License

This package is for internal use only. All rights reserved.
