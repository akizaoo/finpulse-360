
-- ============================================================
-- FINPULSE 360
-- FINANCIAL / BANKING DATA ANALYTICS SQL
-- ============================================================

-- 1. Total number of transactions
SELECT COUNT(*) AS total_transactions
FROM finpulse_360;

-- 2. Total transaction value
SELECT SUM(transaction_amount) AS total_transaction_value
FROM finpulse_360;

-- 3. Average transaction value
SELECT AVG(transaction_amount) AS average_transaction_value
FROM finpulse_360;

-- 4. Maximum transaction value
SELECT MAX(transaction_amount) AS maximum_transaction_value
FROM finpulse_360;

-- 5. Minimum transaction value
SELECT MIN(transaction_amount) AS minimum_transaction_value
FROM finpulse_360;

-- 6. Category-wise transaction count
SELECT
    category,
    COUNT(*) AS transaction_count
FROM finpulse_360
GROUP BY category
ORDER BY transaction_count DESC;

-- 7. Category-wise transaction value
SELECT
    category,
    SUM(transaction_amount) AS total_value,
    AVG(transaction_amount) AS average_value
FROM finpulse_360
GROUP BY category
ORDER BY total_value DESC;

-- 8. High-value transactions
SELECT *
FROM finpulse_360
WHERE transaction_amount >=
(
    SELECT PERCENTILE_CONT(0.95)
    WITHIN GROUP
    (ORDER BY transaction_amount)
    FROM finpulse_360
);

-- 9. Customer transaction activity
SELECT
    customer_id,
    COUNT(*) AS transaction_count,
    SUM(transaction_amount) AS total_value
FROM finpulse_360
GROUP BY customer_id
ORDER BY total_value DESC;

-- 10. Monthly transaction analysis
SELECT
    DATE_TRUNC('month', transaction_date) AS month,
    COUNT(*) AS transaction_count,
    SUM(transaction_amount) AS total_value
FROM finpulse_360
GROUP BY month
ORDER BY month;
