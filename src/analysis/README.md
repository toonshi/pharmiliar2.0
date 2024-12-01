# Hospital Price Analysis Package

This package provides tools for analyzing and visualizing hospital pricing data.

## Structure

- `base.py`: Core data models and database setup
- `data_processing.py`: Data cleaning and transformation functions
- `visualizations.py`: Price visualization and charting tools
- `anomalies.py`: Price anomaly detection and analysis

## Usage

1. Initialize the database:
```python
from analysis.base import init_db
engine = init_db()
```

2. Process and migrate data:
```python
from analysis.data_processing import migrate_data
migrate_data('path/to/excel/file.xlsx')
```

3. Generate visualizations:
```python
from analysis.visualizations import generate_all_visualizations
generate_all_visualizations()
```

4. Analyze price anomalies:
```python
from analysis.anomalies import analyze_price_anomalies, print_anomaly_report
anomalies = analyze_price_anomalies()
print_anomaly_report(anomalies)
```

## Visualization Types

1. Department Summary
   - Average prices by department
   - Service count distribution

2. Price Distributions
   - Normal Rate distribution
   - Special Rate distribution
   - Non-EA Rate distribution

3. Price Correlations
   - Normal vs Special Rate
   - Normal vs Non-EA Rate

## Anomaly Detection

The package can identify several types of pricing anomalies:

1. Fixed Non-EA Rates
   - Services with 5 KSH Non-EA rate
   - Common Non-EA rate patterns

2. Price Differences
   - Large differences between rate types
   - Department-wise price variations

3. Service Patterns
   - Price patterns in similar services
   - Unusual pricing for service types

4. Data Entry Errors
   - Extremely large price differences
   - Unusually low prices for complex procedures
