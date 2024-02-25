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

def generate_frames(camera_index):
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        logger.error("Failed to open camera")
        return

    while True:
        success, frame = cap.read()
        if not success:
            logger.error("Failed to capture video frame")
            break
        else:
            # Resize frame to reduce bandwidth
            frame = cv2.resize(frame, (480, 480))
            frame = cv2.flip(frame, 1)  # Flip the frame horizontally
            # Encode the frame with JPEG format and lower quality
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 5])
            if not ret:
                logger.error("Failed to encode video frame")
                break

            # Convert the frame to bytes and yield for streaming
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

    # Release resources
    cap.release()

@app.route('/')
@auth.login_required
def index():
    cameras = enumerate(list_cameras())
    return render_template('index.html', cameras=cameras)

@app.route('/video', methods=['GET'])
@auth.login_required
def video():
    camera_index = int(request.args.get('camera_index', 0)) # Default to camera index 0 if not specified in request URL query
    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    logger.info(f"Video stream requested by {client_ip} using {user_agent}")
    try:
        return Response(generate_frames(camera_index), mimetype='multipart/x-mixed-replace; boundary=frame')
    except Exception as e:
        logger.error(f"Error serving video stream to {client_ip}: {e}")
        raise

def list_cameras(max_attempts=10):
    print("Checking for available cameras...")
    available_cameras = []
    for index in range(max_attempts):
        try:
            cap = cv2.VideoCapture(index, cv2.CAP_AVFOUNDATION)
            ret, frame = cap.read()
            if ret:
                print(f"Camera found at index {index}")
                available_cameras.append(index)
            else:
                print(f"No camera found at index {index}. Stopping search.")
                break
        except Exception as e:
            print(f"Error accessing camera at index {index}: {e}")
            break
        finally:
            cap.release()
    return available_cameras

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
