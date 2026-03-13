import subprocess
import time
from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime
import requests

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
        return jsonify({"error": "id is required"}), 400

    # create default only once
    if device_id not in state:
        state[device_id] = {
            "emotion": "neutral",
            "nickname": "",
            "speaker": False,
            "updated_at": now_ms()
        }

    current = state[device_id]

    state[device_id] = {
        "emotion": emotion if emotion is not None else current.get("emotion", "neutral"),
        "nickname": nickname if nickname is not None else current.get("nickname", ""),
        "speaker": current.get("speaker", False),
        "updated_at": now_ms()
    }

    return jsonify({"status": "ok"}), 200

@app.get("/emotion/speaker")
def get_emotion_speaker():
    for device_id, device_data in state.items():
        if device_data.get("speaker", False):
            return jsonify({
                "id": device_id,
                "nickname": device_data.get("nickname", ""),
                "emotion": device_data.get("emotion", "neutral"),
                "updated_at": device_data.get("updated_at")
            }), 200

    return jsonify({"error": "no speaker selected"}), 404

@app.post("/speaker/<device_id>")
def set_speaker(device_id):
    # if device does not exist yet, create it
    if device_id not in state:
        state[device_id] = {
            "emotion": "neutral",
            "nickname": "",
            "speaker": False,
            "updated_at": now_ms()
        }

    # only one speaker at a time
    for other_device_id in state:
        state[other_device_id]["speaker"] = False

    state[device_id]["speaker"] = True
    state[device_id]["updated_at"] = now_ms()

    return jsonify({
        "status": "ok",
        "speaker": device_id
    }), 200

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
    ngrok = subprocess.Popen(["ngrok", "http", "5001", "--scheme=http,https"],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)

    # Wait for ngrok to start
    time.sleep(2)

    time.sleep(3)

    try:
        r = requests.get("http://127.0.0.1:4040/api/tunnels")
        tunnels = r.json()["tunnels"]

        print("\n===== NGROK URLS =====")

        for t in tunnels:
            proto = t["proto"]
            url = t["public_url"]
            print(f"{proto.upper()} URL: {url}")

        print("======================\n")

    except Exception as e:
        print("Could not get ngrok URL:", e)

if __name__ == "__main__":
    start_ngrok()
    app.run(host="0.0.0.0", port=5001)
