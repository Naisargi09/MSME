import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

is_api_key_configured = False
SELECTED_MODEL_NAME = "gemini-3.5-flash"  # default fallback
DETECTED_AVAILABLE_MODELS = []

def configure_api_if_needed():
    """
    Checks if Gemini API is configured. If not, reloads the environment file (.env) 
    with override=True and configures the SDK. This allows updating the API key
    without restarting the Flask web server.
    It also queries the model registry to select the best available Flash model.
    """
    global is_api_key_configured, SELECTED_MODEL_NAME, DETECTED_AVAILABLE_MODELS
    if is_api_key_configured:
        return True
        
    # Force reload of dotenv variables
    load_dotenv(override=True)
    
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key and api_key != "your_gemini_api_key_here":
        try:
            genai.configure(api_key=api_key)
            is_api_key_configured = True
            
            # Dynamically detect the highest priority Flash/Pro model available
            try:
                available_models = [m.name.replace("models/", "") for m in genai.list_models()]
                priority_list = [
                    'gemini-3.5-flash',
                    'gemini-2.5-flash',
                    'gemini-2.0-flash',
                    'gemini-flash-latest',
                    'gemini-1.5-flash',
                    'gemini-pro-latest'
                ]
                DETECTED_AVAILABLE_MODELS = [m for m in priority_list if m in available_models]
                if DETECTED_AVAILABLE_MODELS:
                    SELECTED_MODEL_NAME = DETECTED_AVAILABLE_MODELS[0]
                    print(f"Dynamically detected available models: {DETECTED_AVAILABLE_MODELS}")
                    print(f"Selected primary active model: {SELECTED_MODEL_NAME}")
            except Exception as list_err:
                print(f"Could not query model list: {list_err}. Defaulting to {SELECTED_MODEL_NAME}")

            print("Successfully configured Gemini API dynamically.")
            return True
        except Exception as e:
            print(f"Warning: Failed to configure Gemini API dynamically: {e}")
    return False

# Perform initial configuration check on startup
configure_api_if_needed()

def get_gemini_model():
    """
    Returns the configured GenerativeModel instance using the dynamically selected model.
    """
    if not configure_api_if_needed():
        return None
    try:
        return genai.GenerativeModel(SELECTED_MODEL_NAME)
    except Exception as e:
        print(f"Error initializing Gemini model '{SELECTED_MODEL_NAME}': {e}")
        return None

def generate_ai_recommendation(metrics, alerts, products_summary):
    """
    Sends processed business metrics and inventory alerts to Gemini to generate
    a comprehensive business advisory report.
    """
    system_prompt = (
        "You are an expert MSME Business Advisor and Virtual Operations Manager.\n"
        "Your task is to analyze the provided MSME business metrics and inventory alerts,\n"
        "then write a structured operations report that is highly practical, professional, and easy for a local shop owner to implement.\n\n"
        "Ensure your output is structured in clean Markdown with the following exact sections:\n"
        "1. ## Executive Business Summary - (Overall analysis of revenue, profit margins, and health)\n"
        "2. ## Key Operations Risks & Problems - (Detailing specific stockout risks, overstock issues, or supplier delay issues)\n"
        "3. ## Actionable Recommendations - (Direct, practical recommendations for ordering, pricing, or clearances)\n"
        "4. ## Future Action Items Checklist - (A list of 4-5 quick checklists the owner should do this week)\n"
    )

    data_context = f"""
    BUSINESS DATA SUMMARY:
    - Total Revenue: ₹{metrics['total_revenue']:.2f}
    - Total Cost: ₹{metrics['total_cost']:.2f}
    - Total Profit: ₹{metrics['total_profit']:.2f}
    - Average Profit Margin: {metrics['avg_profit_margin']:.2f}%
    - Unique Products: {metrics['total_products']}
    - Business Health: {metrics['health_summary']} (Score: {metrics['health_score']:.1f}/100)

    INVENTORY ALERTS DETECTED:
    {chr(10).join([f"- [{a['type']}] {a['message']}" for a in alerts])}

    PRODUCT DATA DETAILS:
    {products_summary}
    """

    if not configure_api_if_needed():
        return get_mock_recommendations(metrics, alerts)

    global SELECTED_MODEL_NAME, DETECTED_AVAILABLE_MODELS
    models_to_try = list(DETECTED_AVAILABLE_MODELS)
    if SELECTED_MODEL_NAME not in models_to_try and SELECTED_MODEL_NAME:
        models_to_try.insert(0, SELECTED_MODEL_NAME)
    if not models_to_try:
        models_to_try = [SELECTED_MODEL_NAME]

    last_error = None
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            prompt = f"{system_prompt}\n\nHere is the business data to analyze:\n{data_context}"
            response = model.generate_content(prompt)
            SELECTED_MODEL_NAME = model_name  # cache successful model selection
            return response.text
        except Exception as e:
            last_error = e
            err_str = str(e).lower()
            if "429" in err_str or "quota" in err_str or "exhausted" in err_str:
                print(f"Gemini API call failed for model '{model_name}' due to quota limits: {e}. Trying next available model...")
                continue
            else:
                print(f"Gemini API call failed for model '{model_name}': {e}. Trying next available model...")
                continue

    print(f"Gemini API call failed for all models. Last error: {last_error}. Falling back to rule-based analysis.")
    return get_mock_recommendations(metrics, alerts, error_msg=str(last_error))

def chatbot_response(user_message, chat_history, metrics, alerts, products_summary):
    """
    Generates a conversational response for the business copilot chat.
    Injects business data as the conversation context.
    """
    system_context = (
        f"You are the MSME AI Operations Copilot, an AI assistant built specifically for this small business.\n"
        f"You have access to their current business metrics, inventory status, and sales figures.\n"
        f"Answer the user's questions about their business operations, inventory, restocking, and profits.\n"
        f"Be encouraging, business-savvy, and highly specific. Refer to actual products from their catalog in your answers.\n\n"
        f"CURRENT DATA OVERVIEW:\n"
        f"- Total Revenue: ₹{metrics['total_revenue']:.2f}\n"
        f"- Total Profit: ₹{metrics['total_profit']:.2f}\n"
        f"- Average Margin: {metrics['avg_profit_margin']:.2f}%\n"
        f"- Health: {metrics['health_summary']}\n"
        f"- Key Alerts: {', '.join([a['product'] + ' (' + a['type'] + ')' for a in alerts[:5]])}\n\n"
        f"PRODUCT CATALOG DETAILS:\n{products_summary}\n\n"
        f"Instructions:\n"
        f"1. Keep responses concise and focused (under 150 words).\n"
        f"2. Suggest concrete solutions (e.g. 'Restock Basmati Rice', 'Offer discount on Detergent').\n"
        f"3. If the user asks general questions, guide them to their business data.\n"
    )

    if not configure_api_if_needed():
        return get_mock_chat_reply(user_message, metrics, alerts)

    global SELECTED_MODEL_NAME, DETECTED_AVAILABLE_MODELS
    models_to_try = list(DETECTED_AVAILABLE_MODELS)
    if SELECTED_MODEL_NAME not in models_to_try and SELECTED_MODEL_NAME:
        models_to_try.insert(0, SELECTED_MODEL_NAME)
    if not models_to_try:
        models_to_try = [SELECTED_MODEL_NAME]

    last_error = None
    for model_name in models_to_try:
        try:
            # Instantiate the model with system instructions directly
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_context
            )
            
            # Build chat structure with history
            contents = []
            
            # Add conversation history
            for msg in chat_history:
                role = "user" if msg['sender'] == 'user' else "model"
                contents.append({"role": role, "parts": [msg['text']]})
                
            # Add final message
            contents.append({"role": "user", "parts": [user_message]})
            
            response = model.generate_content(contents)
            SELECTED_MODEL_NAME = model_name  # cache successful model selection
            return response.text
        except Exception as e:
            last_error = e
            err_str = str(e).lower()
            if "429" in err_str or "quota" in err_str or "exhausted" in err_str:
                print(f"Gemini API chat failed for model '{model_name}' due to quota limits: {e}. Trying next available model...")
                continue
            else:
                print(f"Gemini API chat failed for model '{model_name}': {e}. Trying next available model...")
                continue

    print(f"Gemini API chat failed for all models. Last error: {last_error}. Falling back to rule-based chat.")
    return get_mock_chat_reply(user_message, metrics, alerts, error_msg=str(last_error))

def get_mock_recommendations(metrics, alerts, error_msg=None):
    """
    Generates high-quality fallback markdown recommendations if Gemini API is unavailable.
    """
    low_stock_items = [a['product'] for a in alerts if a['type'] == 'Low Stock']
    overstock_items = [a['product'] for a in alerts if a['type'] == 'Overstock']
    fast_items = [a['product'] for a in alerts if a['type'] == 'Fast Moving']

    api_warning = ""
    if not is_api_key_configured:
        api_warning = "> [!NOTE]\n> **Offline Simulation Mode:** Configure your `GEMINI_API_KEY` in the `.env` file to enable real Gemini AI analytics.\n\n"
    elif error_msg:
        api_warning = f"> [!WARNING]\n> **Gemini API Error:** ({error_msg}). Displaying rule-based fallback analytics.\n\n"

    report = f"""{api_warning}# Executive Business Summary
Your business health is currently classified as **{metrics['health_summary']}** (Score: **{metrics['health_score']:.1f}/100**).
- **Total Revenue:** ₹{metrics['total_revenue']:.2f}
- **Total Profit:** ₹{metrics['total_profit']:.2f}
- **Average Profit Margin:** {metrics['avg_profit_margin']:.2f}%
- **Total Active SKUs:** {metrics['total_products']} products

Overall, your store exhibits a solid sales velocity, but profits are heavily concentrated in a few high-margin products. We have identified specific inventory imbalances that, if resolved, can unlock additional cash flow and prevent customer dissatisfaction.

# Key Operations Risks & Problems
1. **Stockout Risks:** You have {len(low_stock_items)} item(s) running dangerously low on stock. These include: **{', '.join(low_stock_items) if low_stock_items else 'None'}**. If not restocked immediately, you stand to lose revenue to competitors.
2. **Capital Lockup (Overstock):** There are {len(overstock_items)} overstocked product(s) (such as **{', '.join(overstock_items) if overstock_items else 'None'}**). This stock represents capital tied up on shelves that is not generating active returns.
3. **Supplier Lead Time Delays:** Certain critical products face supplier delay averages of up to 5+ days, making re-ordering schedules highly sensitive.

# Actionable Recommendations
- **Prioritize Restocking:** Set up an immediate reorder for **{', '.join(low_stock_items[:3]) if low_stock_items else 'low-stock products'}**. Account for supplier delays by ordering at least 15 days of buffer stock.
- **Run Capital Clearance:** Implement a bundle deal (e.g., 'Buy 2 Get 1 Free') or a 15% discount on overstocked items: **{', '.join(overstock_items[:2]) if overstock_items else 'slow items'}** to free up working capital.
- **Adjust Margins:** Review products with margins below 15%. Consider slight price increases on popular goods that have high customer ratings (> 4.5) to boost bottom-line profits.

# Future Action Items Checklist
- [ ] Place replenishment order for **{low_stock_items[0] if low_stock_items else 'low stock items'}** today.
- [ ] Setup a 10% promotional discount for slow-moving **{overstock_items[0] if overstock_items else 'overstocked items'}**.
- [ ] Review supplier lead times and request faster dispatch channels for critical categories.
- [ ] Schedule a weekly inventory review using this dashboard tool.
"""
    return report

def get_mock_chat_reply(user_message, metrics, alerts, error_msg=None):
    """
    Returns simple rule-based responses to common user queries in offline mode.
    """
    msg = user_message.lower()
    low_stock = [a['product'] for a in alerts if a['type'] == 'Low Stock']
    overstock = [a['product'] for a in alerts if a['type'] == 'Overstock']
    
    if not is_api_key_configured:
        response = "I am operating in Offline Simulation Mode because the Gemini API key is not configured in the .env file. "
    elif error_msg:
        response = f"I am operating in Offline Mode because the Gemini API call failed: {error_msg}. "
    else:
        response = "I am operating in Offline Mode. "
    
    if "improve" in msg or "profit" in msg or "money" in msg:
        response += f"To improve your monthly profits of **₹{metrics['total_profit']:.2f}**, try: \n1. Promoting products with high margins.\n2. Reducing overstock of items like **{', '.join(overstock[:2]) if overstock else 'your slow items'}** by hosting a sale."
    elif "restock" in msg or "low stock" in msg or "order" in msg:
        if low_stock:
            response += f"You have **{len(low_stock)}** low stock items. I recommend restocking **{', '.join(low_stock[:3])}** immediately. Pay special attention to products with supplier delays!"
        else:
            response += "Great news! Your stock levels look stable across all active SKUs. No urgent restocking is required today."
    elif "overstock" in msg or "slow" in msg or "sales" in msg:
        if overstock:
            response += f"Items like **{', '.join(overstock[:3])}** are overstocked. Consider marking down their prices by 15-20% or bundling them with fast-moving items to clear shelf space."
        else:
            response += "You have no major overstock items. Your inventory velocity is well-balanced."
    else:
        response += f"Based on your data, your business has a revenue of **₹{metrics['total_revenue']:.2f}** and profit of **₹{metrics['total_profit']:.2f}**. Let me know if you want to know about restocking, low stock alerts, or improving profit margins!"
        
    return response
