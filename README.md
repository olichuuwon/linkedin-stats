# LinkedIn Page Admin Analytics Dashboard

A Streamlit app for analyzing LinkedIn post performance and engagement metrics.

## Features

- Upload and process LinkedIn posts and metrics CSV files
- Filter posts by date range and hashtags
- Mark posts as boosted
- View benchmarks and performance flags
- Interactive scatter plots and bar charts
- Site engagement trends over time

## Prerequisites

- Python 3.7+

## Installation

1. Clone or download the repository.
2. Install dependencies:

   ```bash
   pip install streamlit pandas altair xlrd
   ```

## XLS to CSV Conversion

If your LinkedIn data is in an XLS file with two sheets (Metrics and All posts), use the provided script to convert it to CSVs:

1. Place your XLS file in the same directory as `convert_xls_to_csv.py`.
2. Run:

   ```bash
   python convert_xls_to_csv.py your_xls_file.xls
   ```

3. This will generate `Metrics.csv` and `All posts.csv`.

Then, proceed with uploading these CSVs to the app.

## Usage

1. Run the app:

   ```bash
   python -m streamlit run main.py
   ```

2. Upload your LinkedIn CSV files (one containing 'All posts' and one containing 'Metrics').
3. Optionally upload a boosted_config.csv if you have one.
4. Use the filters and explore the visualizations.

## File Formats

- Posts CSV: Should have columns like Post title, Post link, etc.
- Metrics CSV: Should have a Date column and numeric metrics.
- Boosted Config CSV: Post Title and Boosted columns.

## Contributing

Feel free to contribute.

## License

MIT
