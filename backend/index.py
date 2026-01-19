from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
import tempfile
import logging
from datetime import datetime

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Enable CORS for all origins
CORS(app)

# Use /tmp for Vercel serverless functions
UPLOAD_FOLDER = tempfile.gettempdir()

# Import measurement logic
from measurement_logic import analyze_image

# ========================================
# Database Helper Functions
# ========================================
def get_db_collections():
    """Safely get database collections. Returns None if DB not configured."""
    try:
        from database import get_users_collection, get_measurements_collection
        return get_users_collection(), get_measurements_collection()
    except Exception as e:
        app.logger.warning(f"Database not available: {e}")
        return None, None


@app.route('/')
def home():
    return jsonify({'message': 'Welcome to Lenskart AI Fitter API!'})


@app.route('/health')
def health():
    # Check database connection
    db_status = "not_configured"
    try:
        from database import test_connection
        if test_connection():
            db_status = "connected"
        else:
            db_status = "disconnected"
    except Exception:
        db_status = "not_configured"
    
    return jsonify({
        'message': 'API is working fine on Vercel!',
        'database': db_status
    })


# ========================================
# HARDCODED CREDENTIALS
# ========================================
ADMIN_EMAIL = "admin@pupilbot.site"
ADMIN_PASSWORD = "@d$miN####1"


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
        
        # Try to save to MongoDB
        users_collection, _ = get_db_collections()
        
        user_doc = {
            'name': name,
            'phone': phone,
            'created_at': datetime.utcnow()
        }
        
        if users_collection is not None:
            result = users_collection.insert_one(user_doc)
            user_id = str(result.inserted_id)
            app.logger.info(f"User saved to MongoDB with ID: {user_id}")
        else:
            # Fallback: generate a UUID if database isn't available
            user_id = str(uuid.uuid4())
            app.logger.warning(f"MongoDB not available. Using temp user_id: {user_id}")
        
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
    Fetch all measurements from MongoDB.
    Returns list of all tested users with their measurements.
    """
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        _, measurements_collection = get_db_collections()
        
        if measurements_collection is None:
            app.logger.warning("MongoDB not configured - returning empty history")
            return jsonify({
                'success': True,
                'history': [],
                'count': 0,
                'message': 'Database not configured'
            }), 200
        
        # Fetch all measurements, sorted by most recent first
        measurements = list(measurements_collection.find().sort('created_at', -1))
        
        # Convert ObjectId to string for JSON serialization
        history = []
        for m in measurements:
            history.append({
                'id': str(m['_id']),
                'user_id': m.get('user_id'),
                'user_name': m.get('user_name', 'Unknown'),
                'user_phone': m.get('user_phone', 'N/A'),
                'frame_width_mm': m.get('frame_width_mm'),
                'measurements': m.get('measurements', {}),
                'created_at': m.get('created_at').isoformat() if m.get('created_at') else None
            })
        
        app.logger.info(f"Returning {len(history)} measurement records")
        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        }), 200
        
    except Exception as e:
        app.logger.error(f"History fetch error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/process_image', methods=['POST', 'OPTIONS'])
def process_image():
    """
    Endpoint to process a single image file for optical measurements.
    Expects a multipart form with 'image' and 'frame_width_mm'.
    Saves measurements to MongoDB if configured.
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
    user_id = request.form.get('user_id', None)
    user_name = request.form.get('user_name', None)
    user_phone = request.form.get('user_phone', None)
    
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
        
        # Save measurements to MongoDB if configured
        _, measurements_collection = get_db_collections()
        
        if measurements_collection is not None and user_id:
            measurement_doc = {
                'user_id': user_id,
                'user_name': user_name,
                'user_phone': user_phone,
                'frame_width_mm': frame_width_mm,
                'measurements': measurements,
                'created_at': datetime.utcnow()
            }
            result = measurements_collection.insert_one(measurement_doc)
            app.logger.info(f"Measurement saved to MongoDB with ID: {result.inserted_id}")
        
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
