
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
