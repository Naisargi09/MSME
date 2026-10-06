import os
import sys
import pandas as pd
import numpy as np

# Reconfigure stdout to support unicode symbols like ₹ on Windows CMD/Powershell
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

def load_and_clean_data(file_path):
    """
    Loads Excel or CSV file into a Pandas DataFrame and cleans the data.
    Ensures standard columns are present, trims whitespaces, and sets sensible defaults.
    """
    # 1. Detect file type and load
    _, file_extension = os.path.splitext(file_path)
    file_extension = file_extension.lower()
    
    try:
        if file_extension == '.csv':
            df = pd.read_csv(file_path)
        elif file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file format. Please upload a CSV or Excel (.xlsx, .xls) file.")
    except Exception as e:
        raise ValueError(f"Error reading file: {str(e)}")

    # 2. Clean column names (strip whitespace and handle common capitalization)
    df.columns = [col.strip() for col in df.columns]
    
    # Map common column variations if user has slightly different naming
    rename_mapping = {}
    for col in df.columns:
        normalized = col.lower().replace(" ", "_")
        if normalized == 'product_name' and col != 'Product_Name':
            rename_mapping[col] = 'Product_Name'
        elif normalized == 'category' and col != 'Category':
            rename_mapping[col] = 'Category'
        elif normalized == 'current_stock' and col != 'Current_Stock':
            rename_mapping[col] = 'Current_Stock'
        elif normalized == 'monthly_sales' and col != 'Monthly_Sales':
            rename_mapping[col] = 'Monthly_Sales'
        elif normalized == 'cost_price' and col != 'Cost_Price':
            rename_mapping[col] = 'Cost_Price'
        elif normalized == 'selling_price' and col != 'Selling_Price':
            rename_mapping[col] = 'Selling_Price'
        elif normalized in ['supplier_delay', 'supplier_delay_days'] and col != 'Supplier_Delay_Days':
            rename_mapping[col] = 'Supplier_Delay_Days'
        elif normalized in ['rating', 'customer_rating'] and col != 'Customer_Rating':
            rename_mapping[col] = 'Customer_Rating'
            
    if rename_mapping:
        df.rename(columns=rename_mapping, inplace=True)

    # 3. Validate Required Columns
    required_cols = [
        'Product_Name', 'Category', 'Current_Stock', 'Monthly_Sales',
        'Cost_Price', 'Selling_Price', 'Supplier_Delay_Days', 'Customer_Rating'
    ]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required column(s): {', '.join(missing_cols)}")

    # 4. Data cleaning
    # Drop rows where Product Name is missing
    df.dropna(subset=['Product_Name'], inplace=True)
    df['Product_Name'] = df['Product_Name'].astype(str).str.strip()
    
    # Category default
    df['Category'] = df['Category'].fillna('Uncategorized').astype(str).str.strip()
    
    # Fill numerical nulls and coerce types
    numeric_columns = {
        'Current_Stock': 0,
        'Monthly_Sales': 0,
        'Cost_Price': 0.0,
        'Selling_Price': 0.0,
        'Supplier_Delay_Days': 0,
        'Customer_Rating': 5.0
    }
    for col, default_val in numeric_columns.items():
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(default_val)
        if isinstance(default_val, int):
            df[col] = df[col].astype(int)
        else:
            df[col] = df[col].astype(float)
            
    return df

def calculate_business_metrics(df):
    """
    Computes key financial and operational metrics from the cleaned DataFrame.
    """
    # 1. Product level math
    # Profit Margin = (Selling_Price - Cost_Price) * Monthly_Sales
    df['Unit_Profit'] = df['Selling_Price'] - df['Cost_Price']
    df['Monthly_Revenue'] = df['Monthly_Sales'] * df['Selling_Price']
    df['Monthly_Cost'] = df['Monthly_Sales'] * df['Cost_Price']
    df['Monthly_Profit'] = df['Monthly_Sales'] * df['Unit_Profit']
    
    # Profit Margin % (avoid divide by zero)
    df['Profit_Margin_Pct'] = np.where(
        df['Selling_Price'] > 0, 
        (df['Unit_Profit'] / df['Selling_Price']) * 100, 
        0.0
    )

    # 2. Aggregates
    total_revenue = float(df['Monthly_Revenue'].sum())
    total_cost = float(df['Monthly_Cost'].sum())
    total_profit = total_revenue - total_cost
    total_products = int(df['Product_Name'].nunique())
    
    avg_profit_margin = float(df['Profit_Margin_Pct'].mean()) if total_products > 0 else 0.0

    # 3. Product Lists (Sorted)
    # Best-selling products (sorted by revenue or sales)
    best_sellers = df.sort_values(by='Monthly_Sales', ascending=False).head(5)[
        ['Product_Name', 'Category', 'Monthly_Sales', 'Monthly_Revenue', 'Monthly_Profit']
    ].to_dict(orient='records')

    # Low-performing products (sorted by monthly sales, or negative/low profit)
    low_performers = df.sort_values(by='Monthly_Sales', ascending=True).head(5)[
        ['Product_Name', 'Category', 'Monthly_Sales', 'Monthly_Revenue', 'Monthly_Profit']
    ].to_dict(orient='records')

    # Business Health Rating calculation
    # We rank health based on low stock ratio and profit margins
    health_score = 100
    low_stock_count = len(df[df['Current_Stock'] < (df['Monthly_Sales'] / 2)])
    if total_products > 0:
        low_stock_ratio = low_stock_count / total_products
        health_score -= (low_stock_ratio * 40)  # penalize high out-of-stock risk
    
    negative_profit_count = len(df[df['Unit_Profit'] < 0])
    if total_products > 0:
        neg_ratio = negative_profit_count / total_products
        health_score -= (neg_ratio * 60)  # penalize negative margins heavily

    health_score = max(0, min(100, health_score))
    if health_score >= 80:
        health_summary = "Healthy"
    elif health_score >= 50:
        health_summary = "Moderate Risk"
    else:
        health_summary = "Critical Attention Needed"

    return {
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'total_profit': total_profit,
        'total_products': total_products,
        'avg_profit_margin': avg_profit_margin,
        'health_score': health_score,
        'health_summary': health_summary,
        'best_sellers': best_sellers,
        'low_performers': low_performers
    }

def analyze_inventory(df):
    """
    Analyzes stock levels and generates alerts for low stock, overstock, and fast-moving items.
    """
    alerts = []
    
    # Calculate days of inventory coverage (assuming 30 days in a month)
    # Average daily sales = Monthly_Sales / 30
    df['Avg_Daily_Sales'] = df['Monthly_Sales'] / 30.0
    
    # Coverage days: Current_Stock / Avg_Daily_Sales (handle zero sales)
    df['Stock_Coverage_Days'] = np.where(
        df['Avg_Daily_Sales'] > 0,
        df['Current_Stock'] / df['Avg_Daily_Sales'],
        999.0 # Infinity coverage if no sales
    )

    # 1. Low Stock Alerts (Stock cover < 15 days or stock < 10 and sales > 0)
    low_stock_mask = (df['Stock_Coverage_Days'] < 15) & (df['Monthly_Sales'] > 0) | ((df['Current_Stock'] < 10) & (df['Monthly_Sales'] > 5))
    low_stock_df = df[low_stock_mask]
    for _, row in low_stock_df.iterrows():
        # Check if supplier delay compounds the issue
        supplier_risk = ""
        if row['Supplier_Delay_Days'] > 5:
            supplier_risk = f" WARNING: Supplier takes {row['Supplier_Delay_Days']} days to ship."
            
        alerts.append({
            'product': row['Product_Name'],
            'category': row['Category'],
            'type': 'Low Stock',
            'severity': 'high' if row['Current_Stock'] <= 3 else 'medium',
            'message': f"{row['Product_Name']} is running low ({int(row['Current_Stock'])} in stock). Monthly sales are {int(row['Monthly_Sales'])} units (approx. {int(row['Stock_Coverage_Days'])} days of supply left). Restocking is recommended.{supplier_risk}"
        })

    # 2. Overstock Warnings (Stock cover > 90 days and stock > 20)
    overstock_mask = (df['Stock_Coverage_Days'] > 90) & (df['Current_Stock'] > 20)
    overstock_df = df[overstock_mask]
    for _, row in overstock_df.iterrows():
        alerts.append({
            'product': row['Product_Name'],
            'category': row['Category'],
            'type': 'Overstock',
            'severity': 'low',
            'message': f"{row['Product_Name']} is overstocked with {int(row['Current_Stock'])} units, representing over {int(row['Stock_Coverage_Days'])} days of stock. This ties up capital. Consider running a discount or promotion."
        })

    # 3. Fast-Moving High Demand items (Top 25% of sales volume)
    if not df.empty:
        sales_threshold = df['Monthly_Sales'].quantile(0.75)
        # Only label as fast-moving if sales are significant (> 15 units/month)
        fast_moving_mask = (df['Monthly_Sales'] >= max(sales_threshold, 15))
        fast_moving_df = df[fast_moving_mask]
        for _, row in fast_moving_df.iterrows():
            # Only add to alerts if they are not already flagged for low stock to avoid alert fatigue
            if row['Product_Name'] not in [a['product'] for a in alerts if a['type'] == 'Low Stock']:
                alerts.append({
                    'product': row['Product_Name'],
                    'category': row['Category'],
                    'type': 'Fast Moving',
                    'severity': 'info',
                    'message': f"{row['Product_Name']} is selling rapidly with {int(row['Monthly_Sales'])} units sold this month. Current stock is {int(row['Current_Stock'])}."
                })
                
    # Sort alerts: high severity first
    severity_order = {'high': 0, 'medium': 1, 'low': 2, 'info': 3}
    alerts.sort(key=lambda x: severity_order.get(x['severity'], 4))

    return alerts

if __name__ == '__main__':
    # Test script standalone using the sample CSV we created
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sample_csv_path = os.path.abspath(os.path.join(script_dir, "..", "MSME_sample_data.csv"))
    
    if os.path.exists(sample_csv_path):
        print(f"Testing calculations on sample dataset: {sample_csv_path}")
        df = load_and_clean_data(sample_csv_path)
        metrics = calculate_business_metrics(df)
        alerts = analyze_inventory(df)
        
        print("\n--- Summary Metrics ---")
        print(f"Total Revenue: ₹{metrics['total_revenue']:.2f}")
        print(f"Total Cost: ₹{metrics['total_cost']:.2f}")
        print(f"Total Profit: ₹{metrics['total_profit']:.2f}")
        print(f"Total Products: {metrics['total_products']}")
        print(f"Average Profit Margin: {metrics['avg_profit_margin']:.2f}%")
        print(f"Business Health Score: {metrics['health_score']:.1f}/100 ({metrics['health_summary']})")
        
        print("\n--- Alerts ({}) ---".format(len(alerts)))
        for a in alerts[:5]:
            print(f"[{a['type']} - {a['severity'].upper()}] {a['message']}")
    else:
        print(f"Sample data file not found at: {sample_csv_path}")
