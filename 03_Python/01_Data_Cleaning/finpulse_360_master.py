# ============================================================
# FINPULSE 360
# END-TO-END FINANCIAL / BANKING DATA ANALYTICS PROJECT
# ============================================================

import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ------------------------------------------------------------
# 1. PROJECT PATHS
# ------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

DATA_DIR = os.path.join(PROJECT_DIR, "02_Data")
RAW_DIR = os.path.join(DATA_DIR, "Raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "Processed")
REPORT_DIR = os.path.join(PROJECT_DIR, "05_Reports")
SQL_DIR = os.path.join(PROJECT_DIR, "04_SQL")
POWERBI_DIR = os.path.join(PROJECT_DIR, "06_PowerBI")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(SQL_DIR, exist_ok=True)
os.makedirs(POWERBI_DIR, exist_ok=True)

print("=" * 70)
print("FINPULSE 360 - STARTING PROJECT")
print("=" * 70)

# ------------------------------------------------------------
# 2. FIND CSV AUTOMATICALLY
# ------------------------------------------------------------

csv_files = []

search_locations = [
    RAW_DIR,
    DATA_DIR,
    PROJECT_DIR
]

for location in search_locations:
    if os.path.exists(location):
        for file in glob.glob(os.path.join(location, "**", "*.csv"), recursive=True):
            if file not in csv_files:
                csv_files.append(file)

if not csv_files:
    print("\nERROR: No CSV file was found.")
    print("Put your banking CSV inside:")
    print(RAW_DIR)
    input("\nPress Enter to close...")
    raise SystemExit

# Prefer raw-data files
preferred = [
    f for f in csv_files
    if "raw" in f.lower() or "bank" in os.path.basename(f).lower()
]

if preferred:
    file_path = preferred[0]
else:
    file_path = csv_files[0]

print("\nInput dataset:")
print(file_path)

# ------------------------------------------------------------
# 3. LOAD DATA
# ------------------------------------------------------------

try:
    df = pd.read_csv(file_path)
except Exception:
    try:
        df = pd.read_csv(file_path, encoding="latin1")
    except Exception as e:
        print("\nCould not read CSV.")
        print(e)
        input("\nPress Enter to close...")
        raise SystemExit

print("\nOriginal shape:", df.shape)

# ------------------------------------------------------------
# 4. STANDARDIZE COLUMN NAMES
# ------------------------------------------------------------

df.columns = (
    df.columns
    .astype(str)
    .str.strip()
    .str.lower()
    .str.replace(" ", "_", regex=False)
    .str.replace("-", "_", regex=False)
    .str.replace("/", "_", regex=False)
)

print("\nDetected columns:")
print(list(df.columns))

# ------------------------------------------------------------
# 5. REMOVE COMPLETELY EMPTY COLUMNS
# ------------------------------------------------------------

df = df.dropna(axis=1, how="all")

# ------------------------------------------------------------
# 6. REMOVE DUPLICATES
# ------------------------------------------------------------

duplicate_count = int(df.duplicated().sum())
df = df.drop_duplicates().reset_index(drop=True)

print("\nDuplicates removed:", duplicate_count)

# ------------------------------------------------------------
# 7. CLEAN TEXT COLUMNS
# ------------------------------------------------------------

for col in df.select_dtypes(include=["object"]).columns:
    df[col] = df[col].astype(str).str.strip()

# Convert obvious numeric columns
for col in df.columns:
    if df[col].dtype == "object":
        cleaned = (
            df[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.replace("₹", "", regex=False)
            .str.replace("$", "", regex=False)
            .str.replace("INR", "", regex=False)
            .str.strip()
        )

        numeric_version = pd.to_numeric(cleaned, errors="coerce")

        valid_ratio = numeric_version.notna().mean()

        if valid_ratio >= 0.80:
            df[col] = numeric_version

# ------------------------------------------------------------
# 8. HANDLE MISSING VALUES
# ------------------------------------------------------------

missing_before = int(df.isna().sum().sum())

for col in df.columns:

    if pd.api.types.is_numeric_dtype(df[col]):
        if df[col].isna().any():
            median_value = df[col].median()

            if pd.notna(median_value):
                df[col] = df[col].fillna(median_value)
            else:
                df[col] = df[col].fillna(0)

    else:
        if df[col].isna().any():
            mode_values = df[col].mode()

            if len(mode_values) > 0:
                df[col] = df[col].fillna(mode_values.iloc[0])
            else:
                df[col] = df[col].fillna("Unknown")

missing_after = int(df.isna().sum().sum())

print("Missing values before:", missing_before)
print("Missing values after:", missing_after)

# ------------------------------------------------------------
# 9. IDENTIFY IMPORTANT COLUMNS
# ------------------------------------------------------------

def find_column(possible_names):
    for name in possible_names:
        if name in df.columns:
            return name

    for col in df.columns:
        normalized = col.lower().replace("_", "")

        for name in possible_names:
            target = name.lower().replace("_", "")

            if normalized == target:
                return col

    return None


amount_col = find_column([
    "transaction_amount",
    "transactionamount",
    "amount",
    "transaction_value",
    "transactionvalue",
    "debit_amount",
    "credit_amount",
    "value"
])

date_col = find_column([
    "date",
    "transaction_date",
    "transactiondate",
    "datetime",
    "timestamp",
    "transaction_time"
])

category_col = find_column([
    "category",
    "transaction_type",
    "transactiontype",
    "type",
    "purpose",
    "description"
])

customer_col = find_column([
    "customer_id",
    "customerid",
    "customer",
    "account_id",
    "accountid",
    "account_number"
])

merchant_col = find_column([
    "merchant",
    "merchant_name",
    "merchantname",
    "payee",
    "vendor"
])

location_col = find_column([
    "location",
    "city",
    "branch",
    "state"
])

balance_col = find_column([
    "balance",
    "account_balance",
    "closing_balance"
])

print("\nDetected important columns:")
print("Amount:", amount_col)
print("Date:", date_col)
print("Category:", category_col)
print("Customer:", customer_col)
print("Merchant:", merchant_col)
print("Location:", location_col)
print("Balance:", balance_col)

# ------------------------------------------------------------
# 10. CREATE CLEAN DATASET
# ------------------------------------------------------------

cleaned_path = os.path.join(
    PROCESSED_DIR,
    "finpulse_360_cleaned_data.csv"
)

df.to_csv(cleaned_path, index=False)

print("\nClean dataset created:")
print(cleaned_path)

# ------------------------------------------------------------
# 11. DATA QUALITY REPORT
# ------------------------------------------------------------

quality_rows = []

for col in df.columns:
    quality_rows.append({
        "column": col,
        "data_type": str(df[col].dtype),
        "row_count": len(df),
        "missing_values": int(df[col].isna().sum()),
        "unique_values": int(df[col].nunique()),
        "duplicate_values": int(df[col].duplicated().sum())
    })

quality_df = pd.DataFrame(quality_rows)

quality_path = os.path.join(
    PROCESSED_DIR,
    "data_quality_report.csv"
)

quality_df.to_csv(quality_path, index=False)

# ------------------------------------------------------------
# 12. STATISTICAL SUMMARY
# ------------------------------------------------------------

numeric_columns = df.select_dtypes(include=np.number).columns.tolist()

if numeric_columns:
    statistical_summary = df[numeric_columns].describe().T.reset_index()
    statistical_summary = statistical_summary.rename(
        columns={"index": "column"}
    )
else:
    statistical_summary = pd.DataFrame({
        "message": ["No numeric columns detected."]
    })

stat_path = os.path.join(
    PROCESSED_DIR,
    "statistical_summary.csv"
)

statistical_summary.to_csv(stat_path, index=False)

# ------------------------------------------------------------
# 13. CORRELATION ANALYSIS
# ------------------------------------------------------------

if len(numeric_columns) >= 2:

    correlation_matrix = df[numeric_columns].corr()

    correlation_path = os.path.join(
        PROCESSED_DIR,
        "correlation_matrix.csv"
    )

    correlation_matrix.to_csv(correlation_path)

    plt.figure(figsize=(10, 7))
    plt.imshow(
        correlation_matrix,
        interpolation="nearest",
        aspect="auto"
    )
    plt.colorbar()

    plt.xticks(
        range(len(correlation_matrix.columns)),
        correlation_matrix.columns,
        rotation=90
    )

    plt.yticks(
        range(len(correlation_matrix.columns)),
        correlation_matrix.columns
    )

    plt.title("FinPulse 360 - Correlation Matrix")
    plt.tight_layout()

    plt.savefig(
        os.path.join(
            PROCESSED_DIR,
            "correlation_heatmap.png"
        ),
        dpi=150
    )

    plt.close()

# ------------------------------------------------------------
# 14. AMOUNT ANALYSIS
# ------------------------------------------------------------

if amount_col is not None:

    df[amount_col] = pd.to_numeric(
        df[amount_col],
        errors="coerce"
    ).fillna(0)

    amount_summary = pd.DataFrame({
        "metric": [
            "Total Transactions",
            "Total Transaction Value",
            "Average Transaction Value",
            "Median Transaction Value",
            "Minimum Transaction Value",
            "Maximum Transaction Value",
            "Transaction Value Standard Deviation"
        ],
        "value": [
            len(df),
            df[amount_col].sum(),
            df[amount_col].mean(),
            df[amount_col].median(),
            df[amount_col].min(),
            df[amount_col].max(),
            df[amount_col].std()
        ]
    })

    amount_summary.to_csv(
        os.path.join(
            PROCESSED_DIR,
            "transaction_amount_summary.csv"
        ),
        index=False
    )

    # Distribution chart
    plt.figure(figsize=(10, 6))

    plt.hist(
        df[amount_col],
        bins=30
    )

    plt.title("Transaction Amount Distribution")
    plt.xlabel("Transaction Amount")
    plt.ylabel("Number of Transactions")
    plt.tight_layout()

    plt.savefig(
        os.path.join(
            PROCESSED_DIR,
            "transaction_amount_distribution.png"
        ),
        dpi=150
    )

    plt.close()

# ------------------------------------------------------------
# 15. CATEGORY ANALYSIS
# ------------------------------------------------------------

if category_col is not None:

    category_analysis = (
        df.groupby(category_col)
        .size()
        .reset_index(name="transaction_count")
        .sort_values(
            "transaction_count",
            ascending=False
        )
    )

    if amount_col is not None:

        category_value = (
            df.groupby(category_col)[amount_col]
            .agg(
                total_amount="sum",
                average_amount="mean"
            )
            .reset_index()
        )

        category_analysis = category_analysis.merge(
            category_value,
            on=category_col,
            how="left"
        )

    category_analysis.to_csv(
        os.path.join(
            PROCESSED_DIR,
            "category_analysis.csv"
        ),
        index=False
    )

    top_categories = category_analysis.head(10)

    plt.figure(figsize=(10, 6))

    plt.bar(
        top_categories[category_col].astype(str),
        top_categories["transaction_count"]
    )

    plt.title("Top Transaction Categories")
    plt.xlabel("Category")
    plt.ylabel("Transaction Count")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    plt.savefig(
        os.path.join(
            PROCESSED_DIR,
            "category_analysis.png"
        ),
        dpi=150
    )

    plt.close()

# ------------------------------------------------------------
# 16. CUSTOMER ANALYSIS
# ------------------------------------------------------------

if customer_col is not None:

    customer_analysis = (
        df.groupby(customer_col)
        .size()
        .reset_index(name="transaction_count")
    )

    if amount_col is not None:

        customer_value = (
            df.groupby(customer_col)[amount_col]
            .agg(
                total_transaction_value="sum",
                average_transaction_value="mean"
            )
            .reset_index()
        )

        customer_analysis = customer_analysis.merge(
            customer_value,
            on=customer_col,
            how="left"
        )

    customer_analysis = customer_analysis.sort_values(
        "transaction_count",
        ascending=False
    )

    customer_analysis.to_csv(
        os.path.join(
            PROCESSED_DIR,
            "customer_analysis.csv"
        ),
        index=False
    )

# ------------------------------------------------------------
# 17. MERCHANT ANALYSIS
# ------------------------------------------------------------

if merchant_col is not None:

    merchant_analysis = (
        df.groupby(merchant_col)
        .size()
        .reset_index(name="transaction_count")
        .sort_values(
            "transaction_count",
            ascending=False
        )
    )

    if amount_col is not None:

        merchant_value = (
            df.groupby(merchant_col)[amount_col]
            .agg(
                total_transaction_value="sum",
                average_transaction_value="mean"
            )
            .reset_index()
        )

        merchant_analysis = merchant_analysis.merge(
            merchant_value,
            on=merchant_col,
            how="left"
        )

    merchant_analysis.to_csv(
        os.path.join(
            PROCESSED_DIR,
            "merchant_analysis.csv"
        ),
        index=False
    )

# ------------------------------------------------------------
# 18. LOCATION ANALYSIS
# ------------------------------------------------------------

if location_col is not None:

    location_analysis = (
        df.groupby(location_col)
        .size()
        .reset_index(name="transaction_count")
        .sort_values(
            "transaction_count",
            ascending=False
        )
    )

    if amount_col is not None:

        location_value = (
            df.groupby(location_col)[amount_col]
            .agg(
                total_transaction_value="sum",
                average_transaction_value="mean"
            )
            .reset_index()
        )

        location_analysis = location_analysis.merge(
            location_value,
            on=location_col,
            how="left"
        )

    location_analysis.to_csv(
        os.path.join(
            PROCESSED_DIR,
            "location_analysis.csv"
        ),
        index=False
    )

# ------------------------------------------------------------
# 19. DATE / MONTHLY ANALYSIS
# ------------------------------------------------------------

if date_col is not None:

    converted_dates = pd.to_datetime(
        df[date_col],
        errors="coerce"
    )

    valid_dates = converted_dates.notna().sum()

    if valid_dates > 0:

        df["analysis_date"] = converted_dates
        df["analysis_year"] = converted_dates.dt.year
        df["analysis_month"] = converted_dates.dt.month
        df["analysis_month_name"] = converted_dates.dt.strftime("%B")

        monthly_group = (
            df.dropna(subset=["analysis_date"])
            .groupby(
                [
                    "analysis_year",
                    "analysis_month"
                ]
            )
            .size()
            .reset_index(
                name="transaction_count"
            )
        )

        if amount_col is not None:

            monthly_value = (
                df.dropna(subset=["analysis_date"])
                .groupby(
                    [
                        "analysis_year",
                        "analysis_month"
                    ]
                )[amount_col]
                .agg(
                    total_transaction_value="sum",
                    average_transaction_value="mean"
                )
                .reset_index()
            )

            monthly_group = monthly_group.merge(
                monthly_value,
                on=[
                    "analysis_year",
                    "analysis_month"
                ],
                how="left"
            )

        monthly_group.to_csv(
            os.path.join(
                PROCESSED_DIR,
                "monthly_transaction_analysis.csv"
            ),
            index=False
        )

# ------------------------------------------------------------
# 20. HIGH-VALUE TRANSACTIONS
# ------------------------------------------------------------

if amount_col is not None:

    threshold = df[amount_col].quantile(0.95)

    high_value = df[
        df[amount_col] >= threshold
    ].copy()

    high_value = high_value.sort_values(
        amount_col,
        ascending=False
    )

    high_value.to_csv(
        os.path.join(
            PROCESSED_DIR,
            "high_value_transactions.csv"
        ),
        index=False
    )

# ------------------------------------------------------------
# 21. RISK FLAGS
# ------------------------------------------------------------

if amount_col is not None:

    risk_df = df.copy()

    risk_threshold = df[amount_col].quantile(0.95)

    risk_df["high_value_flag"] = np.where(
        risk_df[amount_col] >= risk_threshold,
        "High",
        "Normal"
    )

    risk_df["risk_score"] = np.where(
        risk_df[amount_col] >= risk_threshold,
        2,
        0
    )

    if category_col is not None:

        category_counts = (
            risk_df[category_col]
            .value_counts()
        )

        rare_categories = category_counts[
            category_counts <= 2
        ].index

        risk_df["rare_category_flag"] = np.where(
            risk_df[category_col].isin(
                rare_categories
            ),
            "Review",
            "Normal"
        )

        risk_df.loc[
            risk_df["rare_category_flag"] == "Review",
            "risk_score"
        ] += 1

    risk_df.to_csv(
        os.path.join(
            PROCESSED_DIR,
            "financial_risk_flags.csv"
        ),
        index=False
    )

# ------------------------------------------------------------
# 22. POWER BI DATASET
# ------------------------------------------------------------

powerbi_df = df.copy()

powerbi_path = os.path.join(
    POWERBI_DIR,
    "FinPulse_360_PowerBI_Dataset.csv"
)

powerbi_df.to_csv(
    powerbi_path,
    index=False
)

print("\nPower BI dataset created:")
print(powerbi_path)

# ------------------------------------------------------------
# 23. EXECUTIVE SUMMARY
# ------------------------------------------------------------

summary_lines = []

summary_lines.append("FINPULSE 360 - EXECUTIVE SUMMARY")
summary_lines.append("=" * 60)
summary_lines.append("")
summary_lines.append(
    "FinPulse 360 is an end-to-end financial data analytics project."
)
summary_lines.append("")
summary_lines.append(
    "DATASET OVERVIEW"
)
summary_lines.append(
    "Rows analyzed: " + str(len(df))
)
summary_lines.append(
    "Columns analyzed: " + str(len(df.columns))
)
summary_lines.append(
    "Duplicate rows removed: " + str(duplicate_count)
)
summary_lines.append(
    "Missing values before cleaning: " + str(missing_before)
)
summary_lines.append(
    "Missing values after cleaning: " + str(missing_after)
)
summary_lines.append("")

if amount_col is not None:

    summary_lines.append(
        "TRANSACTION VALUE"
    )
    summary_lines.append(
        "Total transaction value: "
        + f"{df[amount_col].sum():,.2f}"
    )
    summary_lines.append(
        "Average transaction value: "
        + f"{df[amount_col].mean():,.2f}"
    )
    summary_lines.append(
        "Median transaction value: "
        + f"{df[amount_col].median():,.2f}"
    )
    summary_lines.append(
        "Maximum transaction value: "
        + f"{df[amount_col].max():,.2f}"
    )
    summary_lines.append("")

if category_col is not None:

    top_category = (
        df[category_col]
        .value_counts()
        .index[0]
    )

    summary_lines.append(
        "TOP TRANSACTION CATEGORY"
    )
    summary_lines.append(
        str(top_category)
    )
    summary_lines.append("")

if customer_col is not None:

    summary_lines.append(
        "CUSTOMER ANALYSIS"
    )
    summary_lines.append(
        "Unique customers: "
        + str(df[customer_col].nunique())
    )
    summary_lines.append("")

summary_lines.append(
    "ANALYTICAL MODULES COMPLETED"
)

summary_lines.append(
    "1. Data inspection"
)
summary_lines.append(
    "2. Data cleaning"
)
summary_lines.append(
    "3. Missing-value handling"
)
summary_lines.append(
    "4. Duplicate removal"
)
summary_lines.append(
    "5. Statistical analysis"
)
summary_lines.append(
    "6. Correlation analysis"
)
summary_lines.append(
    "7. Transaction amount analysis"
)
summary_lines.append(
    "8. Category analysis"
)
summary_lines.append(
    "9. Customer analysis"
)
summary_lines.append(
    "10. Merchant analysis"
)
summary_lines.append(
    "11. Location analysis"
)
summary_lines.append(
    "12. Monthly analysis"
)
summary_lines.append(
    "13. High-value transaction analysis"
)
summary_lines.append(
    "14. Financial risk flags"
)
summary_lines.append(
    "15. Power BI dataset preparation"
)

summary_path = os.path.join(
    REPORT_DIR,
    "executive_summary.txt"
)

with open(
    summary_path,
    "w",
    encoding="utf-8"
) as f:
    f.write("\n".join(summary_lines))

# ------------------------------------------------------------
# 24. BUSINESS RECOMMENDATIONS
# ------------------------------------------------------------

recommendations = []

recommendations.append(
    "FINPULSE 360 - BUSINESS RECOMMENDATIONS"
)
recommendations.append("=" * 60)
recommendations.append("")

recommendations.append(
    "1. Monitor high-value transactions for enhanced review."
)

recommendations.append(
    "2. Use transaction-category trends to understand customer activity."
)

recommendations.append(
    "3. Track customer transaction frequency to identify important customer segments."
)

recommendations.append(
    "4. Monitor merchant and location performance where available."
)

recommendations.append(
    "5. Use monthly transaction trends for operational planning."
)

recommendations.append(
    "6. Use the Power BI dataset to create an interactive management dashboard."
)

recommendations.append(
    "7. Combine transaction volume and transaction value when evaluating business performance."
)

recommendations.append(
    "8. Investigate unusual or rare transaction patterns before making financial decisions."
)

recommendations_path = os.path.join(
    REPORT_DIR,
    "business_recommendations.txt"
)

with open(
    recommendations_path,
    "w",
    encoding="utf-8"
) as f:
    f.write("\n".join(recommendations))

# ------------------------------------------------------------
# 25. DATA DICTIONARY
# ------------------------------------------------------------

dictionary_rows = []

for col in df.columns:

    dictionary_rows.append({
        "column_name": col,
        "data_type": str(df[col].dtype),
        "description": "Dataset field used in FinPulse 360 analysis"
    })

dictionary_df = pd.DataFrame(dictionary_rows)

dictionary_df.to_csv(
    os.path.join(
        REPORT_DIR,
        "data_dictionary.csv"
    ),
    index=False
)

# ------------------------------------------------------------
# 26. SQL ANALYSIS FILE
# ------------------------------------------------------------

sql_content = """
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
"""

sql_path = os.path.join(
    SQL_DIR,
    "finpulse_360_analysis.sql"
)

with open(
    sql_path,
    "w",
    encoding="utf-8"
) as f:
    f.write(sql_content)

# ------------------------------------------------------------
# 27. README
# ------------------------------------------------------------

readme_lines = []

readme_lines.append("# FinPulse 360")
readme_lines.append("")
readme_lines.append(
    "End-to-end financial and banking data analytics project built with Python."
)
readme_lines.append("")

readme_lines.append("## Project Objective")
readme_lines.append("")
readme_lines.append(
    "FinPulse 360 transforms transaction data into analytical insights "
    "covering transaction behavior, customer activity, categories, "
    "locations, high-value transactions and financial risk indicators."
)
readme_lines.append("")

readme_lines.append("## Key Features")
readme_lines.append("")
readme_lines.append("- Data inspection")
readme_lines.append("- Data cleaning")
readme_lines.append("- Missing-value handling")
readme_lines.append("- Duplicate detection and removal")
readme_lines.append("- Statistical analysis")
readme_lines.append("- Correlation analysis")
readme_lines.append("- Transaction analysis")
readme_lines.append("- Customer analysis")
readme_lines.append("- Category analysis")
readme_lines.append("- Merchant analysis")
readme_lines.append("- Location analysis")
readme_lines.append("- Monthly trend analysis")
readme_lines.append("- High-value transaction analysis")
readme_lines.append("- Financial risk flagging")
readme_lines.append("- Power BI-ready dataset")
readme_lines.append("- SQL analysis")
readme_lines.append("")

readme_lines.append("## Technologies")
readme_lines.append("")
readme_lines.append("- Python")
readme_lines.append("- Pandas")
readme_lines.append("- NumPy")
readme_lines.append("- Matplotlib")
readme_lines.append("- SQL")
readme_lines.append("- Power BI")
readme_lines.append("")

readme_lines.append("## Project Structure")
readme_lines.append("")
readme_lines.append("```text")
readme_lines.append("FinPulse-360/")
readme_lines.append("├── 01_Project_Charter/")
readme_lines.append("├── 02_Data/")
readme_lines.append("│   ├── Raw/")
readme_lines.append("│   └── Processed/")
readme_lines.append("├── 03_Python/")
readme_lines.append("│   └── 01_Data_Cleaning/")
readme_lines.append("│       └── finpulse_360_master.py")
readme_lines.append("├── 04_SQL/")
readme_lines.append("│   └── finpulse_360_analysis.sql")
readme_lines.append("├── 05_Reports/")
readme_lines.append("└── 06_PowerBI/")
readme_lines.append("```")
readme_lines.append("")

readme_lines.append("## Business Value")
readme_lines.append("")
readme_lines.append(
    "The project demonstrates how raw financial transaction data can "
    "be transformed into structured information for reporting, "
    "decision support and business intelligence."
)

readme_path = os.path.join(
    PROJECT_DIR,
    "README.md"
)

with open(
    readme_path,
    "w",
    encoding="utf-8"
) as f:
    f.write("\n".join(readme_lines))

# ------------------------------------------------------------
# 28. FINAL PROJECT SUMMARY
# ------------------------------------------------------------

summary_df = pd.DataFrame({
    "metric": [
        "Input file",
        "Rows after cleaning",
        "Columns",
        "Duplicates removed",
        "Missing values before",
        "Missing values after",
        "Amount column detected",
        "Date column detected",
        "Category column detected",
        "Customer column detected"
    ],
    "value": [
        os.path.basename(file_path),
        len(df),
        len(df.columns),
        duplicate_count,
        missing_before,
        missing_after,
        str(amount_col),
        str(date_col),
        str(category_col),
        str(customer_col)
    ]
})

summary_df.to_csv(
    os.path.join(
        PROCESSED_DIR,
        "project_summary.csv"
    ),
    index=False
)

# ------------------------------------------------------------
# 29. FINAL OUTPUT LIST
# ------------------------------------------------------------

print("\n")
print("=" * 70)
print("FINPULSE 360 COMPLETED SUCCESSFULLY")
print("=" * 70)

print("\nCreated folders:")
print("02_Data/Processed/")
print("04_SQL/")
print("05_Reports/")
print("06_PowerBI/")

print("\nMain files created:")

for folder in [
    PROCESSED_DIR,
    REPORT_DIR,
    SQL_DIR,
    POWERBI_DIR
]:
    if os.path.exists(folder):

        for name in sorted(os.listdir(folder)):

            full_path = os.path.join(folder, name)

            if os.path.isfile(full_path):
                print("  ✓", name)

print("\nREADME:")
print(readme_path)

print("\nPower BI dataset:")
print(powerbi_path)

print("\nSQL file:")
print(sql_path)

print("\n")
print("=" * 70)
print("PROJECT READY FOR GITHUB / POWER BI / LINKEDIN")
print("=" * 70)

input("\nPress Enter to close...")