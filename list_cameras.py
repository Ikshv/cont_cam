import cv2

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

if __name__ == "__main__":
    try:
        cameras = list_cameras()
        print(f"Available camera indexes: {cameras}")
    except ImportError:
        print("OpenCV is not available. Please install OpenCV to use this script.")
