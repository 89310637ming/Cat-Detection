from flask import Flask, request, jsonify
from PIL import Image
import io, time, os
from ultralytics import YOLO

app  = Flask(__name__)
model = YOLO("yolov8n.pt")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route("/detect_cat", methods=["POST"])
def detect_cat():
    # gets the raw jpeg image
    img_bytes = request.data
    if not img_bytes:
        return jsonify({"error": "No image uploaded"}), 400

    # saving a copy to view the image later
    ts = time.strftime("%Y%m%d_%H%M%S")
    fname = f"{ts}_cam.jpg"
    path  = os.path.join(UPLOAD_DIR, fname)
    with open(path, "wb") as f:
        f.write(img_bytes)
    print(f"⇢ saved {path}  ({os.path.getsize(path)} bytes)")

    # run YOLOv8
    img = Image.open(io.BytesIO(img_bytes))
    results = model.predict(img, verbose=False)

    cat = any(
        model.names[int(b.cls[0])] == "cat"
        for r in results
        for b in r.boxes
    )
    print("  YOLO says cat =", cat)

    # Sent a response back to ESP32
    return jsonify({
        "cat_detected": bool(cat),
        "file": fname
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
