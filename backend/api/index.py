from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
import sys
import tempfile
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Enable CORS for all origins
CORS(app, origins=["*"])

# Use /tmp for Vercel serverless functions
UPLOAD_FOLDER = tempfile.gettempdir()

# Import measurement logic
try:
    from measurement_logic import analyze_image
except ImportError:
    # Fallback: try relative import
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "measurement_logic", 
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "measurement_logic.py")
    )
    measurement_logic = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(measurement_logic)
    analyze_image = measurement_logic.analyze_image


# Root route for testing
@app.route('/', methods=['GET'])
@app.route('/api', methods=['GET'])
@app.route('/api/', methods=['GET'])
def root():
    return jsonify({'message': 'Lenskart AI Fitter API is running!'}), 200


@app.route('/health', methods=['GET'])
@app.route('/api/health', methods=['GET'])
def health_check():
    """
    A simple health check endpoint to confirm the API is running.
    """
    app.logger.info("Health check endpoint was hit.")
    return jsonify({'message': 'API is working fine on Vercel!'}), 200


@app.route('/process_image', methods=['POST', 'OPTIONS'])
@app.route('/api/process_image', methods=['POST', 'OPTIONS'])
def process_image_endpoint():
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
