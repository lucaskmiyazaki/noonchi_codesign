import subprocess
import time
from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime

app = Flask(__name__, static_folder="public")

state = {}

def now_ms():
    return int(datetime.utcnow().timestamp() * 1000)

@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200

@app.get("/emotion/<device_id>")
def get_emotion(device_id):
    if device_id not in state:
        return jsonify({"error": "not found"}), 404
    return jsonify(state[device_id]), 200

@app.post("/emotion")
def set_emotion():
    data = request.get_json()
    device_id = data.get("id")
    emotion = data.get("emotion")
    nickname = data.get("nickname")

    if not device_id:
        return jsonify({"error": "id are required"}), 400

    # if device does not exist yet, create empty default
    if device_id not in state:
        state[device_id] = {"emotion": "neutral", "nickname": "", "updated_at": now_ms()}

    # if emotion is missing, keep previous one
    if not emotion:
        emotion = state[device_id]["emotion"]

    # if nickname is missing, keep previous one
    if not nickname:
        nickname = state[device_id]["nickname"]

    state[device_id] = {
        "emotion": emotion,
        "nickname": nickname,
        "updated_at": now_ms()
    }

    return jsonify({"status": "ok"}), 200

@app.get("/state")
def get_state():
    return jsonify(state), 200

@app.post("/reset")
def reset_state():
    for device_id in state:
        state[device_id]["emotion"] = "neutral"
        state[device_id]["updated_at"] = now_ms()

    return jsonify({"status": "reset"}), 200

@app.get("/<path:path>")
def serve_file(path):
    return send_from_directory("public", path)


def start_ngrok():
    # Starts ngrok and prints the public URL
    ngrok = subprocess.Popen(["ngrok", "http", "5001"],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)

    # Wait for ngrok to start
    time.sleep(2)

    # Print the URL (it will show in your console)
    print("ngrok started. Check your terminal for the public URL.")

if __name__ == "__main__":
    start_ngrok()
    app.run(host="0.0.0.0", port=5001)
