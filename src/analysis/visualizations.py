"""Visualization functions for price analysis."""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker
from .base import Department, Service, init_db
import os

def setup_visualization():
    """Set up the visualization environment."""
    plt.style.use('seaborn')
    viz_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                          'visualizations')
    os.makedirs(viz_dir, exist_ok=True)
    return viz_dir

def plot_department_summary():
    """Create price distribution plots by department."""
    viz_dir = setup_visualization()
    engine = init_db()
    Session = sessionmaker(bind=engine)
    
    with Session() as session:
        # Get department averages
        query = session.query(
            Department.name,
            func.avg(Service.normal_rate).label('avg_price')
        ).join(Service)\
         .filter(Service.normal_rate > 0)\
         .group_by(Department.name)
        
        df = pd.DataFrame(query.all(), columns=['Department', 'Average Price'])
        
        plt.figure(figsize=(15, 8))
        plt.bar(df['Department'], df['Average Price'])
        plt.xticks(rotation=45, ha='right')
        plt.title('Average Price by Department')
        plt.xlabel('Department')
        plt.ylabel('Average Price (KSH)')
        
        plt.tight_layout()
        plt.savefig(os.path.join(viz_dir, "department_summary.png"), dpi=300)
        plt.close()

def plot_price_distributions():
    """Create histograms of price distributions."""
    viz_dir = setup_visualization()
    engine = init_db()
    Session = sessionmaker(bind=engine)
    
    with Session() as session:
        query = session.query(
            Service.normal_rate,
            Service.special_rate,
            Service.non_ea_rate
        ).filter(
            Service.normal_rate > 0,
            Service.special_rate > 0,
            Service.non_ea_rate > 0
        )
        
        df = pd.DataFrame(query.all(), 
                         columns=['Normal Rate', 'Special Rate', 'Non-EA Rate'])
        
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        
        for i, col in enumerate(df.columns):
            axes[i].hist(df[col], bins=30)
            axes[i].set_title(f'{col} Distribution')
            axes[i].set_xlabel('Price (KSH)')
            axes[i].set_ylabel('Count')
        
        plt.tight_layout()
        plt.savefig(os.path.join(viz_dir, "price_distributions.png"), dpi=300)
        plt.close()

def plot_price_correlations():
    """Create scatter plots showing correlations between price tiers."""
    viz_dir = setup_visualization()
    engine = init_db()
    Session = sessionmaker(bind=engine)
    
    with Session() as session:
        query = session.query(
            Service.normal_rate,
            Service.special_rate,
            Service.non_ea_rate
        ).filter(
            Service.normal_rate > 0,
            Service.special_rate > 0,
            Service.non_ea_rate > 0
        )
        
        df = pd.DataFrame(query.all(), 
                         columns=['Normal Rate', 'Special Rate', 'Non-EA Rate'])
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7))
        
        # Normal vs Special Rate
        ax1.scatter(df['Normal Rate'], df['Special Rate'], alpha=0.5)
        max_val = max(df['Normal Rate'].max(), df['Special Rate'].max())
        ax1.plot([0, max_val], [0, max_val], 'r--', alpha=0.7)
        ax1.set_xlabel('Normal Rate (KSH)')
        ax1.set_ylabel('Special Rate (KSH)')
        ax1.set_title('Normal vs Special Rate')
        
        # Normal vs Non-EA Rate
        ax2.scatter(df['Normal Rate'], df['Non-EA Rate'], alpha=0.5)
        max_val = max(df['Normal Rate'].max(), df['Non-EA Rate'].max())
        ax2.plot([0, max_val], [0, max_val], 'r--', alpha=0.7)
        ax2.set_xlabel('Normal Rate (KSH)')
        ax2.set_ylabel('Non-EA Rate (KSH)')
        ax2.set_title('Normal vs Non-EA Rate')
        
        plt.tight_layout()
        plt.savefig(os.path.join(viz_dir, "price_correlations.png"), dpi=300)
        plt.close()

def generate_all_visualizations():
    """Generate all visualization plots."""
    print("Generating visualizations...")
    plot_department_summary()
    print("- Department summary completed")
    plot_price_distributions()
    print("- Price distributions completed")
    plot_price_correlations()
    print("- Price correlations completed")
    print("\nAll visualizations have been saved to the 'visualizations' directory.")
