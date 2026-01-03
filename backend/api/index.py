from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route('/')
def home():
    return jsonify({'message': 'Welcome to Lenskart AI Fitter API!'})


@app.route('/api/health')
def health():
    return jsonify({'message': 'API is working fine on Vercel!'})


@app.route('/api/process_image', methods=['POST', 'OPTIONS'])
def process_image():
    if request.method == 'OPTIONS':
        return '', 200
    
    # For now, return a test response to verify the route works
    return jsonify({
        'status': 'Route is working!',
        'note': 'Full processing will be added after route verification'
    })
