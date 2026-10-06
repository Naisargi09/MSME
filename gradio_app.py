import os
import sys
import gradio as gr
import pandas as pd
import matplotlib.pyplot as plt

# Ensure matplotlib runs without a GUI window (headless mode)
import matplotlib
matplotlib.use('Agg')

# Add backend folder to path for modules loading
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

import data_analysis
import ai_engine

# Reconfigure stdout to support unicode symbols like ₹ on Windows CMD/Powershell
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# Custom styling in HTML/CSS matching the dark-theme glassmorphism first dashboard
custom_css = """
body {
    background-color: #080c14 !important;
}
.kpi-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 20px;
}
.kpi-card {
    background: rgba(17, 24, 39, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 16px;
    display: flex;
    align-items: center;
    gap: 16px;
}
.kpi-icon {
    width: 48px;
    height: 48px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
}
.icon-blue { background: rgba(59, 130, 246, 0.15); color: #60a5fa; }
.icon-green { background: rgba(16, 185, 129, 0.15); color: #34d399; }
.icon-purple { background: rgba(139, 92, 246, 0.15); color: #a78bfa; }
.icon-amber { background: rgba(245, 158, 11, 0.15); color: #fbbf24; }
.kpi-info {
    display: flex;
    flex-direction: column;
}
.kpi-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #94a3b8;
}
.kpi-value {
    font-size: 22px;
    font-weight: 700;
    color: #f8fafc;
    margin: 2px 0;
}
.kpi-subtext {
    font-size: 11px;
    color: #94a3b8;
}
.alert-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
    max-height: 400px;
    overflow-y: auto;
}
.alert-card {
    padding: 14px;
    border-radius: 8px;
    border-left: 4px solid #ef4444;
    background: rgba(239, 68, 68, 0.03);
    border-top: 1px solid rgba(255, 255, 255, 0.04);
    border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    border-right: 1px solid rgba(255, 255, 255, 0.04);
}
.alert-card.medium { border-left-color: #f59e0b; background: rgba(245, 158, 11, 0.03); }
.alert-card.low { border-left-color: #0ea5e9; background: rgba(14, 165, 233, 0.03); }
.alert-card.info { border-left-color: #10b981; background: rgba(16, 185, 129, 0.03); }
.alert-title { font-weight: 600; font-size: 13px; color: #f8fafc; }
.alert-desc { font-size: 12px; color: #94a3b8; margin-top: 4px; }
"""

# Matplotlib chart helpers
def generate_revenue_profit_chart(df):
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 4.5), facecolor='#080c14')
    ax.set_facecolor('#080c14')
    
    products = df['Product_Name'].tolist()
    revenues = (df['Selling_Price'] * df['Monthly_Sales']).tolist()
    profits = ((df['Selling_Price'] - df['Cost_Price']) * df['Monthly_Sales']).tolist()
    
    x = range(len(products))
    width = 0.35
    
    ax.bar([i - width/2 for i in x], revenues, width, label='Monthly Revenue (₹)', color='#3b82f6', alpha=0.85)
    ax.bar([i + width/2 for i in x], profits, width, label='Monthly Profit (₹)', color='#10b981', alpha=0.85)
    
    ax.set_title('Revenue vs Profit per Product', fontsize=12, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(products, rotation=45, ha='right', fontsize=9, color='#94a3b8')
    ax.tick_params(axis='y', colors='#94a3b8', labelsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#1d2433')
    ax.spines['bottom'].set_color('#1d2433')
    ax.grid(axis='y', linestyle='--', alpha=0.1)
    ax.legend(facecolor='#080c14', edgecolor='none', labelcolor='#f8fafc')
    
    plt.tight_layout()
    return fig

def generate_stock_sales_chart(df):
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 4.5), facecolor='#080c14')
    ax.set_facecolor('#080c14')
    
    products = df['Product_Name'].tolist()
    stocks = df['Current_Stock'].tolist()
    sales = df['Monthly_Sales'].tolist()
    
    x = range(len(products))
    
    ax.plot(products, stocks, marker='o', color='#f59e0b', label='Current Stock (Units)', linewidth=2)
    ax.plot(products, sales, marker='s', color='#8b5cf6', label='Monthly Sales Volume (Units)', linewidth=2)
    
    ax.set_title('Stock Levels vs Sales Velocity', fontsize=12, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(products, rotation=45, ha='right', fontsize=9, color='#94a3b8')
    ax.tick_params(axis='y', colors='#94a3b8', labelsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#1d2433')
    ax.spines['bottom'].set_color('#1d2433')
    ax.grid(axis='y', linestyle='--', alpha=0.1)
    ax.legend(facecolor='#080c14', edgecolor='none', labelcolor='#f8fafc')
    
    plt.tight_layout()
    return fig

# Main processing handler
def process_uploaded_file(file):
    if file is None:
        return (
            "<p style='color: #94a3b8; text-align: center; padding: 20px;'>Please upload a CSV or Excel spreadsheet to generate analytics.</p>",
            None,
            None,
            "<p style='color: #94a3b8; text-align: center; padding: 20px;'>No inventory alerts to display.</p>",
            None,
            "Upload a business data file to view AI advisory insights.",
            {}, # metrics state
            [], # alerts state
            ""  # products summary state
        )
        
    try:
        # 1. Clean and parse
        df = data_analysis.load_and_clean_data(file.name)
        
        # 2. Computations
        metrics = data_analysis.calculate_business_metrics(df)
        alerts = data_analysis.analyze_inventory(df)
        
        # 3. Format dynamic HTML metrics
        kpi_html = f"""
        <div class="kpi-container">
            <div class="kpi-card">
                <div class="kpi-icon icon-blue">₹</div>
                <div class="kpi-info">
                    <span class="kpi-label">Monthly Revenue</span>
                    <div class="kpi-value">₹{metrics['total_revenue']:,.2f}</div>
                </div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon icon-green">📈</div>
                <div class="kpi-info">
                    <span class="kpi-label">Monthly Profit</span>
                    <div class="kpi-value">₹{metrics['total_profit']:,.2f}</div>
                    <span class="kpi-subtext">{metrics['avg_profit_margin']:.1f}% Avg Margin</span>
                </div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon icon-purple">📦</div>
                <div class="kpi-info">
                    <span class="kpi-label">Active SKUs</span>
                    <div class="kpi-value">{metrics['total_products']}</div>
                </div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon icon-amber">🩺</div>
                <div class="kpi-info">
                    <span class="kpi-label">Store Health</span>
                    <div class="kpi-value">{metrics['health_summary']}</div>
                    <span class="kpi-subtext">Score: {metrics['health_score']:.1f}/100</span>
                </div>
            </div>
        </div>
        """
        
        # 4. Generate Matplotlib Figures
        fig_rev = generate_revenue_profit_chart(df)
        fig_stock = generate_stock_sales_chart(df)
        
        # 5. Build Alerts HTML list
        alerts_html = '<div class="alert-list">'
        if not alerts:
            alerts_html += "<p style='color: #94a3b8; padding: 12px;'>No active alerts. Inventory levels are stable!</p>"
        else:
            for a in alerts:
                severity_class = a['severity']
                alerts_html += f"""
                <div class="alert-card {severity_class}">
                    <div class="alert-title">[{a['type'].upper()} - {a['severity'].upper()}] {a['product']}</div>
                    <div class="alert-desc">{a['message']}</div>
                </div>
                """
        alerts_html += '</div>'
        
        # 6. Format products summary string for AI advisory prompts
        products_subset = df[[
            'Product_Name', 'Category', 'Current_Stock', 
            'Monthly_Sales', 'Cost_Price', 'Selling_Price', 
            'Supplier_Delay_Days', 'Customer_Rating', 'Unit_Profit', 'Profit_Margin_Pct'
        ]]
        products_list = products_subset.to_dict(orient='records')
        
        prod_lines = []
        for p in products_list:
            prod_lines.append(
                f"- {p['Product_Name']} (Category: {p['Category']}): "
                f"Stock={p['Current_Stock']}, Monthly Sales={p['Monthly_Sales']}, "
                f"Price=₹{p['Selling_Price']:.2f}, Margin={p['Profit_Margin_Pct']:.1f}%, "
                f"Supplier Lead Time={p['Supplier_Delay_Days']} days, Rating={p['Customer_Rating']:.1f}/5"
            )
        products_summary_str = "\n".join(prod_lines)
        
        # 7. Generate Live Gemini operations recommendations
        ai_recommendations = ai_engine.generate_ai_recommendation(
            metrics, alerts, products_summary_str
        )
        
        # Cleaned display dataframe (hide analytical columns)
        display_cols = [
            'Product_Name', 'Category', 'Current_Stock', 'Monthly_Sales',
            'Cost_Price', 'Selling_Price', 'Supplier_Delay_Days', 'Customer_Rating'
        ]
        display_df = df[display_cols]
        
        return (
            kpi_html,
            fig_rev,
            fig_stock,
            alerts_html,
            display_df,
            ai_recommendations,
            metrics,
            alerts,
            products_summary_str
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_html = f"<div style='background: rgba(239,68,68,0.1); border: 1px solid #ef4444; border-radius: 8px; padding: 16px; color: #ef4444;'><strong>Error processing file:</strong> {str(e)}</div>"
        return (
            error_html,
            None,
            None,
            error_html,
            None,
            f"Failed to analyze spreadsheet content: {e}",
            {},
            [],
            ""
        )

# Chatbot handler logic
def chatbot_reply(message, history, metrics, alerts, products_summary):
    history = history or []
    if not metrics or not products_summary:
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": "Please upload your Excel/CSV business spreadsheet on the Dashboard tab first so I can analyze your sales and inventory data!"})
        return history
        
    # Format history to fit chatbot_response requirements
    formatted_history = []
    for msg in history:
        # Ignore initial greetings or systems messages that don't fit standard roles
        if msg.get("role") not in ["user", "assistant"]:
            continue
        sender = "user" if msg["role"] == "user" else "system"
        
        # Extract plain text content robustly from Gradio 6 message structure
        raw_content = msg.get("content", "")
        extracted_text = ""
        if isinstance(raw_content, str):
            extracted_text = raw_content
        elif isinstance(raw_content, list):
            # List of parts format: [{'text': '...', 'type': 'text'}, ...]
            text_parts = []
            for part in raw_content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(part.get("text", ""))
                elif isinstance(part, str):
                    text_parts.append(part)
            extracted_text = "".join(text_parts)
        elif isinstance(raw_content, dict):
            # Single part dict format
            if raw_content.get("type") == "text":
                extracted_text = raw_content.get("text", "")
            else:
                extracted_text = str(raw_content)
        else:
            extracted_text = str(raw_content)
            
        formatted_history.append({"sender": sender, "text": extracted_text})
        
    try:
        reply = ai_engine.chatbot_response(
            message, formatted_history, metrics, alerts, products_summary
        )
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": reply})
        return history
    except Exception as e:
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": f"Failed to communicate with AI Copilot: {e}"})
        return history

# Download Sample CSV
def download_sample_data():
    sample_data_path = os.path.join(os.path.dirname(__file__), "MSME_sample_data.csv")
    return sample_data_path

# Gradio Interface build
with gr.Blocks(title="MSME AI Operations Copilot") as demo:
    
    # State variables
    metrics_state = gr.State({})
    alerts_state = gr.State([])
    products_summary_state = gr.State("")
    
    # Header Area
    gr.HTML("""
    <div style="text-align: center; margin-bottom: 24px; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 16px;">
        <h1 style="font-family: 'Outfit', sans-serif; font-size: 28px; font-weight: 800; margin: 0; background: linear-gradient(135deg, #a78bfa 0%, #6366f1 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">MSME AI Operations Copilot</h1>
        <p style="color: #94a3b8; font-size: 14px; margin-top: 4px;">Convert raw spreadsheet metrics into automated insights, recommendations, and conversational strategies</p>
    </div>
    """)
    
    with gr.Tabs():
        # Tab 1: Dashboard
        with gr.Tab("Business Dashboard"):
            
            # Row 1: Upload & Controls
            with gr.Row():
                with gr.Column(scale=3):
                    file_input = gr.File(
                        label="Upload MSME Sales & Inventory Spreadsheet",
                        file_types=[".csv", ".xlsx", ".xls"]
                    )
                with gr.Column(scale=1):
                    download_btn = gr.Button("Download Sample CSV", variant="secondary")
                    sample_file_output = gr.File(label="Sample Data Download", visible=False)
                    download_btn.click(download_sample_data, inputs=[], outputs=[sample_file_output]).then(
                        lambda f: gr.update(visible=True), inputs=[sample_file_output], outputs=[sample_file_output]
                    )
            
            # Row 2: HTML KPI Summary Row (filled dynamically)
            kpis_panel = gr.HTML("<p style='color: #94a3b8; text-align: center; padding: 20px;'>Please upload a CSV or Excel spreadsheet to generate analytics.</p>")
            
            # Row 3: Visualization Charts
            with gr.Row():
                chart_rev_profit = gr.Plot(label="Revenue and Profit per Product")
                chart_stock_sales = gr.Plot(label="Stock Cover and Demand Velocity")
                
            # Row 4: Detailed tables & alerts
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### ⚠️ Inventory Alerts")
                    alerts_panel = gr.HTML("<p style='color: #94a3b8; text-align: center; padding: 20px;'>No inventory alerts to display.</p>")
                with gr.Column(scale=2):
                    gr.Markdown("### 📊 Product Database")
                    db_table = gr.Dataframe(interactive=False)
            
            # Row 5: AI Operations Report Card
            gr.Markdown("## 📋 AI Operations & Recommendations Report")
            report_panel = gr.Markdown("Upload a business data file to view AI advisory insights.")
            
            # Trigger file upload parsing
            file_input.change(
                process_uploaded_file,
                inputs=[file_input],
                outputs=[
                    kpis_panel,
                    chart_rev_profit,
                    chart_stock_sales,
                    alerts_panel,
                    db_table,
                    report_panel,
                    metrics_state,
                    alerts_state,
                    products_summary_state
                ]
            )

        # Tab 2: AI Business Copilot
        with gr.Tab("AI Business Copilot Chat"):
            gr.Markdown("### 🤖 Chat with your Virtual Operations Manager")
            chatbot = gr.Chatbot(
                label="Operations Advisor Chat History", 
                height=450,
                value=[{"role": "assistant", "content": "Hello! I am your virtual operations manager. Please upload your spreadsheet on the Dashboard tab, and I'll help you optimize your business!"}]
            )
            
            with gr.Row():
                chat_input = gr.Textbox(
                    placeholder="Ask about restocking priorities, margins, supplier delays, or clearance ideas...", 
                    scale=8,
                    container=False
                )
                chat_send = gr.Button("Send", variant="primary", scale=1)
                
            # Chips prompts helper row
            gr.Markdown("**Quick Prompts:**")
            with gr.Row():
                chip1 = gr.Button("Which products should I restock first?", size="sm")
                chip2 = gr.Button("How can I increase my monthly profit?", size="sm")
                chip3 = gr.Button("Tell me which products are overstocked.", size="sm")
                
            # Connect chat submission actions
            def handle_chip(chip_val, hist, m, a, p):
                new_hist = chatbot_reply(chip_val, hist, m, a, p)
                return new_hist, ""
                
            chat_input.submit(
                chatbot_reply,
                inputs=[chat_input, chatbot, metrics_state, alerts_state, products_summary_state],
                outputs=[chatbot]
            ).then(lambda: "", None, outputs=[chat_input])
            
            chat_send.click(
                chatbot_reply,
                inputs=[chat_input, chatbot, metrics_state, alerts_state, products_summary_state],
                outputs=[chatbot]
            ).then(lambda: "", None, outputs=[chat_input])
            
            # Connect chips buttons click actions
            chip1.click(
                handle_chip,
                inputs=[chip1, chatbot, metrics_state, alerts_state, products_summary_state],
                outputs=[chatbot, chat_input]
            )
            chip2.click(
                handle_chip,
                inputs=[chip2, chatbot, metrics_state, alerts_state, products_summary_state],
                outputs=[chatbot, chat_input]
            )
            chip3.click(
                handle_chip,
                inputs=[chip3, chatbot, metrics_state, alerts_state, products_summary_state],
                outputs=[chatbot, chat_input]
            )

# Run share=True to generate the public .gradio.live link
if __name__ == '__main__':
    demo.queue()
    # Share set to True creates the public tunnel link
    demo.launch(share=True, server_port=7860, theme=gr.themes.Default(), css=custom_css)
