## YouTube to MP3 (Private Backend)

A minimal full‑stack app that converts a YouTube link to an MP3 using a self‑hosted backend powered by FastAPI and `yt-dlp`.

Important:
- Only download content that you own or have permission to use. Respect creators’ rights and the platform’s Terms of Service.
- Public YouTube‑to‑MP3 APIs are unstable; this project runs a private backend you can deploy yourself (Docker/Render/Heroku/VPS).

### Tech stack
- Backend: FastAPI (Python), `yt-dlp`, `ffmpeg`
- Frontend: Static HTML/JS

### Local development
1. System dependency: `ffmpeg` must be installed and available in `PATH`.
2. Create a virtual environment and install Python deps:
   ```bash
   cd /workspace
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r server/requirements.txt
   ```
3. Run the server:
   ```bash
   uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
   ```
4. Open the UI at `http://localhost:8000/`.

### Docker
Build and run locally:
```bash
docker build -t yt2mp3 .
docker run --rm -p 8000:8000 yt2mp3
```

### Deploying
- Render (one‑click): Create a Web Service from this repo. Use the Dockerfile (recommended) or a Python environment with a Start Command like `uvicorn server.main:app --host 0.0.0.0 --port $PORT`. Ensure `ffmpeg` is installed (Docker image already handles it).
- Railway/Heroku/VPS: Use the Dockerfile or install `ffmpeg` and run the same command.

#### GitHub Pages + private backend
This repo includes a GitHub Pages workflow that publishes the static UI in `web/`. GitHub Pages cannot run a Python backend, so you must deploy the backend separately and point the UI to it.

Steps:
1) Deploy the backend as a container using the provided Dockerfile (e.g., on Render/Railway/Fly/your VPS). It will serve both the API and UI if you keep `web/` in the image. Start command:
   ```bash
   uvicorn server.main:app --host 0.0.0.0 --port ${PORT:-8000}
   ```
2) Copy the backend URL (e.g., `https://your-backend.onrender.com`).
3) In your GitHub repository, add a Repository Secret named `BACKEND_URL` with that URL.
4) Push to `main`/`master`. The GitHub Pages workflow injects `window.API_BASE` into `web/config.js` so the static site calls your backend.

Notes:
- If `BACKEND_URL` is not set, the UI will try same-origin requests which will fail on Pages. Always set the secret.
- CORS is already enabled for all origins. Lock it down in `server/main.py` for production.

### API
- `GET /api/download?url=<youtube_url>` → returns an MP3 file download.
- `GET /health` → `{ "status": "ok" }`

### Notes
- Conversion uses `yt-dlp` with `FFmpegExtractAudio` to produce a 192kbps MP3.
- Temporary files are cleaned up after each request.

