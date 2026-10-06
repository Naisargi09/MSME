import urllib.request
import urllib.parse
import json
import os
import sys

# Reconfigure stdout to support unicode symbols like ₹ on Windows CMD/Powershell
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

def test_api():
    print("==================================================")
    print("       MSME AI Operations Copilot API Test        ")
    print("==================================================")
    
    base_url = "http://localhost:5000"
    
    # 1. Reset state
    print("1. Resetting server state...")
    reset_url = f"{base_url}/api/reset"
    req = urllib.request.Request(reset_url, method='POST')
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode())
            print(f"   Reset response: {res_data}")
            assert res_data.get('success') is True, "Reset failed"
    except Exception as e:
        print(f"Error resetting server: {e}")
        return False

    # 2. Upload file
    print("2. Uploading MSME_sample_data.csv...")
    upload_url = f"{base_url}/api/upload"
    csv_path = os.path.join(os.path.dirname(__file__), "MSME_sample_data.csv")
    
    # Construct multipart/form-data payload manually to avoid dependencies
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    with open(csv_path, 'rb') as f:
        file_content = f.read()
        
    part_header = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="MSME_sample_data.csv"\r\n'
        f"Content-Type: text/csv\r\n\r\n"
    ).encode('utf-8')
    part_footer = f"\r\n--{boundary}--\r\n".encode('utf-8')
    
    body = part_header + file_content + part_footer
    
    req = urllib.request.Request(
        upload_url,
        data=body,
        headers={
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'Content-Length': str(len(body))
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            print("   Upload successful!")
            
            # Assert metrics
            metrics = data['metrics']
            print("\n--- Calculated Metrics ---")
            print(f"   Total Revenue: ₹{metrics['total_revenue']:.2f} (Expected: ₹4,398.00)")
            print(f"   Total Profit: ₹{metrics['total_profit']:.2f} (Expected: ₹1,705.00)")
            print(f"   Total Products: {metrics['total_products']} (Expected: 15)")
            print(f"   Health Summary: {metrics['health_summary']} (Score: {metrics['health_score']:.1f}/100)")
            
            assert abs(metrics['total_revenue'] - 4398.00) < 0.01, "Revenue calculation incorrect"
            assert abs(metrics['total_profit'] - 1705.00) < 0.01, "Profit calculation incorrect"
            assert metrics['total_products'] == 15, "Product count incorrect"
            
            # Check alerts
            alerts = data['alerts']
            print(f"\n   Detected {len(alerts)} inventory alerts.")
            low_stock = [a for a in alerts if a['type'] == 'Low Stock']
            overstock = [a for a in alerts if a['type'] == 'Overstock']
            print(f"   Low Stock items: {[a['product'] for a in low_stock]}")
            print(f"   Overstock items: {[a['product'] for a in overstock]}")
            
            # Check recommendations
            recs = data['ai_recommendations']
            print("\n   AI recommendations generated successfully! Length:", len(recs))
            assert len(recs) > 100, "Recommendations content too short"
            
    except Exception as e:
        print(f"Error uploading and parsing file: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 3. Chat test
    print("\n3. Testing Chat Copilot API...")
    chat_url = f"{base_url}/api/chat"
    chat_payload = json.dumps({
        "message": "Which products should I restock first?",
        "history": []
    }).encode('utf-8')
    
    req = urllib.request.Request(
        chat_url,
        data=chat_payload,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            chat_data = json.loads(response.read().decode())
            reply = chat_data.get('reply')
            print("   Chat response received!")
            print(f"   Copilot response:\n{reply}\n")
            assert len(reply) > 20, "Chat response too short"
            
    except Exception as e:
        print(f"Error calling chat API: {e}")
        return False
        
    print("==================================================")
    print("        ALL API TESTS PASSED SUCCESSFULLY!        ")
    print("==================================================")
    return True

if __name__ == '__main__':
    test_api()
