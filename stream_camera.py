from flask import Flask, Response, request
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

def save_video():
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(f'output_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.avi', fourcc, 20.0, (640, 480))

    os_name = platform.system()
    camera_index = 0
    if os_name == "Windows":
        cap = cv2.VideoCapture(camera_index)
    elif os_name == "Darwin":
        cap = cv2.VideoCapture(camera_index, cv2.CAP_AVFOUNDATION)
    elif os_name == "Linux":
        cap = cv2.VideoCapture(camera_index)

    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            out.write(frame)
        else:
            break

    cap.release()
    out.release()

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
            ret, buffer = cv2.imencode('.jpg', frame)
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

if __name__ == '__main__':
    video_thread = threading.Thread(target=save_video)
    video_thread.start()
    app.run(host='0.0.0.0', port=5001, debug=True)
