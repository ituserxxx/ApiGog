from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

app = Flask(__name__)
CORS(app)


def running_payload():
    return {
        'message': 'ApiGog Flask API Server',
        'status': 'running'
    }



@app.route('/api')
def api_entry():
    return jsonify(running_payload()), 200

@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'ApiGog API'
    }), 200

if __name__ == '__main__':
    app.run(
        debug=os.getenv('DEBUG', True),
        port=os.getenv('PORT', 5000),
        host='0.0.0.0'
    )
