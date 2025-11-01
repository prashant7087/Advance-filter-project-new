
# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import os
# import uuid
# from measurement_logic import analyze_video
# import logging

# # Initialize the Flask app
# app = Flask(__name__)

# # Set up logging
# logging.basicConfig(level=logging.INFO)

# # Enable Cross-Origin Resource Sharing (CORS)
# CORS(app)

# # Ensure the 'uploads' directory exists
# if not os.path.exists('uploads'):
#     os.makedirs('uploads')

# @app.route('/process_video', methods=['POST'])
# def process_video_endpoint():
#     """
#     Endpoint to process a video file for optical measurements.
#     Expects a multipart form with 'video' and 'frame_width_mm'.
#     """
#     # --- 1. Validate Input ---
#     if 'video' not in request.files:
#         app.logger.warning("Request received without video file.")
#         return jsonify({'error': 'Missing video file'}), 400

#     if 'frame_width_mm' not in request.form:
#         app.logger.warning("Request received without frame_width_mm.")
#         return jsonify({'error': 'Missing frame_width_mm parameter'}), 400

#     video_file = request.files['video']
    
#     try:
#         # Convert frame_width_mm to a float for calculation
#         frame_width_mm = float(request.form['frame_width_mm'])
#     except ValueError:
#         app.logger.error("Invalid format for frame_width_mm. Could not convert to float.")
#         return jsonify({'error': 'frame_width_mm must be a valid number'}), 400

#     # --- 2. Save Video File ---
#     # Create a unique filename to avoid conflicts
#     filename = str(uuid.uuid4()) + '.mp4'
#     video_path = os.path.join('uploads', filename)
#     video_file.save(video_path)
#     app.logger.info(f"Video saved to {video_path}")

#     # --- 3. Analyze Video ---
#     try:
#         # Call the analysis function with the required frame_width_mm argument
#         app.logger.info(f"Analyzing video with frame width: {frame_width_mm}mm")
#         measurements, landmarks, frame_dims = analyze_video(video_path, frame_width_mm=frame_width_mm)
        
#         # Prepare the successful response
#         response_data = {
#             "measurements": measurements,
#             "landmarks": landmarks,
#             "frameDimensions": frame_dims
#         }
        
#         return jsonify(response_data)

#     except Exception as e:
#         # Log the full exception for easier debugging
#         app.logger.error(f"Analysis failed for {video_path}: {e}", exc_info=True)
#         return jsonify({'error': f"Analysis Failed: {e}"}), 500

#     finally:
#         # --- 4. Cleanup ---
#         # Ensure the temporary video file is always deleted
#         if os.path.exists(video_path):
#             os.remove(video_path)
#             app.logger.info(f"Cleaned up temporary file: {video_path}")

# if __name__ == '__main__':
#     # Run the Flask app
#     app.run(debug=True, port=5000)

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
from measurement_logic import analyze_image
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# --- UPDATED CORS Configuration ---
# As requested, explicitly allowing all origins ("*") and localhost:3000
CORS(app, origins=["http://localhost:3000", "*"])

if not os.path.exists('uploads'):
    os.makedirs('uploads')

# --- NEW Health Check Route ---
@app.route('/health', methods=['GET'])
def health_check():
    """
    A simple health check endpoint to confirm the API is running.
    You can test this in Postman with a GET request.
    """
    app.logger.info("Health check endpoint was hit.")
    # Returning JSON is a good practice for APIs
    return jsonify({'message': 'api is working fine'}), 200

# --- Existing Image Processing Route ---
@app.route('/process_image', methods=['POST'])
def process_image_endpoint():
    """
    Endpoint to process a single image file for optical measurements.
    Expects a multipart form with 'image' and 'frame_width_mm'.
    """
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
    image_path = os.path.join('uploads', filename)
    image_file.save(image_path)
    app.logger.info(f"Image saved to {image_path}")

    try:
        app.logger.info(f"Analyzing image with frame width: {frame_width_mm}mm")
        measurements, landmarks, frame_dims = analyze_image(image_path, frame_width_mm=frame_width_mm)
        response_data = { "measurements": measurements, "landmarks": landmarks, "frameDimensions": frame_dims }
        return jsonify(response_data)
    except Exception as e:
        app.logger.error(f"Analysis failed for {image_path}: {e}", exc_info=True)
        return jsonify({'error': f"Analysis Failed: {e}"}), 500
    finally:
        if os.path.exists(image_path):
            os.remove(image_path)
            app.logger.info(f"Cleaned up temporary file: {image_path}")

if __name__ == '__main__':
    # Added host='0.0.0.0' so you can access it from your frontend
    # running on localhost:3000
    app.run(debug=True, host='0.0.0.0', port=6000)
