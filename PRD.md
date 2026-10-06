# Product Requirement Document (PRD)

## Project Name
MSME AI Operations Copilot

## 1. Feature Specifications

### Feature 1: Dashboard Interface
A unified dashboard that serves as the command center for the MSME owner.
- **Key Metrics Display:**
  - **Total Revenue:** Calculated from monthly sales and selling prices.
  - **Total Profit / Margin:** Total profits generated, alongside average profit margin.
  - **Total Products:** Count of unique products in the catalog.
  - **Low Stock Alerts Count:** Number of items requiring urgent replenishment.
  - **Business Health Summary:** A brief score/status text based on inventory risk and profit trends.
- **Interactive Visualizations:**
  - **Revenue and Profit Bar Chart:** Shows individual product metrics.
  - **Stock Levels vs Monthly Sales Chart:** Compares current stock with monthly sales to highlight depletion speeds.
  - **Category Performance Pie Chart:** Breakdown of product counts or sales by category.

### Feature 2: Excel/CSV Upload Feature
A simple interface to drag-and-drop or upload business spreadsheets.
- **Accepted Formats:** `.csv`, `.xlsx`, `.xls`
- **Required Columns:**
  - `Product_Name`: Name of the item.
  - `Category`: Category of the product.
  - `Current_Stock`: Current units available in warehouse/shop.
  - `Monthly_Sales`: Number of units sold in the last 30 days.
  - `Cost_Price`: Unit wholesale/cost price.
  - `Selling_Price`: Unit retail/selling price.
  - `Supplier_Delay_Days`: Number of days it takes for a supplier to ship replacements.
  - `Customer_Rating`: Average rating of the product from customers.

### Feature 3: Inventory Intelligence Module
Analyzes inventory data to prevent stockouts and overstocking.
- **Low Stock Alerts:** Identifies products with low supply relative to demand (e.g., supply lasting less than 2 weeks, or current stock under a threshold).
- **Overstock Warnings:** Identifies items sitting on shelves for too long (e.g., supply lasting more than 3 months) which ties up business capital.
- **Restock Priority & supplier delay factoring:** Flagging items where supplier delay is high and stock is low.
- **Automatic Alerts:** Human-readable explanations, e.g., *"Cooking Oil stock is low because monthly demand is high (45 units). Restocking is recommended."*

### Feature 4: Sales Analysis Module
Provides analytical performance data of the store's inventory.
- **Revenue & Profit calculations:** Calculates profit for each item (`(Selling_Price - Cost_Price) * Monthly_Sales`).
- **Best-Selling Products:** Highlights top-performing products by sales.
- **Low-Performing Products:** Highlights items with very low sales or negative profits.

### Feature 5: AI Business Copilot
An interactive conversational interface allowing business owners to talk to their data.
- **Chat Interface:** Chat bubbles for the user and the assistant.
- **Suggested Prompt Chips:** "How can I improve my profits?", "Which products have the worst supplier delays?", "Show me a restocking plan."
- **Contextual Awareness:** Gemini API utilizes the uploaded spreadsheet data to answer queries accurately.

### Feature 6: AI Report Generator
A structured summary of the business operations.
- **Sections:**
  1. Executive Business Summary
  2. Main Problems & Risks Detected (Stockouts, low margin items)
  3. Actionable Recommendations (Restock schedules, pricing modifications)
  4. Future Action Items Checklist
- **Exporting:** Printable PDF/HTML document format for archiving.

## 2. User Experience Flow
1. **Application Launch:** The user opens the dashboard and is prompted to upload a file (with sample data download available).
2. **File Upload:** User uploads their CSV or Excel sheet.
3. **Data Analysis:** The server analyzes the file and updates dashboard counts and Chart.js visualizations.
4. **AI Recommendation:** Gemini generates high-level business suggestions displayed directly on the screen.
5. **Interactive Copilot Chat:** User chats with the AI to ask follow-up questions.
6. **Report Generation:** User clicks "Generate Report" to view a consolidated layout of their business operations.
