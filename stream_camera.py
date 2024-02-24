from flask import Flask, Response, request, render_template
from flask_httpauth import HTTPBasicAuth
import cv2
import platform
import logging
from logging.handlers import RotatingFileHandler
import os
import threading
import datetime

# Initialize Flask application
app = Flask(__name__)
auth = HTTPBasicAuth()

# Configure logging
logging.basicConfig(level=logging.INFO)
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
logger = logging.getLogger(__name__)
logger.addHandler(handler)

# Dummy users dictionary - replace with a more secure method
users = {
    "u6b6u6": os.environ.get('TEST_USER_PASSWORD')  # Securely fetch the password from environment variables
}

@auth.verify_password
def verify_password(username, password):
    if username in users:
        return users.get(username) == password
    return False

def generate_frames():
    os_name = platform.system()
    camera_index = 0
    if os_name == "Windows":
        cap = cv2.VideoCapture(camera_index)
    elif os_name == "Darwin":
        cap = cv2.VideoCapture(camera_index, cv2.CAP_AVFOUNDATION)
    elif os_name == "Linux":
        cap = cv2.VideoCapture(camera_index)

    while True:
        success, frame = cap.read()
        if not success:
            logger.error("Failed to capture video frame")
            break
        else:
            frame = cv2.flip(frame, 1)  # Flip horizontally

            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                logger.error("Failed to encode video frame")
                break
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video')
@auth.login_required
def video():
    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    logger.info(f"Video stream requested by {client_ip} using {user_agent}")
    try:
        return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    except Exception as e:
        logger.error(f"Error serving video stream to {client_ip}: {e}")
        raise

@app.route('/')
@auth.login_required
def index():
    return render_template('/templates/index.html')

@app.route('/start_recording', methods=['POST'])
def start_recording():
    # Logic to start recording
    return "Recording Started"

@app.route('/stop_recording', methods=['POST'])
def stop_recording():
    # Logic to stop recording
    return "Recording Stopped"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
