# Software Requirement Specification (SRS)

## Project Name
MSME AI Operations Copilot

## 1. Functional Requirements

### FR-01: CSV and Excel File Upload
- The system must accept uploads of `.csv`, `.xlsx`, and `.xls` files.
- The system must validate the file type and presence of required columns: `Product_Name`, `Category`, `Current_Stock`, `Monthly_Sales`, `Cost_Price`, `Selling_Price`, `Supplier_Delay_Days`, `Customer_Rating`.
- The system must handle upload failures gracefully and return clear, user-friendly error messages (e.g., "Missing Column: Product_Name").

### FR-02: Data Processing
- The system must read and parse uploaded file content into a Pandas DataFrame.
- The system must handle empty cells, zero values, or invalid data types (e.g., negative stocks or string values in price columns) by cleaning or ignoring them safely.

### FR-03: Business & Inventory Metrics Calculation
- The system must calculate:
  - **Total Revenue:** Sum of `Monthly_Sales` multiplied by `Selling_Price` for each product.
  - **Total Cost:** Sum of `Monthly_Sales` multiplied by `Cost_Price` for each product.
  - **Total Profit:** `Total Revenue` minus `Total Cost`.
  - **Profit Margin per Product:** `(Selling_Price - Cost_Price) / Selling_Price * 100`.
  - **Days of Stock Available:** `Current_Stock / (Monthly_Sales / 30)` (assuming uniform monthly sales).
- The system must detect:
  - **Low Stock:** Stock levels representing less than 15 days of sales, or under 10 units.
  - **Overstock:** Stock levels representing more than 90 days of sales.
  - **Fast-Moving Products:** Products in the top 25th percentile of sales volume.
  - **Supplier Risks:** Products with low stock and high supplier delay days (> 5 days).

### FR-04: Gemini API Integration
- The system must establish a secure connection to the Google Gemini API using the `google-generativeai` SDK.
- The system must securely fetch the API key from environment variables or a local configuration file.
- The system must format the calculated business statistics and inventory warnings into a structured prompt context.
- The system must request Gemini to return actionable operations advice structured for small businesses.

### FR-05: Business Chatbot (Copilot)
- The system must support an interactive chat window.
- The chatbot endpoint must consume user questions and return answers using the uploaded spreadsheet analysis as the ground-truth context.
- The chat context must persist for the duration of the session to allow follow-up questions.

### FR-06: Report Generator
- The system must compile metrics, charts, AI recommendations, and chat summaries into a structured HTML report layout that is print-ready (PDF output via browser printing).

---

## 2. Non-Functional Requirements

### NFR-01: Simple UI & Accessibility
- The frontend dashboard must feature a modern, clutter-free glassmorphism layout.
- The app should prioritize dark theme readability and use clean typography (Inter font).
- The dashboard must load and display properly on both desktop and mobile layouts (responsive).

### NFR-02: Fast Response Times
- Data processing and calculation should complete in less than 500 milliseconds for standard shop catalogs (< 1,000 products).
- Chat interactions should display a responsive typing loader to maintain high perceived speed while waiting for Gemini API responses.

### NFR-03: Clean Code & Maintainability
- The codebase must separate concerns clearly: frontend assets under `frontend/` and Flask/Python analysis files under `backend/`.
- Code must be modular, utilizing documented python functions with docstrings.
