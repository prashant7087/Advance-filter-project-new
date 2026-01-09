from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
import tempfile
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Enable CORS for all origins
CORS(app)

# Use /tmp for Vercel serverless functions
UPLOAD_FOLDER = tempfile.gettempdir()

# Import measurement logic
from measurement_logic import analyze_image


@app.route('/')
def home():
    return jsonify({'message': 'Welcome to Lenskart AI Fitter API!'})


@app.route('/health')
def health():
    return jsonify({'message': 'API is working fine on Vercel!'})


# ========================================
# HARDCODED CREDENTIALS
# ========================================
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "admin@123"


@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    """
    Validate login credentials.
    Expects JSON: { "email": "...", "password": "..." }
    """
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        app.logger.info(f"Login attempt for email: {email}")
        
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            # Generate a simple session token
            session_token = str(uuid.uuid4())
            app.logger.info(f"Login successful for {email}")
            return jsonify({
                'success': True,
                'token': session_token,
                'message': 'Login successful'
            }), 200
        else:
            app.logger.warning(f"Login failed for {email}")
            return jsonify({
                'success': False,
                'error': 'Invalid email or password'
            }), 401
            
    except Exception as e:
        app.logger.error(f"Login error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/save-user', methods=['POST', 'OPTIONS'])
def save_user():
    """
    Save user information (name, phone).
    Expects JSON: { "name": "...", "phone": "..." }
    Returns: { "success": true, "user_id": "..." }
    """
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        
        if not name or not phone:
            return jsonify({'success': False, 'error': 'Name and phone are required'}), 400
        
        app.logger.info(f"Saving user: {name}, {phone}")
        
        # For Vercel serverless, generate a UUID (no persistent DB in this simple version)
        user_id = str(uuid.uuid4())
        app.logger.info(f"User saved with ID: {user_id}")
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'message': 'User saved successfully'
        }), 200
        
    except Exception as e:
        app.logger.error(f"Save user error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/history', methods=['GET', 'OPTIONS'])
def get_history():
    """
    Fetch measurement history.
    For Vercel serverless, returns empty history (no persistent storage).
    """
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        # For Vercel serverless without persistent DB, return empty history
        app.logger.info("History endpoint called - returning empty history (serverless mode)")
        return jsonify({
            'success': True,
            'history': [],
            'count': 0,
            'message': 'History not available in serverless mode'
        }), 200
        
    except Exception as e:
        app.logger.error(f"History fetch error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/process_image', methods=['POST', 'OPTIONS'])
def process_image():
    """
    Endpoint to process a single image file for optical measurements.
    Expects a multipart form with 'image' and 'frame_width_mm'.
    """
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 200
    
    if 'image' not in request.files:
        app.logger.warning("Request received without image file.")
        return jsonify({'error': 'Missing image file'}), 400
    
    if 'frame_width_mm' not in request.form:
        app.logger.warning("Request received without frame_width_mm.")
        return jsonify({'error': 'Missing frame_width_mm parameter'}), 400

    image_file = request.files['image']
    
    try:
        frame_width_mm = float(request.form['frame_width_mm'])
    except ValueError:
        app.logger.error("Invalid format for frame_width_mm.")
        return jsonify({'error': 'frame_width_mm must be a valid number'}), 400

    filename = str(uuid.uuid4()) + '.jpg'
    image_path = os.path.join(UPLOAD_FOLDER, filename)
    image_file.save(image_path)
    app.logger.info(f"Image saved to {image_path}")

    try:
        app.logger.info(f"Analyzing image with frame width: {frame_width_mm}mm")
        measurements, landmarks, frame_dims = analyze_image(image_path, frame_width_mm=frame_width_mm)
        response_data = {
            "measurements": measurements,
            "landmarks": landmarks,
            "frameDimensions": frame_dims
        }
        return jsonify(response_data)
    except Exception as e:
        app.logger.error(f"Analysis failed for {image_path}: {e}", exc_info=True)
        return jsonify({'error': f"Analysis Failed: {e}"}), 500
    finally:
        if os.path.exists(image_path):
            os.remove(image_path)
            app.logger.info(f"Cleaned up temporary file: {image_path}")


if __name__ == '__main__':
    app.run(debug=True)
