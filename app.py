from flask import Flask, request, jsonify, send_from_directory, render_template
from status import BatteryManager
import os
import csv

UPLOAD_DIR = "uploads"
STATUS_FILE = "status_history.csv"

app = Flask(__name__)
os.makedirs(UPLOAD_DIR, exist_ok=True)

battery_manager = BatteryManager()

# Initialize CSV if needed
if not os.path.exists(STATUS_FILE):
    with open(STATUS_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "battery_level", "battery_voltage", "solar_panel_on", "heating_pad_on", "temperature"])
        writer.writeheader()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/detect_cat", methods=["POST"])
def detect_cat():
    img_bytes = request.data
    if not img_bytes:
        return jsonify({"error": "No image uploaded"}), 400

    ts = time.strftime("%Y%m%d_%H%M%S")
    fname = f"{ts}_cam.jpg"
    path = os.path.join(UPLOAD_DIR, fname)
    with open(path, "wb") as f:
        f.write(img_bytes)

    return jsonify({"message": "Image uploaded successfully", "file": fname}), 200

@app.route("/update_status", methods=["POST"])
def update_status():
    data = request.json
    if not data:
        return jsonify({"error": "No JSON received"}), 400

    # Update the internal state
    battery_manager.update(
        battery_level=data.get("battery_level"),
        solar_panel_on=data.get("solar_panel_on"),
        heating_pad_on=data.get("heating_pad_on"),
        temperature=data.get("temperature")
    )

    # Save new status to CSV
    status = battery_manager.get_status()
    with open(STATUS_FILE, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=status.keys())
        writer.writerow(status)

    return jsonify({"message": "Status updated"}), 200

@app.route("/status", methods=["GET"])
def get_status():
    # Just return the latest info
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
