import os
import cv2
import mediapipe as mp
from flask import Flask, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils


def allowed_file(filename):
    """Check if the uploaded file is an allowed type."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def process_image(file_path, threshold):
    """Process the image with MediaPipe Pose to detect multiple people."""
    # Load image
    image = cv2.imread(file_path)


    scale_factor = 3.0  # Increase the size by 3x
    width = int(image.shape[1] * scale_factor)
    height = int(image.shape[0] * scale_factor)
    resized_image = cv2.resize(image, (width, height), interpolation=cv2.INTER_LINEAR)


    rgb_image = cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB)

    with mp_pose.Pose(
            static_image_mode=True,
            min_detection_confidence=threshold,
            model_complexity=2,  # Higher accuracy
    ) as pose:

        results = pose.process(rgb_image)


        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                resized_image,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=3, circle_radius=4),  # Blue for lines
                mp_drawing.DrawingSpec(color=(255, 255, 0), thickness=4, circle_radius=5),  # Yellow for landmarks
            )

        output_path = os.path.join(UPLOAD_FOLDER, "processed_image.jpg")
        cv2.imwrite(output_path, resized_image)
        return output_path


@app.route('/')
def index():
    """Render the homepage with a file upload form."""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file uploads."""
    if 'file' not in request.files or 'threshold' not in request.form:
        return 'No file or threshold provided.', 400

    file = request.files['file']
    threshold = float(request.form['threshold'])

    if file.filename == '':
        return 'No selected file.', 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        processed_file = process_image(file_path, threshold)
        return send_from_directory(app.config['UPLOAD_FOLDER'], "processed_image.jpg")

    return 'Invalid file format. Please upload a valid image.', 400


if __name__ == "__main__":
    app.run(debug=True)
