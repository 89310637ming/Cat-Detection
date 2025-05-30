from flask import Flask, request, jsonify, send_from_directory, render_template
import csv
from status import BatteryManager
from PIL  import Image
import io, time, os
from ultralytics import YOLO

# ───────────────────────────────────────────────────────────────
UPLOAD_DIR = "uploads"
STATUS_FILE = "status_history.csv"
FIELDNAMES = ["timestamp", "battery_level", "battery_voltage", "solar_panel_on", "heating_pad_on", "temperature"]
MODEL_PATH = "yolov8n.pt"
# ───────────────────────────────────────────────────────────────
app = Flask(__name__)
os.makedirs(UPLOAD_DIR, exist_ok=True)
model = YOLO(MODEL_PATH)

battery_manager = BatteryManager()

# Initialize CSV if missing
if not os.path.exists(STATUS_FILE):
    with open(STATUS_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()

# ───────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/detect_cat", methods=["POST"])
def detect_cat():
    img_bytes = request.data          # raw JPEG coming from ESP32
    if not img_bytes:
        return jsonify({"error": "No image uploaded"}), 400

    # save the file so we can view / download it
    ts     = time.strftime("%Y%m%d_%H%M%S")
    fname  = f"{ts}_cam.jpg"
    path   = os.path.join(UPLOAD_DIR, fname)
    with open(path, "wb") as f:
        f.write(img_bytes)
    print(f"⇢ saved {path} ({os.path.getsize(path)} bytes)")

    # run YOLO
    img      = Image.open(io.BytesIO(img_bytes))
    results  = model.predict(img, verbose=False)
    cat      = any(model.names[int(b.cls[0])] == "cat"
                   for r in results for b in r.boxes)
    print("YOLO says cat =", cat)

    return jsonify({
        "cat_detected": bool(cat),
        "file": fname          # useful for the ESP32 or UI
    }), 200

@app.route("/update_status", methods=["POST"])
def update_status():
    data = request.json
    if not data:
        return jsonify({"error": "No JSON received"}), 400

    # Update battery manager
    battery_manager.update(
        data.get("battery_level"),
        data.get("solar_panel_on"),
        data.get("heating_pad_on"),
        data.get("temperature")
    )

    # Save new status into CSV manually ordered
    status = battery_manager.get_status()
    row = {
        "timestamp": status["timestamp"],
        "battery_level": status["battery_level"],
        "battery_voltage": status["battery_voltage"],
        "solar_panel_on": status["solar_panel_on"],
        "heating_pad_on": status["heating_pad_on"],
        "temperature": status["temperature"]
    }

    with open(STATUS_FILE, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow(row)

    return jsonify({"message": "Status updated"}), 200

@app.route("/status", methods=["GET"])
def get_status():
    return jsonify(battery_manager.get_status())

@app.route("/history", methods=["GET"])
def get_history():
    try:
        with open(STATUS_FILE, 'r') as f:
            reader = csv.DictReader(f)
            history = list(reader)
            return jsonify(history)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/img/<path:filename>")
def get_image(filename):
    return send_from_directory(UPLOAD_DIR, filename)

@app.route("/list_images")
def list_images():
    files = sorted(os.listdir(UPLOAD_DIR), reverse=True)
    return jsonify(files)

# ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
