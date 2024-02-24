import time
from flask import Flask, render_template, request, redirect, url_for, Response
import subprocess
import cv2

app = Flask(__name__)

ffmpeg_process = None  # Global variable to manage FFmpeg process

@app.route('/')
def index():
    """Render the main page with a list of detected cameras."""
    cameras = detect_cameras()
    return render_template('/index.html', cameras=cameras)

@app.route('/start_stream', methods=['POST'])
def start_stream():
    global ffmpeg_process
    if ffmpeg_process:
        # Stop existing stream before starting a new one
        ffmpeg_process.terminate()
        ffmpeg_process = None

    selected_camera = request.form.get('camera')
    if selected_camera:
        print(f"Selected camera: {selected_camera}")
        ffmpeg_command = construct_ffmpeg_command(selected_camera)
        print("FFmpeg command:", ffmpeg_command)
        try:
            ffmpeg_process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # Wait a bit and then check if the process is still running or if it exited with an error
            time.sleep(2)
            if ffmpeg_process.poll() is not None:
                print("FFmpeg process ended prematurely with exit code:", ffmpeg_process.returncode)
                stderr_output = ffmpeg_process.stderr.read().decode()
                print("FFmpeg error output:", stderr_output)
        except Exception as e:
            print("Error starting FFmpeg process:", e)
            ffmpeg_process = None

        return redirect(url_for('index'))
    else:
        return "No camera selected", 400

@app.route('/video_feed')
def video_feed():
    """Route to stream video from the currently selected camera."""
    if ffmpeg_process is None:
        return Response(status=500)
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def detect_cameras():
    """Detects connected cameras and returns them as a list of tuples."""
    cameras = []
    for index in range(10):  # Arbitrary max index
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            camera_name = f"Camera {index}"
            cameras.append((index, camera_name))  # Add as a tuple
            print(f"Detected camera: {camera_name}, Index: {index}")
            cap.release()
        else:
            print(f"No camera detected at index {index}")
    print(f"Number of cameras detected: {len(cameras)}")
    return cameras


def construct_ffmpeg_command(camera_index):
    """Constructs the FFmpeg command based on the selected camera index."""
    return [
        'ffmpeg',
        '-f', 'avfoundation',
        '-i', str(camera_index),  # Camera index is used directly here
        '-c:v', 'h264',
        '-preset', 'ultrafast',
        '-tune', 'zerolatency',
        '-pix_fmt', 'yuv420p',
        '-s', '640x480',
        'pipe:1'
    ]

def generate_frames():
    """Yields frames from FFmpeg to the response."""
    global ffmpeg_process
    try:
        while True:
            if ffmpeg_process.poll() is not None:
                break
            frame = ffmpeg_process.stdout.read(1024)
            if not frame:
                break
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    except Exception as e:
        print("Error generating frames:", e)
    finally:
        if ffmpeg_process:
            ffmpeg_process.terminate()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
