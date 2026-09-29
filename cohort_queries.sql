
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
