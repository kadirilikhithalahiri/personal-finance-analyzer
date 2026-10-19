# Personal Finance Analyzer

A Streamlit website with a Python data-processing backend for the cleaned Amazon sales transaction dataset.

## Features
- Upload CSV or JSON data
- Filter by category, geography, and date
- KPIs: sales, profit, quantity, profit margin
- Monthly sales/profit trends
- Category, product, and geography charts
- Lowest-profit products table
- Download filtered data as CSV or JSON

## 1. Prepare the dataset
In Google Colab, download:
`finance_analyzer_output/cleaned_transactions.csv`

Place it at:
`data/cleaned_transactions.csv`

If you do not bundle the file, the website still works: upload the CSV or JSON from the sidebar.

Expected fields: `Sales`, `Profit`, `Quantity`; recommended fields: `Order_Date`, `Category`, `Geography`, `Product_Name`.

## 2. Run locally
Install Python 3.10 or newer, open a terminal in this folder, then run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit.

## 3. Free hosting
This project can be deployed to a free Python web host such as Render or Hugging Face Spaces, subject to each host's current free-tier limitations.

### Render
- Create a new Web Service and connect a Git repository or provide a public repository URL.
- Build command: `pip install -r requirements.txt`
- Start command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
- Include `data/cleaned_transactions.csv` in the project if you want the dataset preloaded.
- Free services may sleep when idle and their local filesystem is ephemeral; don't rely on the service filesystem to store user data.

### Hugging Face Spaces
- Create a new Space and choose the Streamlit SDK if available in the creation options.
- Upload `app.py`, `requirements.txt`, and optionally `data/cleaned_transactions.csv`.
- If the current Space template requires a specific entrypoint or SDK setup, follow the instructions displayed by Hugging Face at creation time.

## Privacy note
Do not upload personal, financial, or confidential transaction data to a public website unless you have permission. The included example dataset is sales-analysis data, not a private personal bank statement.
