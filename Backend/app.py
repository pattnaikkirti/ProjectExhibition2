from flask import Flask, render_template, Response, jsonify, send_from_directory, request
from flask_cors import CORS
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import joblib
from collections import deque
import os
import threading
import time
import base64
from PIL import Image
import io

app = Flask(__name__, template_folder='../Frontend', static_folder='../Frontend')
CORS(app)  # Enable CORS for all routes

# Load model and encoder
clf = joblib.load("isl_model.pkl")
encoder = joblib.load("isl_label_encoder.pkl")

# Create HandLandmarker
model_path = os.path.join(os.path.dirname(__file__), 'hand_landmarker.task')
base_options = python.BaseOptions(model_asset_path=model_path)
options = vision.HandLandmarkerOptions(base_options=base_options, num_hands=1)
detector = vision.HandLandmarker.create_from_options(options)

# Global variables for video processing
window_size = 5
predictions_window = deque(maxlen=window_size)
recognized_text = ""
current_sign = ""
hand_present = False
cap = None
processing_thread = None
stop_processing = False

# Initialize webcam
def init_camera():
    global cap
    if cap is None or not cap.isOpened():
        cap = cv2.VideoCapture(0)
        # Try different camera indices if 0 doesn't work
        for i in range(3):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                print(f"Camera opened at index {i}")
                return True
        print("Error: Could not open any camera")
        return False
    return True

def process_frame():
    global recognized_text, current_sign, hand_present, predictions_window
    
    while not stop_processing and cap and cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1) 
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        results = detector.detect(mp_image)

        if results.hand_landmarks:
            hand_present = True 

            for hand_landmarks in results.hand_landmarks:
                # Draw landmarks on frame - make them more visible
                for landmark in hand_landmarks:
                    x = int(landmark.x * frame.shape[1])
                    y = int(landmark.y * frame.shape[0])
                    # Draw larger, more visible dots with border
                    cv2.circle(frame, (x, y), 8, (0, 0, 255), -1)  # Red filled circle
                    cv2.circle(frame, (x, y), 8, (255, 255, 255), 2)  # White border

                # Draw connections between landmarks
                connections = [
                    (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
                    (0, 5), (5, 6), (6, 7), (7, 8),  # Index finger
                    (0, 9), (9, 10), (10, 11), (11, 12),  # Middle finger
                    (0, 13), (13, 14), (14, 15), (15, 16),  # Ring finger
                    (0, 17), (17, 18), (18, 19), (19, 20),  # Pinky
                    (5, 9), (9, 13), (13, 17)  # Palm
                ]
                
                for connection in connections:
                    if connection[0] < len(hand_landmarks) and connection[1] < len(hand_landmarks):
                        x1 = int(hand_landmarks[connection[0]].x * frame.shape[1])
                        y1 = int(hand_landmarks[connection[0]].y * frame.shape[0])
                        x2 = int(hand_landmarks[connection[1]].x * frame.shape[1])
                        y2 = int(hand_landmarks[connection[1]].y * frame.shape[0])
                        cv2.line(frame, (x1, y1), (x2, y2), (255, 255, 255), 2)  # White lines

                landmarks = []
                for lm in hand_landmarks:
                    landmarks.extend([lm.x, lm.y, lm.z])

                pred = clf.predict([landmarks])[0]
                predictions_window.append(pred)

                smooth_pred = max(set(predictions_window), key=predictions_window.count)
                current_sign = encoder.inverse_transform([smooth_pred])[0]

                # Add current sign display on frame
                cv2.rectangle(frame, (40, 20), (400, 80), (0, 0, 0), -1)
                cv2.putText(frame, f"Current Sign: {current_sign}", (50, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

        else:
            if hand_present and current_sign != "":
                recognized_text += current_sign
                current_sign = ""
            hand_present = False

        # Add recognized text display on frame
        cv2.rectangle(frame, (40, 100), (800, 150), (0, 0, 0), -1)
        cv2.putText(frame, f"Text: {recognized_text}", (50, 140),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 0, 0), 2)

        # Store the frame for streaming
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        
        # Yield the frame for streaming
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        time.sleep(0.03)  # ~30 FPS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/detect.html')
def detect():
    return render_template('detect.html')

@app.route('/about.html')
def about():
    return render_template('about.html')

@app.route('/style.css')
def styles():
    return send_from_directory('../Frontend', 'style.css')

@app.route('/detect.js')
def detect_js():
    return send_from_directory('../Frontend', 'detect.js')

@app.route('/video_feed')
def video_feed():
    if not init_camera():
        return "Camera not available", 500
    
    def generate_frames():
        global recognized_text, current_sign, hand_present, predictions_window
        
        while True:
            if cap is None or not cap.isOpened():
                break
                
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1) 
            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
            results = detector.detect(mp_image)

            if results.hand_landmarks:
                hand_present = True 

                for hand_landmarks in results.hand_landmarks:
                    # Draw landmarks on frame - make them more visible
                    for landmark in hand_landmarks:
                        x = int(landmark.x * frame.shape[1])
                        y = int(landmark.y * frame.shape[0])
                        # Draw larger, more visible dots with border
                        cv2.circle(frame, (x, y), 8, (0, 0, 255), -1)  # Red filled circle
                        cv2.circle(frame, (x, y), 8, (255, 255, 255), 2)  # White border

                    # Draw connections between landmarks
                    connections = [
                        (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
                        (0, 5), (5, 6), (6, 7), (7, 8),  # Index finger
                        (0, 9), (9, 10), (10, 11), (11, 12),  # Middle finger
                        (0, 13), (13, 14), (14, 15), (15, 16),  # Ring finger
                        (0, 17), (17, 18), (18, 19), (19, 20),  # Pinky
                        (5, 9), (9, 13), (13, 17)  # Palm
                    ]
                    
                    for connection in connections:
                        if connection[0] < len(hand_landmarks) and connection[1] < len(hand_landmarks):
                            x1 = int(hand_landmarks[connection[0]].x * frame.shape[1])
                            y1 = int(hand_landmarks[connection[0]].y * frame.shape[0])
                            x2 = int(hand_landmarks[connection[1]].x * frame.shape[1])
                            y2 = int(hand_landmarks[connection[1]].y * frame.shape[0])
                            cv2.line(frame, (x1, y1), (x2, y2), (255, 255, 255), 2)  # White lines

                    landmarks = []
                    for lm in hand_landmarks:
                        landmarks.extend([lm.x, lm.y, lm.z])

                    pred = clf.predict([landmarks])[0]
                    predictions_window.append(pred)

                    smooth_pred = max(set(predictions_window), key=predictions_window.count)
                    current_sign = encoder.inverse_transform([smooth_pred])[0]

                    # Add current sign display on frame
                    cv2.rectangle(frame, (40, 20), (400, 80), (0, 0, 0), -1)
                    cv2.putText(frame, f"Current Sign: {current_sign}", (50, 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

            else:
                if hand_present and current_sign != "":
                    recognized_text += current_sign
                    current_sign = ""
                hand_present = False

            # Add recognized text display on frame
            cv2.rectangle(frame, (40, 100), (800, 150), (0, 0, 0), -1)
            cv2.putText(frame, f"Text: {recognized_text}", (50, 140),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 0, 0), 2)

            # Encode frame for streaming
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            
            # Yield the frame for streaming
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(0.033)  # ~30 FPS
    
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_text')
def get_text():
    return jsonify({
        'recognized_text': recognized_text,
        'current_sign': current_sign
    })

@app.route('/clear_text')
def clear_text():
    global recognized_text
    recognized_text = ""
    return jsonify({'status': 'success'})

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get the image data from the request
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'No image data provided'}), 400
        
        # Decode the base64 image
        image_data = base64.b64decode(data['image'].split(',')[1])
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to numpy array and then to OpenCV format
        frame = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Process the frame for hand detection
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
        results = detector.detect(mp_image)
        
        if results.hand_landmarks:
            hand_landmarks = results.hand_landmarks[0]
            
            # Extract landmarks for prediction
            landmarks = []
            landmark_coords = []
            for lm in hand_landmarks:
                landmarks.extend([lm.x, lm.y, lm.z])
                landmark_coords.append({'x': lm.x, 'y': lm.y, 'z': lm.z})
            
            # Make prediction
            pred = clf.predict([landmarks])[0]
            current_sign = encoder.inverse_transform([pred])[0]
            
            return jsonify({
                'success': True,
                'prediction': current_sign,
                'hand_detected': True,
                'landmarks': landmark_coords
            })
        else:
            return jsonify({
                'success': True,
                'prediction': '',
                'hand_detected': False
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.teardown_appcontext
def cleanup(exc):
    global cap, stop_processing
    if cap:
        stop_processing = True
        cap.release()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
