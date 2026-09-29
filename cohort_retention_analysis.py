"""
Cohort Retention Analysis for Online Retail II Dataset
Task 22: Cohort Retention Basics
Data Analytics Track - Veda Technology Internship
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import sqlite3

# Set style for better visualizations
sns.set(style="whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

def load_data():
    """
    Load the Online Retail II dataset
    For this example, we'll create a sample dataset similar to Online Retail II
    """
    print("Loading dataset...")
    
    # Create sample data similar to Online Retail II structure
    np.random.seed(42)
    
    # Generate 1000 customers over 12 months
    n_customers = 1000
    start_date = datetime(2019, 1, 1)
    
    data = []
    for i in range(n_customers):
        # Random signup month
        signup_month = np.random.randint(0, 12)
        signup_date = start_date + pd.DateOffset(months=signup_month)
        
        # Random number of purchases (1-20)
        n_purchases = np.random.randint(1, 21)
        
        for j in range(n_purchases):
            # Purchase date (within 12 months of signup)
            months_after_signup = np.random.randint(0, 12)
            purchase_date = signup_date + pd.DateOffset(months=months_after_signup)
            
            # Random purchase amount
            amount = np.random.uniform(10, 500)
            
            data.append({
                'CustomerID': f'C{i:04d}',
                'InvoiceDate': purchase_date,
                'InvoiceNo': f'INV{len(data):06d}',
                'Quantity': np.random.randint(1, 10),
                'UnitPrice': round(amount / np.random.randint(1, 10), 2),
                'Country': np.random.choice(['UK', 'Germany', 'France', 'Spain', 'Italy'])
            })
    
    df = pd.DataFrame(data)
    print(f"Dataset loaded: {len(df)} transactions for {df['CustomerID'].nunique()} customers")
    return df

def create_cohort_table(df):
    """
    Create cohort retention table by signup month
    """
    print("\nCreating cohort table...")
    
    # Extract invoice year and month
    df['InvoiceYearMonth'] = df['InvoiceDate'].dt.to_period('M')
    
    # Determine each customer's cohort (first purchase month)
    df['CohortMonth'] = df.groupby('CustomerID')['InvoiceYearMonth'].transform('min')
    
    # Calculate the number of months between cohort month and invoice month
    df['CohortIndex'] = (df['InvoiceYearMonth'] - df['CohortMonth']).apply(lambda x: x.n)
    
    # Count unique customers per cohort and cohort index
    cohort_data = df.groupby(['CohortMonth', 'CohortIndex'])['CustomerID'].nunique().reset_index()
    cohort_counts = cohort_data.pivot(index='CohortMonth', columns='CohortIndex', values='CustomerID')
    
    # Calculate cohort sizes (number of customers in each cohort)
    cohort_sizes = cohort_counts.iloc[:, 0]
    
    # Calculate retention rates
    retention = cohort_counts.divide(cohort_sizes, axis=0)
    
    # Convert to percentages
    retention = retention.round(3) * 100
    
    print("Cohort table created successfully")
    return retention, cohort_counts

def create_sql_queries():
    """
    Create SQL queries for cohort retention analysis
    """
    print("\nGenerating SQL queries...")
    
    sql_queries = """
-- SQL Query 1: Determine Customer Cohorts (First Purchase Month)
WITH customer_cohorts AS (
    SELECT 
        CustomerID,
        MIN(DATE(InvoiceDate, 'start of month')) AS cohort_month
    FROM online_retail
    GROUP BY CustomerID
)

-- SQL Query 2: Calculate Cohort Retention
SELECT 
    cc.cohort_month,
    CAST(strftime('%Y', DATE(InvoiceDate, 'start of month')) AS INTEGER) * 12 + 
    CAST(strftime('%m', DATE(InvoiceDate, 'start of month')) AS INTEGER) -
    (CAST(strftime('%Y', cc.cohort_month) AS INTEGER) * 12 + 
     CAST(strftime('%m', cc.cohort_month) AS INTEGER)) AS cohort_index,
    COUNT(DISTINCT o.CustomerID) AS customer_count
FROM online_retail o
JOIN customer_cohorts cc ON o.CustomerID = cc.CustomerID
GROUP BY cc.cohort_month, cohort_index
ORDER BY cc.cohort_month, cohort_index;

-- SQL Query 3: Calculate Retention Rates
WITH cohort_counts AS (
    SELECT 
        cohort_month,
        cohort_index,
        customer_count,
        FIRST_VALUE(customer_count) OVER (PARTITION BY cohort_month ORDER BY cohort_index) AS cohort_size
    FROM (
        SELECT 
            cc.cohort_month,
            CAST(strftime('%Y', DATE(InvoiceDate, 'start of month')) AS INTEGER) * 12 + 
            CAST(strftime('%m', DATE(InvoiceDate, 'start of month')) AS INTEGER) -
            (CAST(strftime('%Y', cc.cohort_month) AS INTEGER) * 12 + 
             CAST(strftime('%m', cc.cohort_month) AS INTEGER)) AS cohort_index,
            COUNT(DISTINCT o.CustomerID) AS customer_count
        FROM online_retail o
        JOIN customer_cohorts cc ON o.CustomerID = cc.CustomerID
        GROUP BY cc.cohort_month, cohort_index
    )
)
SELECT 
    cohort_month,
    cohort_index,
    cohort_size,
    customer_count,
    ROUND((customer_count * 100.0 / cohort_size), 2) AS retention_rate
FROM cohort_counts
ORDER BY cohort_month, cohort_index;
"""
    
    # Save SQL queries to file
    with open('cohort_queries.sql', 'w') as f:
        f.write(sql_queries)
    
    print("SQL queries saved to cohort_queries.sql")
    return sql_queries

def visualize_retention(retention):
    """
    Create heatmap visualization of cohort retention
    """
    print("\nGenerating retention heatmap...")
    
    plt.figure(figsize=(14, 8))
    
    # Create heatmap
    sns.heatmap(
        retention,
        annot=True,
        fmt='.1f',
        cmap='YlOrRd',
        vmin=0,
        vmax=100,
        cbar_kws={'label': 'Retention Rate (%)'}
    )
    
    plt.title('Cohort Retention Analysis - Customer Retention by Signup Month', fontsize=16, fontweight='bold')
    plt.xlabel('Months Since Signup', fontsize=12)
    plt.ylabel('Cohort (Signup Month)', fontsize=12)
    plt.tight_layout()
    
    plt.savefig('cohort_retention_heatmap.png', dpi=300, bbox_inches='tight')
    print("Heatmap saved as cohort_retention_heatmap.png")
    plt.show()

def analyze_insights(retention):
    """
    Generate insights from cohort retention data
    """
    print("\n" + "="*60)
    print("COHORT RETENTION INSIGHTS")
    print("="*60)
    
    insights = []
    
    # Average retention across all cohorts
    avg_retention = retention.mean(axis=0)
    insights.append(f"Average retention across all cohorts:")
    for month_idx, rate in avg_retention.items():
        if month_idx == 0:
            insights.append(f"  Month 0 (signup month): {rate:.1f}%")
        else:
            insights.append(f"  Month {month_idx}: {rate:.1f}%")
    
    # Best performing cohort
    cohort_performance = retention.mean(axis=1)
    best_cohort = cohort_performance.idxmax()
    insights.append(f"\nBest performing cohort: {best_cohort} (avg retention: {cohort_performance.max():.1f}%)")
    
    # Worst performing cohort
    worst_cohort = cohort_performance.idxmin()
    insights.append(f"Worst performing cohort: {worst_cohort} (avg retention: {cohort_performance.min():.1f}%)")
    
    # Retention decay
    if len(avg_retention) > 1:
        month1_retention = avg_retention.iloc[1] if len(avg_retention) > 1 else 0
        month0_retention = avg_retention.iloc[0]
        decay = month0_retention - month1_retention
        insights.append(f"\nRetention decay from month 0 to month 1: {decay:.1f} percentage points")
    
    # Long-term retention
    if len(avg_retention) >= 6:
        month6_retention = avg_retention.iloc[6]
        insights.append(f"6-month retention rate: {month6_retention:.1f}%")
    
    for insight in insights:
        print(insight)
    
    return insights

def save_results(retention, insights):
    """
    Save results to CSV and text files
    """
    print("\nSaving results...")
    
    # Save cohort table to CSV
    retention.to_csv('cohort_retention_table.csv')
    print("Cohort table saved to cohort_retention_table.csv")
    
    # Save insights to text file
    with open('cohort_insights.txt', 'w') as f:
        f.write("COHORT RETENTION ANALYSIS INSIGHTS\n")
        f.write("="*60 + "\n\n")
        for insight in insights:
            f.write(insight + "\n")
    print("Insights saved to cohort_insights.txt")

def main():
    """
    Main execution function
    """
    print("="*60)
    print("COHORT RETENTION ANALYSIS - TASK 22")
    print("Data Analytics Track - Veda Technology Internship")
    print("="*60)
    
    # Load data
    df = load_data()
    
    # Create cohort table
    retention, cohort_counts = create_cohort_table(df)
    
    # Display cohort table
    print("\nCohort Retention Table:")
    print(retention)
    
    # Create SQL queries
    sql_queries = create_sql_queries()
    
    # Visualize retention
    visualize_retention(retention)
    
    # Analyze insights
    insights = analyze_insights(retention)
    
    # Save results
    save_results(retention, insights)
    
    print("\n" + "="*60)
    print("ANALYSIS COMPLETE!")
    print("="*60)
    print("\nGenerated files:")
    print("  - cohort_retention_table.csv")
    print("  - cohort_retention_heatmap.png")
    print("  - cohort_insights.txt")
    print("  - cohort_queries.sql")
    print("\nWhat is a cohort?")
    print("  A cohort is a group of users who share a common characteristic")
    print("  or experience within a defined time period. In this analysis,")
    print("  cohorts are defined by the month of their first purchase.")
    print("\nWhy is cohort retention useful?")
    print("  - It helps understand customer behavior patterns over time")
    print("  - It identifies which cohorts have better long-term retention")
    print("  - It measures the effectiveness of customer acquisition strategies")
    print("  - It informs product and marketing decisions to improve retention")
    print("  - It provides insights into customer lifetime value")

if __name__ == "__main__":
    main()
