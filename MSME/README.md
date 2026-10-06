# MSME AI Operations Copilot

**MSME AI Operations Copilot** is an AI-powered operations assistant designed to help Micro, Small, and Medium Enterprises (MSMEs) transition from manual spreadsheet tracking to automated business intelligence. 

Business owners can upload their sales and inventory spreadsheets (CSV or Excel) and immediately receive financial summaries, stockout/overstock alerts, and professional operation recommendations from a virtual advisor powered by Google Gemini.

---

## 🌟 Key Features

1. **Intelligent Dashboard:** Displays key business statistics including Total Revenue, Net Profit, Average Margins, and an automated Business Health Index score.
2. **Interactive Visualizations (Chart.js):**
   - **Revenue vs Profit:** Visualizes the financial performance of each individual SKU.
   - **Stock vs Demand:** Compares current shelf stock against monthly sales volumes to pinpoint fast-moving goods and depletion speeds.
3. **Inventory Intelligence Module:**
   - Detects low stock items at risk of running out.
   - Highlights overstocked goods tying up capital on shelves.
   - Alerts for products at high risk due to supplier dispatch lead times.
4. **AI Business Copilot:** A conversational chat interface. Business owners can ask questions like *"How can I improve my margins?"* or *"What is my restock priority?"* and receive context-aware, product-specific advice.
5. **Printable Operations Report:** Generates an executive operations report styled for paper printing or PDF export.

---

## 🛠️ Technology Stack

- **Frontend:** HTML5, CSS3 (Vanilla Glassmorphism), Javascript (ES6), Chart.js (via CDN)
- **Backend:** Python 3, Flask (API routing & asset serving)
- **Data Processing:** Pandas, OpenPyXL (Excel reader)
- **AI Reasoning:** Google Gemini API (`google-generativeai` SDK)

---

## 📂 Project Structure

```
MSME_AI_Copilot/
├── run.py                 # Setup & startup automation script
├── requirements.txt       # Backend dependencies
├── .env.example           # API configuration template
├── MSME_sample_data.csv   # Sample dataset in CSV format
├── MSME_sample_data.xlsx  # Sample dataset in Excel format (Auto-generated)
├── test_app.py            # Integration test runner
├── documents/
│   ├── BRD.md             # Business Requirement Document
│   ├── PRD.md             # Product Requirement Document
│   ├── SRS.md             # Software Requirement Specification
│   └── ADR.md             # Architecture Decision Record
├── backend/
│   ├── app.py             # Flask Web Server
│   ├── data_analysis.py   # Business logic & alerts computations
│   └── ai_engine.py       # Gemini API client & offline mocks
└── frontend/
    ├── index.html         # User Interface layout
    ├── style.css          # Premium glassmorphism style rules
    └── script.js          # Chart rendering, file uploads, & chat actions
```

---

## 🚀 Getting Started

We provide an automated setup script `run.py` to make running the application as easy as possible on Windows and other operating systems.

### Prerequisites
- Python 3.10+ installed on your computer.

### Step 1: Run the Setup and Server
Double-click `run.py` or run the following command in your terminal:
```bash
python run.py
```
This automated script will:
1. Create a local Python virtual environment (`.venv`).
2. Upgrade `pip` and install all required packages listed in `requirements.txt`.
3. Create a `.env` configuration file from `.env.example`.
4. Generate the `MSME_sample_data.xlsx` dataset file from the CSV template.
5. Launch the Flask web server.

### Step 2: Set your Gemini API Key (Optional)
By default, the application runs in **Offline Simulation Mode** with built-in rules if you do not have a Gemini API key. This lets you test the dashboard immediately. 

To enable full Gemini AI capabilities:
1. Open the newly created `.env` file in a text editor.
2. Replace the placeholder with your actual key from [Google AI Studio](https://aistudio.google.com/):
   ```env
   GEMINI_API_KEY=your_actual_api_key_here
   ```
3. Save the file and restart the server (`python run.py`).

### Step 3: Open the Dashboard
Open your browser and navigate to:
```
http://localhost:5000/
```

---

## 📊 Sample Spreadsheet Format

If you wish to create your own spreadsheet, ensure it contains the following header columns (case-insensitive, spaces can be replaced with underscores):
- `Product_Name`: Name of the item.
- `Category`: Product category.
- `Current_Stock`: Current shelf inventory quantity.
- `Monthly_Sales`: Unit sales over the last 30 days.
- `Cost_Price`: Wholesale unit purchase price.
- `Selling_Price`: Retail unit selling price.
- `Supplier_Delay_Days`: Average days for restocking delivery.
- `Customer_Rating`: Average customer review score (1.0 to 5.0).
