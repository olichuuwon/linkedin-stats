import pandas as pd
import sys

if len(sys.argv) < 2:
    print("Usage: python convert_xls_to_csv.py <xls_file>")
    sys.exit(1)

# Path to the XLS file
xls_file = sys.argv[1]

# Read the Metrics sheet and save as CSV
df_metrics = pd.read_excel(xls_file, sheet_name="Metrics")
df_metrics.to_csv("Metrics.csv", index=False)

# Read the All posts sheet and save as CSV
df_posts = pd.read_excel(xls_file, sheet_name="All posts")
df_posts.to_csv("All posts.csv", index=False)

print(
    f"Conversion complete. CSVs saved as Metrics.csv and All posts.csv from {xls_file}"
)
