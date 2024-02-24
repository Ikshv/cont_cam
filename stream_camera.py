from flask import Flask, Response
from flask_httpauth import HTTPBasicAuth
import cv2
import platform

app = Flask(__name__)
auth = HTTPBasicAuth()

users = {
    "u6b6u6": "Sigmarho420!"  # This should be a secure password or ideally, use a more secure method to store credentials.
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
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video')
@auth.login_required
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)


