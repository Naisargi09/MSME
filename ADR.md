# Architecture Decision Record (ADR)

## Project Name
MSME AI Operations Copilot

## 1. Frontend Technologies
- **Technology:** HTML5, CSS3 (Vanilla), JavaScript (ES6+), Chart.js (via CDN).
- **Reason:**
  - **Zero Build Step:** Using vanilla JS and CSS avoids compile steps (like Webpack/Vite), keeping the project fast, easy to run, and highly accessible to beginners or hackathon judges.
  - **Visuals:** Custom Vanilla CSS allows complete control over glassmorphism effects, shadows, and smooth layout grids, resulting in a premium custom aesthetic.
  - **Charts:** Chart.js is lightweight, highly configurable, and provides clean interactive tooltips and responsiveness out-of-the-box.

## 2. Backend Technologies
- **Technology:** Python, Flask, `python-dotenv`.
- **Reason:**
  - **Python API Ecosystem:** Python is the standard language for data processing and AI.
  - **Flask:** Flask provides a lightweight, clean web framework to create API endpoints and serve static frontend folders simultaneously. It has almost no boilerplate, making it easy to understand and debug.

## 3. Data Processing
- **Technology:** Pandas (`pandas`), Excel Parser (`openpyxl`).
- **Reason:**
  - **Data manipulation:** Pandas handles Excel and CSV sheets efficiently. It allows simple aggregations, sorting, and indexing with clean methods (`sum()`, `mean()`, filtering query statements).
  - **Robust CSV parsing:** Handles variations in separator tokens, encodings, and missing values gracefully.

## 4. AI Model
- **Model:** Google Gemini API (`google-generativeai` SDK).
- **Reason:**
  - **Speed & Context:** Gemini models offer rapid response times and large context windows, enabling us to dump the aggregated metrics of the business directly into the system prompt for accurate reasoning.
  - **Practical Advice:** Gemini excels at roleplay as a friendly, professional virtual advisor.
