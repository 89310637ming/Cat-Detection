from flask import Flask, request, jsonify, send_from_directory
from PIL  import Image
import io, time, os
from ultralytics import YOLO

# ── Config ────────────────────────────────────────────────────────────
UPLOAD_DIR = "uploads"
MODEL_PATH = "yolov8n.pt"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app   = Flask(__name__)
model = YOLO(MODEL_PATH)

# ── Main upload endpoint ──────────────────────────────────────────────
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

# ── NEW: serve images back to a browser ───────────────────────────────
@app.route("/img/<path:filename>")
def get_image(filename):
    """
    Example URL:
        http://<EC2-IP>:5001/img/20250428_131045_cam.jpg
    """
    return send_from_directory(UPLOAD_DIR, filename)

# convenience: quick list of files
@app.route("/list_images")
def list_images():
    files = sorted(os.listdir(UPLOAD_DIR), reverse=True)
    return jsonify(files)

# ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
