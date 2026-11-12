# AuraDB Interactive Control Panel — Web & Server Architecture

A lightweight, local control panel stack built for managing and viewing seismogram data and thumbnails accessed via a secure VPN/SMB network share.

---

## Architecture Overview

```text
 ┌─────────────────┐        HTTP / CORS       ┌──────────────────┐
 │  Vue 3 + Vite   │ ◄──────────────────────► │   Flask Server   │
 │   (Frontend)    │   API & Thumbnails       │    (Python)      │
 └─────────────────┘                          └────────┬─────────┘
                                                       │
                                              VPN / SMB Network Share
                                              (Seismogram Data & Thumbnails)

```

The system is split into three main parts:

1. **Frontend (`vue`)**: Built with **Vue 3** and **Vite** for a fast, modern reactive interface.
2. **Backend (`server/app.py`)**: A **Flask** REST API that handles health checks (`/health`) and dynamic thumbnail serving (`/thumbnails/<path>`) directly from a network share.
3. **Documentation (`docs`)**: Automatically built Sphinx documentation served locally via Python.

---

## Directory & Script Reference

Managed primarily through Node scripts in `package.json`:

* **`npm run dev`**: Concurrently boots up the Flask backend and the documentation server.
* **`npm run dev:vue`**: Starts the Vite development server for the frontend.
* **`npm run dev:server`**: Runs the Python Flask server (`server/app.py`) on `[http://127.0.0.1:5000](http://127.0.0.1:5000)`.
* **`npm run dev:docs`**: Builds and hosts local Sphinx documentation on port `8000`.
* **`npm run build`**: Bundles the Vue frontend production assets using Vite.

---

## API Endpoints

* **`GET /health`**
* Checks if the required VPN and SMB network share is active and mounted.
* *Response (Online):* `200 OK` with status and mount path.
* *Response (Offline):* `503 Service Unavailable` if the network share is missing.

* **`GET /thumbnails/<path:subpath>`**
* Dynamically streams image assets directly from the mounted data folder's `thumbnails` directory.

---

## Getting Started

1. **Prerequisites:** Ensure you are connected to the required **VPN** and that the network share is mounted.
2. **Install Dependencies:**

```bash
# Frontend / Node dependencies
npm install

# Backend / Python dependencies (ensure virtual environment is active)
uv pip install flask flask-cors python-dotenv

```

3. **Run Development Mode:**

```bash
npm run build
npm run dev

```

4. **Modifications**

If modifications are made, it is best to clean and rebuild the components

```bash
cd web 
rm -rf node_modules/.vite 
cd ../docs && make clean && make html
cd ../web
npm run build && npm run dev
```

5. **Browser Cache**

If browser does not update with latest build after standard refresh, try CRTL+F5 (hard refresh)
