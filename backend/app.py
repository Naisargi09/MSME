import os
import sys
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# Ensure backend directory is in the system path for relative imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_analysis import load_and_clean_data, calculate_business_metrics, analyze_inventory
import ai_engine

app = Flask(__name__, static_folder='../frontend', static_url_path='')

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB Upload Limit

# Global in-memory cache for state persistence (ideal for local single-user execution)
GLOBAL_STATE = {
    'df': None,
    'metrics': None,
    'alerts': None,
    'products_summary_str': "",
    'products_list': [],
    'ai_recommendations': ""
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv', 'xlsx', 'xls'}

@app.route('/')
def index():
    """Serves the main frontend page."""
    return app.send_static_file('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    Accepts CSV/Excel uploads, runs analysis, caches data, 
    and triggers Gemini AI to generate initial business recommendations.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request.'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected.'}), 400
        
    if not allowed_file(file.filename):
        return jsonify({'error': 'Unsupported file type. Please upload a CSV or Excel file.'}), 400

    try:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # 1. Clean and load data
        df = load_and_clean_data(file_path)
        
        # 2. Compute sales and inventory metrics
        metrics = calculate_business_metrics(df)
        alerts = analyze_inventory(df)
        
        # 3. Create products summary representation for AI prompt context
        products_subset = df[[
            'Product_Name', 'Category', 'Current_Stock', 
            'Monthly_Sales', 'Cost_Price', 'Selling_Price', 
            'Supplier_Delay_Days', 'Customer_Rating', 'Unit_Profit', 'Profit_Margin_Pct'
        ]]
        
        products_list = products_subset.to_dict(orient='records')
        
        # Build text description of products catalog
        prod_lines = []
        for p in products_list:
            prod_lines.append(
                f"- {p['Product_Name']} (Category: {p['Category']}): "
                f"Stock={p['Current_Stock']}, Monthly Sales={p['Monthly_Sales']}, "
                f"Price=${p['Selling_Price']:.2f}, Margin={p['Profit_Margin_Pct']:.1f}%, "
                f"Supplier Lead Time={p['Supplier_Delay_Days']} days, Rating={p['Customer_Rating']:.1f}/5"
            )
        products_summary_str = "\n".join(prod_lines)
        
        # 4. Generate AI Recommendations
        ai_recommendations = ai_engine.generate_ai_recommendation(
            metrics, alerts, products_summary_str
        )
        
        # 5. Cache state in global object
        GLOBAL_STATE['df'] = df
        GLOBAL_STATE['metrics'] = metrics
        GLOBAL_STATE['alerts'] = alerts
        GLOBAL_STATE['products_summary_str'] = products_summary_str
        GLOBAL_STATE['products_list'] = products_list
        GLOBAL_STATE['ai_recommendations'] = ai_recommendations
        
        # Clean up uploaded file
        try:
            os.remove(file_path)
        except Exception:
            pass
            
        return jsonify({
            'success': True,
            'filename': filename,
            'metrics': metrics,
            'alerts': alerts,
            'products': products_list,
            'ai_recommendations': ai_recommendations
        })

    except Exception as e:
        print(f"Error during file processing: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Processes chat prompts from the AI Business Copilot interface,
    supplying active business data as context.
    """
    data = request.json or {}
    user_message = data.get('message', '').strip()
    chat_history = data.get('history', [])

    if not user_message:
        return jsonify({'error': 'Message is empty.'}), 400

    if GLOBAL_STATE['metrics'] is None:
        return jsonify({
            'reply': "Please upload your Excel/CSV business spreadsheet first so I can analyze your sales and inventory data!"
        })

    try:
        reply = ai_engine.chatbot_response(
            user_message,
            chat_history,
            GLOBAL_STATE['metrics'],
            GLOBAL_STATE['alerts'],
            GLOBAL_STATE['products_summary_str']
        )
        return jsonify({'reply': reply})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/state', methods=['GET'])
def get_state():
    """Returns cached state if page is refreshed."""
    if GLOBAL_STATE['metrics'] is None:
        return jsonify({'loaded': False})
        
    return jsonify({
        'loaded': True,
        'metrics': GLOBAL_STATE['metrics'],
        'alerts': GLOBAL_STATE['alerts'],
        'products': GLOBAL_STATE['products_list'],
        'ai_recommendations': GLOBAL_STATE['ai_recommendations']
    })

@app.route('/api/reset', methods=['POST'])
def reset_state():
    """Resets the cached business data."""
    for key in GLOBAL_STATE.keys():
        GLOBAL_STATE[key] = None
    return jsonify({'success': True})

if __name__ == '__main__':
    # Set default port to 5000 or fetch from env
    port = int(os.getenv("PORT", 5000))
    # Run server locally
    app.run(host='0.0.0.0', port=port, debug=True)
