from PIL import Image
import numpy as np
import math
import os
import urllib.request

# MediaPipe Tasks API
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# --- Landmark Indices (from MediaPipe Face Mesh) ---
LEFT_PUPIL = 473
RIGHT_PUPIL = 468
LEFT_REFERENCE = 127
RIGHT_REFERENCE = 356
LEFT_EYE_LOWER_LID = 27 
FITTING_HEIGHT_OFFSET = 11.0 # in mm
NOSE_TIP = 1
FOREHEAD = 10
CHIN = 152

# Model file path - use /tmp for Vercel serverless (read-only filesystem)
import tempfile
MODEL_PATH = os.path.join(tempfile.gettempdir(), 'face_landmarker.task')
MODEL_URL = 'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task'


def download_model_if_needed():
    """Download the face landmarker model if it doesn't exist."""
    if not os.path.exists(MODEL_PATH):
        print(f"Downloading face landmarker model to {MODEL_PATH}...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("Download complete.")
    return MODEL_PATH


def analyze_image(image_path, frame_width_mm):
    """
    Analyzes a single image to find facial landmarks and calculate optical measurements.
    Uses the new MediaPipe Tasks API.
    """
    # Ensure model is downloaded
    model_path = download_model_if_needed()
    
    # Create FaceLandmarker
    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        output_face_blendshapes=False,
        output_facial_transformation_matrixes=False,
        num_faces=1
    )
    
    detector = vision.FaceLandmarker.create_from_options(options)
    
    # Load and process image
    try:
        pil_image = Image.open(image_path)
    except Exception:
        raise ValueError("Error: Could not read image file.")

    # Convert to RGB (MediaPipe needs RGB)
    pil_image = pil_image.convert('RGB')
    image_rgb = np.array(pil_image)
    
    frame_height_px, frame_width_px, _ = image_rgb.shape
    frame_dims = {"width": frame_width_px, "height": frame_height_px}

    # Create MediaPipe Image (already RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
    
    # Detect face landmarks
    detection_result = detector.detect(mp_image)
    
    if not detection_result.face_landmarks:
        raise ValueError("No face detected in the image.")
    
    # Get landmarks (first face)
    face_landmarks = detection_result.face_landmarks[0]
    
    # Convert to the format expected by the rest of the code
    class LandmarkWrapper:
        def __init__(self, lm):
            self.x = lm.x
            self.y = lm.y
            self.z = lm.z
    
    landmarks = [LandmarkWrapper(lm) for lm in face_landmarks]
    
    # --- Pixel to MM Conversion ---
    left_ref_pt = landmarks[LEFT_REFERENCE]
    right_ref_pt = landmarks[RIGHT_REFERENCE]
    ref_width_px = math.sqrt(((right_ref_pt.x - left_ref_pt.x) * frame_width_px)**2 + 
                             ((right_ref_pt.y - left_ref_pt.y) * frame_height_px)**2)
    if ref_width_px == 0:
        raise ValueError("Could not establish a reference width for measurement.")
    mm_per_pixel = frame_width_mm / ref_width_px

    # --- Measurement Calculations ---
    left_pupil_pt = landmarks[LEFT_PUPIL]
    right_pupil_pt = landmarks[RIGHT_PUPIL]
    pd_px = math.sqrt(((right_pupil_pt.x - left_pupil_pt.x) * frame_width_px)**2 + 
                      ((right_pupil_pt.y - left_pupil_pt.y) * frame_height_px)**2)
    pd_mm = pd_px * mm_per_pixel

    lower_lid_pt = landmarks[LEFT_EYE_LOWER_LID]
    eye_height_px = abs(lower_lid_pt.y - left_pupil_pt.y) * frame_height_px
    eye_height_mm = eye_height_px * mm_per_pixel
    fh_mm = eye_height_mm + FITTING_HEIGHT_OFFSET

    forehead_z = landmarks[FOREHEAD].z
    chin_z = landmarks[CHIN].z
    tilt_rad = math.atan2(chin_z - forehead_z, 0.2)
    tilt_deg = abs(math.degrees(tilt_rad))

    vertex_mm = (abs(landmarks[NOSE_TIP].z) * 100) + 8 

    measurements = { "pd": pd_mm, "fh": fh_mm, "tilt": min(tilt_deg, 15.0), "vertex": min(vertex_mm, 14.0) }
    landmarks_for_3d = [[lm.x, lm.y, lm.z] for lm in landmarks]
    
    detector.close()
    return measurements, landmarks_for_3d, frame_dims