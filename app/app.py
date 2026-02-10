from flask import Flask, request, jsonify
from flask_compress import Compress
from app.api_logic import process_request
import os

app = Flask(__name__)
Compress(app)

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "GrowMate Soil Advisory"}), 200

@app.route('/api/advisory', methods=['POST'])
def advisory():
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"status": "error", "message": "No JSON payload provided"}), 400
            
        result = process_request(data)
        
        status_code = 200
        if result.get("status") == "error":
            status_code = 400
            
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
