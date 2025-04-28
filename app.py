from flask import Flask, request, jsonify, send_from_directory, render_template_string
from PIL import Image
import os
import io
import time
from ultralytics import YOLO

# --- Configuration ---
UPLOAD_DIR = "uploads"
MODEL_PATH = "yolov8n.pt"

app = Flask(__name__)
model = YOLO(MODEL_PATH)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Server-side state
global_state = {
    "last_cat": False,
    "last_image_filename": None,
    "hx1": 0.0,
    "hx2": 0.0,
    "motor": "idle"
}

# --- Endpoints ---

@app.route("/")
def dashboard():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ESP32 Cat Detection Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; margin: 20px; background: #f2f2f2; }
            .card { background: white; display: inline-block; padding: 20px; margin: 10px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
            img { max-width: 90%; border-radius: 10px; margin-top: 10px; }
        </style>
    </head>
    <body>
        <h1>ESP32 Cat Detection Dashboard</h1>
        <div id="stats" class="card">
            <p>Weight 1 (HX1): <span id="hx1">0</span> g</p>
            <p>Weight 2 (HX2): <span id="hx2">0</span> g</p>
            <p>Motor Status: <span id="motor">idle</span></p>
            <p>Cat Detected: <span id="cat">No</span></p>
        </div>
        <div id="image" class="card">
            <p>Last Captured Image:</p>
            <img id="latest" src="" alt="No image yet">
        </div>

        <script>
            async function update() {
                const res = await fetch('/state');
                const data = await res.json();
                document.getElementById('hx1').innerText = data.hx1.toFixed(1);
                document.getElementById('hx2').innerText = data.hx2.toFixed(1);
                document.getElementById('motor').innerText = data.motor;
                document.getElementById('cat').innerText = data.last_cat ? 'Yes' : 'No';
                if (data.last_image_filename) {
                    document.getElementById('latest').src = '/img/' + data.last_image_filename + '?t=' + Date.now();
                }
            }
            setInterval(update, 3000);
            update();
        </script>
    </body>
    </html>
    ''')

@app.route("/detect_cat", methods=["POST"])
def detect_cat():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    
    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # Save image locally
    ts = time.strftime("%Y%m%d_%H%M%S")
    fname = f"{ts}_{file.filename or 'cam.jpg'}"
    path  = os.path.join(UPLOAD_DIR, fname)
    file.save(path)
    print(f"Saved locally: {path}")

    # YOLOv8 prediction
    img = Image.open(path)
    results = model.predict(img, verbose=False)

    cat_found = any(
        model.names[int(box.cls[0])] == "cat"
        for r in results
        for box in r.boxes
    )
    print(f"YOLO: cat detected = {cat_found}")

    # Update server state
    global_state["last_cat"] = cat_found
    global_state["last_image_filename"] = fname

    return jsonify({
        "cat_detected": cat_found,
        "filename": fname
    })

@app.route("/state", methods=["GET", "POST"])
def state():
    if request.method == "POST":
        data = request.get_json()
        if data:
            global_state.update({
                "hx1": data.get("hx1", global_state["hx1"]),
                "hx2": data.get("hx2", global_state["hx2"]),
                "motor": data.get("motor", global_state["motor"])
            })
    return jsonify(global_state)

@app.route("/img/<filename>", methods=["GET"])
def get_image(filename):
    return send_from_directory(UPLOAD_DIR, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
