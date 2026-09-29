"""
Cohort Retention Analysis using SQL (SQLite)
Task 22: Cohort Retention Basics
Data Analytics Track - Veda Technology Internship

This script performs the entire cohort retention analysis using SQL queries
executed against a SQLite database, demonstrating SQL-based implementation.
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

def load_data_to_db():
    """
    Load data and create SQLite database
    """
    print("Loading dataset and creating SQLite database...")
    
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
                'InvoiceDate': purchase_date.strftime('%Y-%m-%d'),
                'InvoiceNo': f'INV{len(data):06d}',
                'Quantity': np.random.randint(1, 10),
                'UnitPrice': round(amount / np.random.randint(1, 10), 2),
                'Country': np.random.choice(['UK', 'Germany', 'France', 'Spain', 'Italy'])
            })
    
    df = pd.DataFrame(data)
    print(f"Dataset loaded: {len(df)} transactions for {df['CustomerID'].nunique()} customers")
    
    # Create SQLite database and load data
    conn = sqlite3.connect('online_retail.db')
    df.to_sql('online_retail', conn, if_exists='replace', index=False)
    
    print("Data loaded into SQLite database: online_retail.db")
    return conn

def execute_sql_cohort_analysis(conn):
    """
    Execute SQL queries to perform cohort retention analysis
    """
    print("\nExecuting SQL cohort retention analysis...")
    
    # SQL Query to calculate cohort retention
    sql_query = """
    WITH customer_cohorts AS (
        SELECT 
            CustomerID,
            MIN(DATE(InvoiceDate)) AS cohort_month
        FROM online_retail
        GROUP BY CustomerID
    ),
    cohort_counts AS (
        SELECT 
            cc.cohort_month,
            CAST(strftime('%Y', DATE(o.InvoiceDate)) AS INTEGER) * 12 + 
            CAST(strftime('%m', DATE(o.InvoiceDate)) AS INTEGER) -
            (CAST(strftime('%Y', cc.cohort_month) AS INTEGER) * 12 + 
             CAST(strftime('%m', cc.cohort_month) AS INTEGER)) AS cohort_index,
            COUNT(DISTINCT o.CustomerID) AS customer_count
        FROM online_retail o
        JOIN customer_cohorts cc ON o.CustomerID = cc.CustomerID
        GROUP BY cc.cohort_month, cohort_index
    ),
    cohort_sizes AS (
        SELECT 
            cohort_month,
            customer_count AS cohort_size
        FROM cohort_counts
        WHERE cohort_index = 0
    )
    SELECT 
        cc.cohort_month,
        cc.cohort_index,
        cs.cohort_size,
        cc.customer_count,
        ROUND((cc.customer_count * 100.0 / cs.cohort_size), 2) AS retention_rate
    FROM cohort_counts cc
    JOIN cohort_sizes cs ON cc.cohort_month = cs.cohort_month
    ORDER BY cc.cohort_month, cc.cohort_index
    """
    
    # Execute query and load into DataFrame
    df_retention = pd.read_sql_query(sql_query, conn)
    
    print("SQL query executed successfully")
    print(f"Results: {len(df_retention)} rows returned")
    
    return df_retention

def create_cohort_table_from_sql(df_retention):
    """
    Create cohort retention table from SQL results
    """
    print("\nCreating cohort table from SQL results...")
    
    # Pivot the data to create cohort table
    cohort_table = df_retention.pivot(
        index='cohort_month', 
        columns='cohort_index', 
        values='retention_rate'
    )
    
    # Convert cohort_month to readable format
    cohort_table.index = pd.to_datetime(cohort_table.index).strftime('%Y-%m')
    
    print("Cohort table created from SQL results")
    return cohort_table

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
    
    plt.title('Cohort Retention Analysis (SQL Implementation) - Customer Retention by Signup Month', 
              fontsize=16, fontweight='bold')
    plt.xlabel('Months Since Signup', fontsize=12)
    plt.ylabel('Cohort (Signup Month)', fontsize=12)
    plt.tight_layout()
    
    plt.savefig('cohort_retention_heatmap_sql.png', dpi=300, bbox_inches='tight')
    print("Heatmap saved as cohort_retention_heatmap_sql.png")
    plt.show()

def analyze_insights_from_sql(df_retention):
    """
    Generate insights from SQL results
    """
    print("\n" + "="*60)
    print("COHORT RETENTION INSIGHTS (SQL-BASED)")
    print("="*60)
    
    insights = []
    
    # Calculate average retention by cohort index
    avg_retention = df_retention.groupby('cohort_index')['retention_rate'].mean()
    
    insights.append("Average retention across all cohorts:")
    for month_idx in sorted(avg_retention.index):
        rate = avg_retention[month_idx]
        if month_idx == 0:
            insights.append(f"  Month 0 (signup month): {rate:.1f}%")
        else:
            insights.append(f"  Month {month_idx}: {rate:.1f}%")
    
    # Best performing cohort
    cohort_performance = df_retention.groupby('cohort_month')['retention_rate'].mean()
    best_cohort = cohort_performance.idxmax()
    insights.append(f"\nBest performing cohort: {best_cohort} (avg retention: {cohort_performance.max():.1f}%)")
    
    # Worst performing cohort
    worst_cohort = cohort_performance.idxmin()
    insights.append(f"Worst performing cohort: {worst_cohort} (avg retention: {cohort_performance.min():.1f}%)")
    
    # Retention decay
    if len(avg_retention) > 1:
        month1_retention = avg_retention[1] if 1 in avg_retention.index else 0
        month0_retention = avg_retention[0]
        decay = month0_retention - month1_retention
        insights.append(f"\nRetention decay from month 0 to month 1: {decay:.1f} percentage points")
    
    # Long-term retention
    if 6 in avg_retention.index:
        month6_retention = avg_retention[6]
        insights.append(f"6-month retention rate: {month6_retention:.1f}%")
    
    for insight in insights:
        print(insight)
    
    return insights

def save_sql_results(retention, df_retention, insights):
    """
    Save SQL-based results to files
    """
    print("\nSaving SQL-based results...")
    
    # Save cohort table to CSV
    retention.to_csv('cohort_retention_table_sql.csv')
    print("Cohort table saved to cohort_retention_table_sql.csv")
    
    # Save raw SQL results to CSV
    df_retention.to_csv('cohort_retention_raw_sql.csv', index=False)
    print("Raw SQL results saved to cohort_retention_raw_sql.csv")
    
    # Save insights to text file
    with open('cohort_insights_sql.txt', 'w') as f:
        f.write("COHORT RETENTION ANALYSIS INSIGHTS (SQL-BASED)\n")
        f.write("="*60 + "\n\n")
        for insight in insights:
            f.write(insight + "\n")
    print("Insights saved to cohort_insights_sql.txt")
    
    # Save the SQL query used
    sql_query = """
-- Complete SQL Query for Cohort Retention Analysis
WITH customer_cohorts AS (
    SELECT 
        CustomerID,
        MIN(DATE(InvoiceDate)) AS cohort_month
    FROM online_retail
    GROUP BY CustomerID
),
cohort_counts AS (
    SELECT 
        cc.cohort_month,
        CAST(strftime('%Y', DATE(o.InvoiceDate)) AS INTEGER) * 12 + 
        CAST(strftime('%m', DATE(o.InvoiceDate)) AS INTEGER) -
        (CAST(strftime('%Y', cc.cohort_month) AS INTEGER) * 12 + 
         CAST(strftime('%m', cc.cohort_month) AS INTEGER)) AS cohort_index,
        COUNT(DISTINCT o.CustomerID) AS customer_count
    FROM online_retail o
    JOIN customer_cohorts cc ON o.CustomerID = cc.CustomerID
    GROUP BY cc.cohort_month, cohort_index
),
cohort_sizes AS (
    SELECT 
        cohort_month,
        customer_count AS cohort_size
    FROM cohort_counts
    WHERE cohort_index = 0
)
SELECT 
    cc.cohort_month,
    cc.cohort_index,
    cs.cohort_size,
    cc.customer_count,
    ROUND((cc.customer_count * 100.0 / cs.cohort_size), 2) AS retention_rate
FROM cohort_counts cc
JOIN cohort_sizes cs ON cc.cohort_month = cs.cohort_month
ORDER BY cc.cohort_month, cc.cohort_index;
"""
    
    with open('cohort_retention_query_executed.sql', 'w') as f:
        f.write(sql_query)
    print("Executed SQL query saved to cohort_retention_query_executed.sql")

def display_sql_query_info():
    """
    Display information about the SQL implementation
    """
    print("\n" + "="*60)
    print("SQL IMPLEMENTATION DETAILS")
    print("="*60)
    print("\nThis analysis uses SQLite with the following SQL approach:")
    print("1. customer_cohorts CTE: Identifies first purchase month per customer")
    print("2. cohort_counts CTE: Counts customers per cohort and time period")
    print("3. cohort_sizes CTE: Gets initial cohort sizes")
    print("4. Final SELECT: Joins results and calculates retention rates")
    print("\nKey SQL features used:")
    print("- Common Table Expressions (CTEs)")
    print("- Window functions (not needed in this simplified version)")
    print("- Date functions (strftime for SQLite)")
    print("- JOIN operations")
    print("- Aggregation functions (COUNT, AVG)")

def main():
    """
    Main execution function for SQL-based analysis
    """
    print("="*60)
    print("COHORT RETENTION ANALYSIS - SQL IMPLEMENTATION")
    print("Task 22: Cohort Retention Basics")
    print("Data Analytics Track - Veda Technology Internship")
    print("="*60)
    
    # Load data into SQLite database
    conn = load_data_to_db()
    
    # Execute SQL analysis
    df_retention = execute_sql_cohort_analysis(conn)
    
    # Display raw SQL results
    print("\nRaw SQL Results (first 10 rows):")
    print(df_retention.head(10))
    
    # Create cohort table from SQL results
    retention = create_cohort_table_from_sql(df_retention)
    
    # Display cohort table
    print("\nCohort Retention Table (from SQL):")
    print(retention)
    
    # Visualize retention
    visualize_retention(retention)
    
    # Analyze insights
    insights = analyze_insights_from_sql(df_retention)
    
    # Save results
    save_sql_results(retention, df_retention, insights)
    
    # Display SQL implementation details
    display_sql_query_info()
    
    # Close database connection
    conn.close()
    print("\nDatabase connection closed")
    
    print("\n" + "="*60)
    print("SQL ANALYSIS COMPLETE!")
    print("="*60)
    print("\nGenerated files:")
    print("  - online_retail.db (SQLite database)")
    print("  - cohort_retention_table_sql.csv")
    print("  - cohort_retention_raw_sql.csv")
    print("  - cohort_retention_heatmap_sql.png")
    print("  - cohort_insights_sql.txt")
    print("  - cohort_retention_query_executed.sql")
    print("\nThis demonstrates a complete SQL-based implementation")
    print("of cohort retention analysis using SQLite.")

if __name__ == "__main__":
    main()
