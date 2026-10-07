# server/app.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import os
from flask_cors import CORS
from dotenv import load_dotenv
from flask import Flask, send_from_directory, jsonify
from src.seismogram_pipeline.core.verify_network import verify_and_access_share

load_dotenv()

app = Flask(__name__)

# Enable CORS so Vue can deploy at http://localhost:5173 and fetch images from http://localhost:5000
CORS(app)

data_folder = verify_and_access_share()


@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint for Vue to check if the VPN/SMB mount is active."""
    mounted = os.path.exists(data_folder)
    return jsonify({
        "status": "online",
        "vpn_mounted": mounted,
        "mount_path": data_folder
    }), 200 if mounted else 503

@app.route('/thumbnails/<path:subpath>', methods=['GET'])
def serve_thumbnail(subpath):
    """
    Serves any thumbnail dynamically from:
    <data_folder>/thumbnails/<subpath>
    (e.g., Raw_Data/thumbnails/Box 2896 thumbnails/filename.jpg)
    """
    if not os.path.exists(data_folder):
        return jsonify({"error": "SMB share not mounted. Connect to VPN and mount drive."}), 503
    
    thumbnails_root = os.path.join(data_folder, 'thumbnails')
    return send_from_directory(thumbnails_root, subpath)

if __name__ == '__main__':
    # Runs locally on http://127.0.0.1:5000
    app.run(host='127.0.0.1', port=5000, debug=True)