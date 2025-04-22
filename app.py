# from flask import Flask, request, jsonify
# from PIL import Image
# import io
# from ultralytics import YOLO

# app = Flask(__name__)

# model = YOLO('yolov8n.pt')

# @app.route('/detect_cat', methods=['POST'])
# def detect_cat():
#     """
#     Expects a file field "image" in the HTTP POST,
#     e.g., via multipart/form-data or from a client like curl/Postman/ESP32.
#     """
#     # check if an image was uploaded
#     if 'image' not in request.files:
#         return jsonify({"error": "No image uploaded"}), 400
    
#     file = request.files['image']
#     if file.filename == '':
#         return jsonify({"error": "Empty filename"}), 400

#     try:
#         # Read the uploaded file into a Pillow image
#         image_bytes = file.read()
#         img = Image.open(io.BytesIO(image_bytes))

#         # YOLOv8 inference
#         results = model.predict(img, verbose=False)

#         # Check for a cat
#         cat_detected = False
#         for result in results:
#             for box in result.boxes:
#                 class_id = int(box.cls[0].item())  # class index (tensor)
#                 class_name = model.names[class_id] # map index to label
#                 if class_name == 'cat':
#                     cat_detected = True
#                     break

#         # Return JSON response
#         return jsonify({"cat_detected": cat_detected}), 200

#     except Exception as e:
#         # Catch and report any errors
#         return jsonify({"error": str(e)}), 500

# if __name__ == '__main__':
#     # For local development on port 5000
#     app.run(host='0.0.0.0', port=5001, debug=True)
from flask import Flask, request, jsonify
from PIL import Image
import io, time, os
from ultralytics import YOLO

app  = Flask(__name__)
model = YOLO("yolov8n.pt")

UPLOAD_DIR = "uploads"                  # <‑‑ where we drop the jpegs
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route("/detect_cat", methods=["POST"])
def detect_cat():
    # ─── 1. receive file ───────────────────────────────────────────────
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    # optional: save a copy so you can inspect later
    ts   = time.strftime("%Y%m%d_%H%M%S")
    fname = f"{ts}_{file.filename or 'cam.jpg'}"
    path  = os.path.join(UPLOAD_DIR, fname)
    file.save(path)
    print(f"⇢ saved {path}  ({os.path.getsize(path)} bytes)")

    # ─── 2. run YOLOv8 ────────────────────────────────────────────────
    img = Image.open(path)
    results = model.predict(img, verbose=False)

    cat = any(
        model.names[int(b.cls[0])] == "cat"
        for r in results
        for b in r.boxes
    )
    print("  YOLO says cat =", cat)

    # ─── 3. JSON back to caller ───────────────────────────────────────
    return jsonify({
        "cat_detected": bool(cat),
        "file": fname          # handy when debugging
    }), 200


if __name__ == "__main__":
    # listen on LAN so the ESP32 can reach us
    app.run(host="0.0.0.0", port=5001, debug=True)

