# app.py
import os
import torch
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

# ??????? ???? predict ?? utils.ocr (?? ??? ??????)
from utils.ocr import predict

app = Flask(__name__)

UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/predict', methods=['POST'])
def predict_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        result = predict(filepath)
        os.remove(filepath)  # ???????: ???? ?????? ??? ????????

        return jsonify({
            "success": True,
            "result": result
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/', methods=['GET'])
def home():
    return "? Dots OCR API is running. POST to /predict with 'image' file."


if __name__ == '__main__':
    device = torch.device('cpu')
    print(f"?? Running on device: {device}")
    app.run(host='0.0.0.0', port=5000, debug=False)